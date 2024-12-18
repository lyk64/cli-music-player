"""
Author: lyk64
Date: 2024-05-05
Version: 1.0

This program is a command-line music player that allows users to manage a local music library and control playback.

Classes:
1. MusicPlayer
    - Manages the playback of music tracks
    - Provides functionality for adding a batch of songs from a text file

2. MusicDownloader
    - Downloads songs from Youtube based on user queries
    - Utilizes BeautifulSoup for parsing YouTube search results to extract video URLs

3. CLI:
    - Provides a command-line interface for users to interact with the music player

Dependencies:
    - os: File and directory operations.
    - re: Regular expressions for text manipulation.
    - sys: Interpreter-related functions and variables.
    - pygame: Audio playback.
    - shutil: High-level file operations.
    - yt_dlp: YouTube video downloading.
    - random: Random number generation and selection.
    - requests: HTTP requests for downloading.
    - threading: Concurrent task execution.
    - mutagen.mp3: MP3 audio metadata handling.
    - concurrent.futures: Asynchronous task execution and thread management.
    - BeautifulSoup: HTML parsing.
    - sanitize_filename: Filename sanitization for Youtube downloads.
"""

import os
import re
import sys
import pygame
import shutil
import yt_dlp
import random
import requests
import threading
import mutagen.mp3
import concurrent.futures
from bs4 import BeautifulSoup
from youtube_dl.utils import sanitize_filename

pygame.init()

class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.is_playing = False
        self.is_shuffling = False
        self.current_song_index = 0
        self.songs = []
        self.songs_folder = "songs"
        self.temp_folder = "temp"
        os.makedirs(self.songs_folder, exist_ok=True)
        os.makedirs(self.temp_folder, exist_ok=True)
        pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)

    def batch_add_songs(self, file_path):
        downloader = MusicDownloader()
        try:
            with open(file_path, "r") as file:
                content = file.read()
                songs = re.findall(r'\[(.*?)\]', content)
                if songs:
                    semaphore = threading.Semaphore(10)
                    threads = []
                    songs_list = songs[0].split(', ')
                    songs_list = list(set(songs_list))
                    for song in songs_list:
                        i = songs_list.index(song) + 1
                        print(f"\033[34mCreating download thread #{i}\033[0m")
                        thread = threading.Thread(target=lambda: self.save_with_semaphore(downloader, semaphore, song))
                        threads.append(thread)
                        thread.start()
                    for thread in threads:
                        thread.join()
                    for song in os.listdir(self.temp_folder):
                        downloader.fix()

                else:
                    print("\033[91mNo songs found in the text file.\033[0m")
        except FileNotFoundError:
            print("\033[91mFile not found.\033[0m")

    def set_volume(self, volume_level):
        if 0 <= volume_level <= 100:
            pygame.mixer.music.set_volume(volume_level / 100)
            print(f"\033[34mVolume set to {volume_level}\033[0m")
        else:
            print("\033[91mVolume level must be between 0 and 100.\033[0m")

    def save_with_semaphore(self, downloader, semaphore, song):
        with semaphore:
            downloader.save_batch(song)

    def pause(self):
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
        else:
            print("\033[91mError: No song is currently playing.\033[0m")

    def play(self):
        if not self.is_playing:
            pygame.mixer.music.unpause()
            self.is_playing = True
        else:
            print("\033[91mError: Song is currently playing.\033[0m")

    def play_specific_song(self, index):
        self.refresh_list()
        if not self.songs:
            print("\033[91mError: No songs available.\033[0m")
            return

        if 0 <= index < len(self.songs):
            self.current_song_index = index
            self.play_selected_song()
        else:
            print("\033[91mError: Invalid song index.\033[0m")

    def toggle_shuffle(self):
        self.is_shuffling = not self.is_shuffling
        if self.is_shuffling:
            random.shuffle(self.songs)
            print(f"\033[34mShuffle turned on.\033[0m")
        else:
            self.refresh_list()
            print(f"\033[34mShuffle turned off.\033[0m")

    def play_song(self, direction):
        if self.songs:
            if self.is_shuffling:
                self.current_song_index = random.randint(0, len(self.songs) - 1)
            else:
                if direction == "next":
                    self.current_song_index = (self.current_song_index + 1) % len(self.songs)
                elif direction == "previous":
                    self.current_song_index = (self.current_song_index - 1) % len(self.songs)
                else:
                    print("\033[91mInvalid direction.\033[0m")
                    return
            self.play_selected_song()
        else:
            print("\033[91mNo songs available.\033[0m")

    def play_selected_song(self):
        if self.songs:
            selected_song = self.songs[self.current_song_index]
            song_path = os.path.join(self.songs_folder, f"{selected_song}.mp3")
            try:
                pygame.mixer.music.load(song_path)
                pygame.mixer.music.play()
                self.is_playing = True
            except pygame.error as e:
                print("\033[91mError loading or playing the song:", e, "\033[0m")
        else:
            print("\033[91mError: No songs available to play.\033[0m")

    def get_song_list(self):
        songs = [file[:-4] for file in os.listdir(self.songs_folder) if file.endswith('.mp3')]
        return songs
        
    def refresh_list(self):
        self.songs = self.get_song_list()

    def handle_events(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.USEREVENT + 1:
                    self.play_song("next")
            pygame.time.delay(100)

class MusicDownloader:
    def __init__(self):
        self.temp_folder = "temp"
        self.songs_folder = "songs"

    def download(self, url):        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'outtmpl': os.path.join(self.temp_folder, sanitize_filename('"%(title)s".%(ext)s')),
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download = False)
                title = info.get('title', 'Unknown Title')
                sys.stdout.flush()
                ydl.download([url])
                return True
            except Exception as e:
                print("\033[91mError:", e, "\033[0m")
                return False

    def get_url(self, query):
        query = query.replace(' ', '+')
        url = f"https://www.youtube.com/results?search_query={query}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        for script in soup.find_all('script'):
            if 'videoId' in script.text:
                videoId = re.search(r'"videoId":"([^"]+)"', script.text).group(1)
                found_url = f"https://www.youtube.com/watch?v={videoId}"
                return found_url

    def fix(self):
        downloaded_file = os.listdir(self.temp_folder)[0]
        pattern = re.compile(r'[^a-zA-Z0-9]')
        new_title = pattern.sub('', downloaded_file[:-4])
        new_title = new_title.replace(" ", "")
        old_file_name = os.path.join(self.temp_folder, downloaded_file)
        new_file_name = os.path.join(self.temp_folder, f"{new_title}.mp3")
        os.rename(old_file_name, new_file_name)
        shutil.move(new_file_name, os.path.join(self.songs_folder, f"{new_title}.mp3"))
        music_player = MusicPlayer()
        music_player.refresh_list()
        index = len(music_player.songs)
        print(f"\033[34mDownloaded {index} : \033[93m{new_title}\033[0m")

    def save(self, query):
        url = self.get_url(query)
        self.download(url)
        self.fix()

    def save_batch(self, query):
        url = self.get_url(query)
        self.download(url)

