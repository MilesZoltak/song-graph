import os
import json
from .playlist_fetch import get_playlist_tracks, sanitize_filename, get_spotify_client
from .lyrics_fetch import fetch_lyrics_for_tracks, get_genius_client
from .sentiment_analysis import add_sentiment_to_tracks, create_sentiment_classifier

def save_playlist_json(tracks, playlist_name, output_dir='playlists'):
    """
    Save playlist tracks to JSON file.
    
    Args:
        tracks: List of track dictionaries
        playlist_name: Name of the playlist
        output_dir: Directory to save JSON files (default 'playlists')
    
    Returns:
        Path to saved JSON file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Sanitize playlist name for filename
    safe_filename = sanitize_filename(playlist_name)
    output_file = os.path.join(output_dir, f'{safe_filename}.json')
    
    # Save to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tracks, f, indent=2, ensure_ascii=False)
    
    return output_file

async def process_playlist(playlist_url, spotify_client=None, genius_client=None, sentiment_classifier=None):
    """
    Process a Spotify playlist through the full pipeline:
    1. Fetch tracks and audio features from Spotify
    2. Fetch lyrics from Genius
    3. Analyze sentiment
    
    Args:
        playlist_url: Spotify playlist URL or ID
        spotify_client: Optional Spotify client (creates if not provided)
        genius_client: Optional Genius client (creates if not provided)
        sentiment_classifier: Optional sentiment classifier (creates if not provided)
    
    Returns:
        Dictionary with playlist_name, track_count, and tracks list
    """
    # Step 1: Fetch playlist tracks and audio features
    if spotify_client is None:
        spotify_client = get_spotify_client()
    
    tracks, playlist_name = get_playlist_tracks(playlist_url, spotify_client)
    
    # Step 2: Fetch lyrics
    if genius_client is None:
        genius_client = get_genius_client()
    
    tracks = fetch_lyrics_for_tracks(tracks, genius_client)
    
    # Step 3: Analyze sentiment
    if sentiment_classifier is None:
        sentiment_classifier = create_sentiment_classifier()
    
    tracks = add_sentiment_to_tracks(tracks, sentiment_classifier)
    
    # Step 4: Save to JSON
    output_file = save_playlist_json(tracks, playlist_name)
    
    return {
        'playlist_name': playlist_name,
        'track_count': len(tracks),
        'tracks': tracks,
        'output_file': output_file
    }

