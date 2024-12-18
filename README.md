# Command-Line Music Player

## Overview
This command-line music player is a Python program designed to manage a local music library and control playback of audio tracks.

## Features
- Add songs from YouTube by searching for them
- Select specific songs from the list
- Manage playback: play, pause, skip, and shuffle
- Set volume level
- View the list of available songs
- Batch add songs from a text file

## Dependencies
- pygame
- yt-dlp
- requests
- mutagen
- beautifulsoup4
- youtube_dl

## Installation
1. Clone the repository:

    ```bash
    git clone https://github.com/lyk64/cli-music-player.git
    ```

2. Navigate into the cloned repository directory:

    ```bash
    cd cli-music-player
    ```

3. Install dependencies:

    ```bash
    pip install -r dependencies.txt
    ```

## Usage
1. Run the program:

    ```bash
    python cli_music_player.py
    ```

2. Type `help` to see available commands.

3. Use commands like `search <query>` to add songs from YouTube, `list` to view available songs, and `select <index>` to select a song to play.


## Contributors
- Creator: [lyk64](https://github.com/lyk64)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
