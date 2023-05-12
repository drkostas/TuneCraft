# TuneCraft: Spotify Playlist Generator

[![GitHub license](https://img.shields.io/badge/license-Apache-blue.svg)](
https://github.com/yourusername/TuneCraft/blob/master/LICENSE)

## Table of Contents

+ [About](#about)
+ [Getting Started](#getting_started)
  + [Prerequisites](#prerequisites)
+ [Installing the requirements](#installing)
  + [Using the Makefile](#installing_makefile)
+ [Running the code](#run_locally)
  + [Execution Options](#execution_options)
    + [main.py](#src_main)
+ [Todo](#todo)
+ [License](#license)

## About <a name = "about"></a>

TuneCraft is a Spotify playlist generator that creates new playlists based on your existing playlists, musical taste, and specified criteria. It is designed to help you explore new music while maintaining a familiar sound.

The main code is located in the [main.py](main.py) file. Functions for interacting with the Spotify API and generating playlists can be found in the same file.

## Getting Started <a name = "getting_started"></a>

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites <a name = "prerequisites"></a>

You need to have a machine with Python >= 3.6 and any Bash-based shell (e.g. zsh) installed.

```ShellSession
$ python3.10 -V
Python 3.10

$ echo $SHELL
/usr/bin/zsh
```

## Installing the requirements <a name = "installing"></a>

### Using the Makefile <a name = "installing_makefile"></a>
All the installation steps are being handled by the [Makefile](Makefile).

Then, to create a conda environment, install the requirements, setup the library and run the tests
execute the following commands:

```ShellSession
$ make create_env
$ conda activate tunecraft
$ make requirements
```

## Running the code <a name = "run_locally"></a>

### Execution Options <a name = "execution_options"></a>

First, make sure you are in the correct virtual environment:

```ShellSession
$ conda activate tune_craft

$ which python
/home/<user>/anaconda3/envs/src/bin/python
```

#### main.py <a name = "src_main"></a>

Now, in order to run the code you can call the [main.py](main.py)
directly.

```ShellSession
$ python main.py -h
usage: main.py -u USER_ID [-s SEED_PLAYLIST] [-nt NUMBER_TRACKS] [--new-artists] [--refresh] [--list-playlists] [-h]

TuneCraft - Spotify Playlist Generator

Required Arguments:
  -u USER_ID, --user-id USER_ID
                        Your Spotify user ID

Optional Arguments:
  -s SEED_PLAYLIST, --seed-playlist SEED_PLAYLIST
                        The seed playlist ID to generate a new playlist from
  -nt NUMBER_TRACKS, --number-tracks NUMBER_TRACKS
                        Number of tracks in the generated playlist
  --new-artists         Include only new artists
  --refresh             Refresh the local database from Spotify
  --list-playlists      List all your playlists
  -h, --help            Show this help message and exit
```

Usage Examples <a name = "usage_examples"></a>

Generate a new playlist based on a seed playlist ID with 20 tracks:

$ python main.py -u your_user_id -s your_seed_playlist_id -nt 20


Generate a new playlist with only new artists:

$ python main.py -u your_user_id -s your_seed_playlist_id --new-artists


List all your playlists:

$ python main.py -u your_user_id --list-playlists


Refresh the local database and list all your playlists:

$ python main.py -u your_user_id --refresh --list-playlists

Todo <a name = "todo"></a>
Add support for generating playlists based on moods and genres.
Implement a web interface for easier user interaction.
Improve the playlist generation algorithm for better recommendations.
License <a name = "license"></a>

This project is licensed under the Apache License - see the LICENSE file for details.