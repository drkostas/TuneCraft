import argparse
import os
import sqlite3
from typing import List, Tuple, Union
from os.path import join, dirname
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import random

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SPOTIFY_USERNAME = os.getenv("SPOTIFY_USERNAME")
SCOPE = "playlist-modify-public user-library-read"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=SCOPE))


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Spotify playlist generator', add_help=False)

    optional_args = parser.add_argument_group('Optional Arguments')
    optional_args.add_argument('--refresh', action='store_true',
                               help="Refresh playlists from Spotify")
    optional_args.add_argument('--list-playlists', action='store_true',
                               help="List your Spotify playlists")
    optional_args.add_argument('-s', '--seed-playlist',
                               help="The seed playlist ID to generate a new playlist from")
    optional_args.add_argument('-nt', '--number-tracks', type=int, default=20,
                               help="Number of tracks in the generated playlist")
    optional_args.add_argument('--new-artists', action='store_true',
                               help="Include only new artists in the generated playlist")
    optional_args.add_argument('--use_all', action='store_true', 
                               help="Use all tracks in the seed playlist as seeds")
    optional_args.add_argument("-h", "--help", action="help", help="Show this help message and exit")

    return parser.parse_args()


def create_tables_if_not_exists(table: Union[str, None] = None):
    with sqlite3.connect("playlists.db") as conn:
        cursor = conn.cursor()
        if table == 'playlists' or table is None:
            cursor.execute("CREATE TABLE IF NOT EXISTS playlists (id TEXT PRIMARY KEY, name TEXT, user_id TEXT)")
        if table == 'playlist_tracks' or table is None:
            cursor.execute("CREATE TABLE IF NOT EXISTS playlist_tracks "
                           "(playlist_id TEXT, track_id TEXT, PRIMARY KEY(playlist_id, track_id))")
        if table == 'liked_tracks' or table is None:
            cursor.execute("CREATE TABLE IF NOT EXISTS liked_tracks "
                           "(user_id TEXT, track_id TEXT, PRIMARY KEY(user_id, track_id))")
        conn.commit()


def get_user_playlists(user_id: str) -> List[dict]:
    playlists = []
    offset = 0
    while True:
        results = sp.user_playlists(user_id, offset=offset)
        if not results["items"]:
            break
        playlists.extend(results["items"])
        offset += len(results["items"])
    return playlists


def get_playlist_tracks(playlist_id: str) -> List[str]:
    tracks = []
    offset = 0
    while True:
        results = sp.playlist_tracks(playlist_id, offset=offset)
        if not results["items"]:
            break
        tracks.extend([item["track"]["id"] for item in results["items"]])
        offset += len(results["items"])
    return tracks


def get_and_save_liked_tracks(user_id: str):
    liked_tracks = set()
    offset = 0
    while True:
        results = sp.current_user_saved_tracks(limit=50, offset=offset)
        if not results["items"]:
            break
        liked_tracks.update([item["track"]["id"] for item in results["items"]])
        offset += len(results["items"])

    with sqlite3.connect("playlists.db") as conn:
        cursor = conn.cursor()
        create_tables_if_not_exists(table='liked_tracks')
        cursor.executemany("REPLACE INTO liked_tracks (user_id, track_id) VALUES (?, ?)",
                           [(user_id, track_id) for track_id in liked_tracks])
        conn.commit()


