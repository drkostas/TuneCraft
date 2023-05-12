import argparse
import os
import sqlite3
from typing import List, Tuple
from os.path import join, dirname
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

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
    optional_args.add_argument('--refresh', action='store_true', help="Refresh playlists from Spotify")
    optional_args.add_argument('--list-playlists', action='store_true', help="List your Spotify playlists")
    optional_args.add_argument('-s', '--seed-playlist', help="The seed playlist ID to generate a new playlist from")
    optional_args.add_argument('-nt', '--number-tracks', type=int, default=20, help="Number of tracks in the generated playlist")
    optional_args.add_argument('--new-artists', action='store_true', help="Include only new artists in the generated playlist")
    optional_args.add_argument("-h", "--help", action="help", help="Show this help message and exit")

    return parser.parse_args()

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

def get_playlist_tracks_from_db(playlist_id: str) -> List[str]:
    with sqlite3.connect("playlists.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT track_id FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
        return [row[0] for row in cursor.fetchall()]

def save_playlists_to_db(playlists: List[dict], user_id: str):
    with sqlite3.connect("playlists.db") as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS playlists (id TEXT PRIMARY KEY, name TEXT, user_id TEXT)")
        cursor.executemany("REPLACE INTO playlists (id, name, user_id) VALUES (?, ?, ?)",
                           [(pl["id"], pl["name"], user_id) for pl in playlists])

        cursor.execute("CREATE TABLE IF NOT EXISTS playlist_tracks (playlist_id TEXT, track_id TEXT, PRIMARY KEY(playlist_id, track_id))")
        for pl in playlists:
            tracks = get_playlist_tracks(pl["id"])
            cursor.executemany("REPLACE INTO playlist_tracks (playlist_id, track_id) VALUES (?, ?)",
                               [(pl["id"], track_id) for track_id in tracks])

        conn.commit()

def get_playlists_from_db(user_id: str) -> List[Tuple[str, str]]:
    with sqlite3.connect("playlists.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM playlists WHERE user_id = ?", (user_id,))
        return cursor.fetchall()

def refresh_playlists(user_id: str):
    playlists = get_user_playlists(user_id)
    save_playlists_to_db(playlists, user_id)

def list_playlists(user_id: str, refresh: bool =False):
    if refresh:
        refresh_playlists(user_id)
    playlists = get_playlists_from_db(user_id)
    for pl in playlists:
        print(f"{pl[0]}: {pl[1]}")

def generate_playlist(user_id: str, seed_playlist: str, number_tracks: int, new_artists: bool):
    if seed_playlist not in [pl[0] for pl in get_playlists_from_db(user_id)]:
        print("Invalid seed playlist ID.")
        return

    seed_playlist_tracks = get_playlist_tracks_from_db(seed_playlist)
    seed_artists = set([sp.track(track)["artists"][0]["id"] for track in seed_playlist_tracks]) if new_artists else set()

    existing_tracks = set()
    for pl in get_playlists_from_db(user_id):
        existing_tracks.update(get_playlist_tracks(pl[0]))

    new_tracks = []
    while len(new_tracks) < number_tracks:
        recommendations = sp.recommendations(seed_tracks=seed_playlist_tracks, limit=number_tracks * 2)
        recommended_tracks = [track for track in recommendations["tracks"] if track["artists"][0]["id"] not in seed_artists and track["id"] not in existing_tracks]
        
        for track in recommended_tracks:
            if len(new_tracks) < number_tracks:
                new_tracks.append(track)
            else:
                break

    seed_playlist_name = sp.playlist(seed_playlist)["name"]
    playlist_name = f"TuneCraft_{seed_playlist_name}"
    new_playlist = sp.user_playlist_create(user_id, playlist_name)
    sp.playlist_add_items(new_playlist["id"], [track["id"] for track in new_tracks])




def main():
    args = get_args()
    print("Welcome to Spotify Playlist Generator!")
    user_id = SPOTIFY_USERNAME
    if not args.seed_playlist and not args.list_playlists and not args.refresh:
        print("Please provide an argument. Use -h or --help for more information.")
        return

    if args.refresh:
        print("Refreshing playlists from Spotify and saving them locally...")
        refresh_playlists(user_id)

    if args.list_playlists:
        print("Your playlists:")
        list_playlists(user_id)

    if args.seed_playlist:
        print(f"Generating a new playlist based on {args.seed_playlist}...")
        generate_playlist(user_id, args.seed_playlist, args.number_tracks, args.new_artists)

if __name__ == "__main__":
    main()