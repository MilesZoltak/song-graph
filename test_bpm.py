"""
Test script to extract BPM from all tracks in a Spotify playlist using librosa.
"""
import os
import tempfile
import librosa
import numpy as np
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from spotify_preview_finder import search_and_get_links
import pandas as pd

# Load environment variables
load_dotenv()

# Configuration
PLAYLIST_URL = "https://open.spotify.com/playlist/6ENxgIEdvQK45A3sLIq6t0"

def download_preview(preview_url):
    """Download preview audio to temporary file."""
    if not preview_url:
        return None
    
    try:
        response = requests.get(preview_url, timeout=10)
        response.raise_for_status()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.write(response.content)
        temp_file.close()
        
        return temp_file.name
    except Exception:
        return None


def get_preview_url_for_track(title, artist, api_preview_url):
    """Try to get preview URL from API or spotify-preview-finder."""
    if api_preview_url:
        return api_preview_url, 'api'
    
    try:
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        query = f"{title} {artist}"
        result = search_and_get_links(query, client_id, client_secret, limit=1)
        
        if result and result.get('success') and result.get('results'):
            return result['results'][0]['previewUrl'], 'finder'
    except Exception:
        pass
    
    return None, None

def calculate_bpm_for_track(preview_url):
    """Download and calculate BPM for a preview URL."""
    try:
        audio_file = download_preview(preview_url)
        if not audio_file:
            return None
        
        # Load and analyze
        y, sr = librosa.load(audio_file, duration=30)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        if isinstance(tempo, np.ndarray):
            bpm = float(tempo[0]) if len(tempo) > 0 else float(tempo)
        else:
            bpm = float(tempo)
        
        # Cleanup
        os.remove(audio_file)
        
        return bpm
    except Exception:
        return None

def main():
    print("=" * 80)
    print("BPM Extraction Test - Full Playlist")
    print("=" * 80)
    
    # Initialize Spotify client
    print("\n1. Initializing Spotify client...")
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:3000/callback'),
        scope='playlist-read-private playlist-read-collaborative',
        cache_path='.spotify_cache',
        open_browser=True
    ))
    print("   ✓ Spotify client initialized")
    
    # Extract playlist ID
    playlist_id = PLAYLIST_URL.split('playlist/')[-1].split('?')[0]
    
    # Get playlist info
    print(f"\n2. Fetching playlist...")
    playlist_info = sp.playlist(playlist_id)
    playlist_name = playlist_info['name']
    total_tracks = playlist_info['tracks']['total']
    print(f"   ✓ Playlist: {playlist_name}")
    print(f"   Total tracks: {total_tracks}")
    
    # Get all tracks
    print(f"\n3. Fetching all tracks...")
    all_tracks = []
    results = sp.playlist_tracks(playlist_id)
    all_tracks.extend(results['items'])
    
    # Handle pagination
    while results['next']:
        results = sp.next(results)
        all_tracks.extend(results['items'])
    
    print(f"   ✓ Fetched {len(all_tracks)} tracks")
    
    # Process each track
    print(f"\n4. Processing tracks...")
    data = []
    
    for i, item in enumerate(all_tracks, 1):
        if not item['track']:
            continue
        
        track = item['track']
        title = track['name']
        artist = track['artists'][0]['name'] if track['artists'] else 'Unknown'
        api_preview = track.get('preview_url')
        
        print(f"   [{i}/{len(all_tracks)}] {title} - {artist}")
        
        # Try to get preview URL
        preview_url, source = get_preview_url_for_track(title, artist, api_preview)
        
        if not preview_url:
            print(f"        ✗ No preview URL available")
            data.append({
                '#': i,
                'Song': title,
                'Artist': artist,
                'BPM': 'No Preview'
            })
            continue
        
        print(f"        ✓ Preview URL ({source})")
        
        # Calculate BPM
        bpm = calculate_bpm_for_track(preview_url)
        
        if bpm:
            print(f"        ✓ BPM: {bpm:.1f}")
            data.append({
                '#': i,
                'Song': title,
                'Artist': artist,
                'BPM': f"{bpm:.1f}"
            })
        else:
            print(f"        ✗ BPM calculation failed")
            data.append({
                '#': i,
                'Song': title,
                'Artist': artist,
                'BPM': 'Failed'
            })
    
    # Display results as dataframe
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    df = pd.DataFrame(data)
    print(df.to_string(index=False))
    
    # Summary statistics
    numeric_bpms = [float(row['BPM']) for row in data if row['BPM'] not in ['No Preview', 'Failed']]
    if numeric_bpms:
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total tracks: {len(data)}")
        print(f"Successful BPM extractions: {len(numeric_bpms)}")
        print(f"Average BPM: {sum(numeric_bpms) / len(numeric_bpms):.1f}")
        print(f"Min BPM: {min(numeric_bpms):.1f}")
        print(f"Max BPM: {max(numeric_bpms):.1f}")
        print("=" * 80)

if __name__ == "__main__":
    main()