def get_playlist_tracks_from_db(playlist_id: str) -> List[str]:
    with sqlite3.connect("playlists.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT track_id FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
        return [row[0] for row in cursor.fetchall()]


def display_playlist_tracks(playlist_id: str, user_id: str) -> None:
    tracks = get_playlist_tracks(playlist_id)
    with sqlite3.connect("playlists.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT track_id FROM liked_tracks WHERE user_id = ?", (user_id,))
        liked_track_ids = set([row[0] for row in cursor.fetchall()])

    for idx, track_id in enumerate(tracks):
        track = sp.track(track_id)
        heart_symbol = "<3" if track_id in liked_track_ids else ""
        print(f"{idx + 1}. {track['name']} - {track['artists'][0]['name']} {heart_symbol}")


def save_playlists_to_db(playlists: List[dict], user_id: str):
    with sqlite3.connect("playlists.db") as conn:
        cursor = conn.cursor()
        create_tables_if_not_exists(table='plalylists')
        cursor.executemany("REPLACE INTO playlists (id, name, user_id) VALUES (?, ?, ?)",
                           [(pl["id"], pl["name"], user_id) for pl in playlists])

        create_tables_if_not_exists(table='playlist_tracks')
        for pl in playlists:
            tracks = get_playlist_tracks(pl["id"])
            cursor.executemany("REPLACE INTO playlist_tracks (playlist_id, track_id) VALUES (?, ?)",
                               [(pl["id"], track_id) for track_id in tracks])

        conn.commit()


def check_and_clear_database():
    with sqlite3.connect("playlists.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = cursor.fetchall()
        if existing_tables:
            clear = input("Tables already exist. Do you want to clear the database? (y/n): ")
            if clear.lower() == 'y':
                cursor.execute("DROP TABLE IF EXISTS playlists")
                cursor.execute("DROP TABLE IF EXISTS playlist_tracks")
                cursor.execute("DROP TABLE IF EXISTS liked_tracks")
            else:
                print("Continuing with existing tables.")
                return
        create_tables_if_not_exists()
        conn.commit()


def get_playlists_from_db(user_id: str) -> List[Tuple[str, str]]:
    with sqlite3.connect("playlists.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM playlists WHERE user_id = ?", (user_id,))
        return cursor.fetchall()


def refresh_playlists(user_id: str):
    create_tables_if_not_exists()
    with sqlite3.connect("playlists.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM playlists WHERE user_id = ?", (user_id,))
        existing_playlists = set([row[0] for row in cursor.fetchall()])
        current_playlists = set([pl["id"] for pl in sp.current_user_playlists()["items"]])

        # Delete playlists not in Spotify anymore
        for pl in existing_playlists - current_playlists:
            cursor.execute("DELETE FROM playlists WHERE id = ?", (pl,))

        # Update tracks in each playlist
        for pl in current_playlists:
            tracks = get_playlist_tracks(pl)
            cursor.execute("SELECT track_id FROM playlist_tracks WHERE playlist_id = ?", (pl,))
            existing_tracks = set([row[0] for row in cursor.fetchall()])
            current_tracks = set(tracks)

            # Delete tracks not in the playlist anymore
            for track in existing_tracks - current_tracks:
                cursor.execute("DELETE FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?", (pl, track))

            # Insert new tracks
            for track in current_tracks - existing_tracks:
                cursor.execute("INSERT INTO playlist_tracks (playlist_id, track_id) VALUES (?, ?)", (pl, track))

        conn.commit()


def list_playlists(user_id: str, refresh: bool = False):
    if refresh:
        refresh_playlists(user_id)
    playlists = get_playlists_from_db(user_id)
    for pl in playlists:
        print(f"{pl[0]}: {pl[1]}")


def generate_playlist(user_id: str, seed_playlist: str, number_tracks: int, new_artists: bool, use_all: bool):
    seed_playlist_name = sp.playlist(seed_playlist)["name"]
    print(f"Using {seed_playlist_name} as seed playlist.")

    if seed_playlist not in [pl[0] for pl in get_playlists_from_db(user_id)]:
        print("Invalid seed playlist ID.")
        return

    seed_playlist_tracks = get_playlist_tracks(seed_playlist)

    if use_all:
        selected_indices = list(range(len(seed_playlist_tracks)))
    else:
        print("Here are the tracks in the seed playlist:")
        display_playlist_tracks(seed_playlist, user_id)
        input_str = input("Enter space-separated track numbers to use as seeds (leave blank for random selection): ")
        if input_str.strip() == "":
            selected_indices = []
        else:
            try:
                selected_indices = [int(x) - 1 for x in input_str.split()]
                if not all(0 <= idx < len(seed_playlist_tracks) for idx in selected_indices):
                    print("Invalid input. Using random tracks.")
                    selected_indices = []
            except ValueError:
                print("Invalid input. Using random tracks.")
                selected_indices = []

    if not selected_indices:
        selected_indices = random.sample(range(len(seed_playlist_tracks)), min(5, len(seed_playlist_tracks)))

    seed_tracks = [seed_playlist_tracks[idx] for idx in selected_indices]
    seed_artists = set([sp.track(track)["artists"][0]["id"] for track in seed_tracks]) if new_artists else set()

    # Check existing tracks including liked songs
    existing_tracks = set()
    for pl in get_playlists_from_db(user_id):
        existing_tracks.update(get_playlist_tracks(pl[0]))
    with sqlite3.connect("playlists.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT track_id FROM liked_tracks WHERE user_id = ?", (user_id,))
        liked_track_ids = set([row[0] for row in cursor.fetchall()])
    existing_tracks.update(liked_track_ids)

    new_tracks = []
    chunk_size = 5
    seed_playlist_tracks_chunks = [seed_playlist_tracks[i:i + chunk_size] for i in range(0, len(seed_playlist_tracks), chunk_size)]

    print("Retrieving recommendations...", end="")
    for seed_tracks in seed_playlist_tracks_chunks:
        seed_artists = set([sp.track(track)["artists"][0]["id"] for track in seed_tracks]) if new_artists else set()

        while len(new_tracks) < number_tracks:
            print(".", end="", flush=True)
            recommendations = sp.recommendations(seed_tracks=seed_tracks, limit=min(number_tracks * 2, 100))
            recommended_tracks = [track for track in recommendations["tracks"]
                                    if track["artists"][0]["id"] not in seed_artists and track["id"] not in existing_tracks]

            for track in recommended_tracks:
                if len(new_tracks) < number_tracks:
                    new_tracks.append(track)
                else:
                    break
    print(" Done!")

    num_tracks_used = len(selected_indices) if not use_all else len(seed_playlist_tracks)
    playlist_name = f"[TuneCraft] {seed_playlist_name}"
    description = f"This playlist was generated by https://github.com/drkostas/TuneCraft. Flags used: source-playlist: {seed_playlist_name}, number-tracks-used: {num_tracks_used}, only-new-artists: {'true' if new_artists else 'false'}, number-tracks: {number_tracks}"
    new_playlist = sp.user_playlist_create(user_id, playlist_name, description=description)
    sp.playlist_add_items(new_playlist["id"], [track["id"] for track in new_tracks])


def main():
    args = get_args()
    print("Welcome to Spotify Playlist Generator!")
    user_id = SPOTIFY_USERNAME
    if not args.seed_playlist and not args.list_playlists and not args.refresh:
        print("Please provide an argument. Use -h or --help for more information.")
        return

    if args.refresh:
        check_and_clear_database()
        print("Refreshing playlists from Spotify and saving them locally...")
        refresh_playlists(user_id)
        print("Retrieving liked tracks from Spotify and saving them locally...")
        get_and_save_liked_tracks(user_id)
        playlists = get_user_playlists(user_id)
        save_playlists_to_db(playlists, user_id)

    if args.list_playlists:
        print("Your playlists:")
        list_playlists(user_id, args.refresh)

    if args.seed_playlist:
        print("Generating a new playlist...")
        generate_playlist(user_id, args.seed_playlist, args.number_tracks, args.new_artists, args.use_all)

    print("Program finished.")


if __name__ == "__main__":
    main()