class CLI:
    def __init__(self, music_player):
        self.music_player = music_player

    def handle_events(self):
        self.music_player.handle_events()

    def start(self):
        print(f"\033[34mType 'help' for available commands.\033[0m")

        event_thread = threading.Thread(target=self.music_player.handle_events)
        event_thread.start()

        while True:
            command = input("\033[34mEnter a command: \033[0m").strip().lower()
            if command == "help":
                self.print_help()
            elif command.startswith("search "):
                query = command[7:].strip()
                MusicDownloader().save(query)
            else:
                self.handle_command(command)

    def handle_command(self, command):
        command_map = {
            "pause": self.music_player.pause,
            "play": self.music_player.play,
            "next": lambda: self.music_player.play_song("next"),
            "previous": lambda: self.music_player.play_song("previous"),
            "list": self.list_songs,
            "shuffle": self.toggle_shuffle,
            "current": self.current_song,
        }
        if command.startswith("select "):
            try:
                index = int(command.split()[1]) - 1
                self.music_player.play_specific_song(index)
            except (IndexError, ValueError):
                print("\033[91mInvalid command.\033[0m")
        elif command.startswith("volume "):
            try:
                volume_level = int(command.split()[1])
                self.music_player.set_volume(volume_level)
            except (IndexError, ValueError):
                print("\033[91mInvalid command.\033[0m")
        elif command.startswith("batch "):
            try:
                self.music_player.batch_add_songs(command.split()[1])
            except TypeError:
                print("\033[91mInvalid command. File path must be a string.\033[0m")
            except (FileNotFoundError, Exception) as e:
                print("\033[91mError:", e, "\033[0m")
        else:
            commandFunction = command_map.get(command, self.invalid_command)
            commandFunction()        

    def list_songs(self):
        songs = self.music_player.get_song_list()
        print(f"\033[34mAvailable songs:\033[0m")
        for i, song in enumerate(songs, 1):
            song_path = os.path.join(self.music_player.songs_folder, f"{song}.mp3")
            try:
                audio = mutagen.mp3.MP3(song_path)
                duration = audio.info.length
                hours = int(duration / 3600)
                minutes = int((duration % 3600) / 60)
                seconds = int(duration % 60)
                hours_str = f"{hours:02d}"
                minutes_str = f"{minutes:02d}"
                seconds_str = f"{seconds:02d}"
                print(f"\033[34m{i} :\033[0m \033[93m{song}\033[34m - {hours_str}:{minutes_str}:{seconds_str}\033[0m")
            except Exception as e:
                print("\033[91mError getting duration for", song + ":", e, "\033[0m")

    def current_song(self):
        if self.music_player.songs:
            song_index = self.music_player.current_song_index + 1
            song = self.music_player.songs[self.music_player.current_song_index]
            print(f"\033[34mNow Playing {song_index} : \033[93m{song}\033[0m")
        else:
            print(f"\033[34mNo song is currently playing.\033[0m")

    def toggle_shuffle(self):
        self.music_player.toggle_shuffle()

    def print_help(self):
        print(f"\033[34mAvailable commands:")
        print(f"  \033[32mhelp:\033[0m Return a list of available commands")
        print(f"  \033[32msearch <query>:\033[0m Search and download a song")
        print(f"  \033[32mselect <index>:\033[0m Select a song from the list")
        print(f"  \033[32mlist:\033[0m List all available songs")
        print(f"  \033[32mshuffle:\033[0m Toggle shuffle mode")
        print(f"  \033[32mplay:\033[0m Resume playing the paused song")
        print(f"  \033[32mpause:\033[0m Pause the currently playing song")
        print(f"  \033[32mnext:\033[0m Play the next song in the playlist")
        print(f"  \033[32mprevious:\033[0m Play the previous song in the playlist")
        print(f"  \033[32mcurrent:\033[0m Return the name of the current song")
        print(f"  \033[32mvolume <level>:\033[0m Set volume level (0 to 100)")
        print(f"  \033[32mbatch <path>:\033[0m Add songs from a text file")

    def invalid_command(self):
        print("\033[91mInvalid command. Type 'help' for available commands.\033[0m")

music_player = MusicPlayer()
cli = CLI(music_player)
cli.start()
