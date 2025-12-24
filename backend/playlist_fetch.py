import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import os
import re
from dotenv import load_dotenv
from .audio_features import add_audio_features_to_tracks

# Load environment variables from .env file
load_dotenv()

def sanitize_filename(name):
    """Convert playlist name to a safe filename."""
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Remove or replace special characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Remove leading/trailing dots and spaces
    name = name.strip('. ')
    return name

def get_spotify_client(redirect_uri=None, open_browser=False):
    """
    Create and return a Spotify client with OAuth authentication.
    
    Args:
        redirect_uri: Optional redirect URI (defaults to env var or default)
        open_browser: Whether to open browser for auth (default False for API use)
    
    Returns:
        spotipy.Spotify client instance
    """
    redirect_uri = redirect_uri or os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:3000/callback')
    
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=redirect_uri,
        scope='playlist-read-private playlist-read-collaborative',
        cache_path='.spotify_cache',
        open_browser=open_browser
    ))
    return sp

def extract_playlist_id(playlist_url):
    """Extract playlist ID from URL or return as-is if already an ID."""
    if 'spotify.com' in playlist_url:
        return playlist_url.split('playlist/')[-1].split('?')[0]
    return playlist_url

def get_album_art_url(album_data):
    """
    Extract album art URL from Spotify album data.
    Returns the medium-sized image URL, or largest available.
    
    Args:
        album_data: Album object from Spotify API
    
    Returns:
        Album art URL string or None
    """
    images = album_data.get('images', [])
    if not images:
        return None
    
    # Prefer medium (300x300), fallback to largest
    for size in ['medium', 'large', 'small']:
        for img in images:
            if img.get('height') == 300 or (size == 'large' and img.get('height', 0) > 300):
                return img.get('url')
    
    # Return first available image
    return images[0].get('url') if images else None

def get_playlist_metadata(playlist_url, spotify_client=None):
    """
    Get playlist metadata (name, images, owner, description, etc.) without fetching tracks.
    
    Args:
        playlist_url: Spotify playlist URL or URI
        spotify_client: Optional Spotify client (creates new one if not provided)
    
    Returns:
        Dictionary with playlist metadata
    """
    if spotify_client is None:
        spotify_client = get_spotify_client()
    
    # Extract playlist ID from URL
    playlist_id = extract_playlist_id(playlist_url)
    
    # Get playlist info
    playlist_info = spotify_client.playlist(playlist_id)
    
    # Extract relevant metadata
    images = playlist_info.get('images', [])
    thumbnail_url = images[0].get('url') if images else None
    
    # Calculate total duration (we'll need to fetch tracks for this, but for now return basic info)
    total_tracks = playlist_info.get('tracks', {}).get('total', 0)
    
    return {
        'playlist_id': playlist_id,
        'name': playlist_info.get('name'),
        'description': playlist_info.get('description'),
        'thumbnail_url': thumbnail_url,
        'owner': playlist_info.get('owner', {}).get('display_name') or playlist_info.get('owner', {}).get('id'),
        'total_tracks': total_tracks,
        'public': playlist_info.get('public', False),
        'followers': playlist_info.get('followers', {}).get('total', 0)
    }

def get_playlist_tracks_basic(playlist_url, spotify_client=None):
    """
    Get basic track information from a Spotify playlist (no audio features/BPM).
    
    Args:
        playlist_url: Spotify playlist URL or URI
        spotify_client: Optional Spotify client (creates new one if not provided)
    
    Returns:
        Tuple of (list of dictionaries containing basic track information, playlist_name)
    """
    if spotify_client is None:
        spotify_client = get_spotify_client()
    
    # Extract playlist ID from URL
    playlist_id = extract_playlist_id(playlist_url)
    
    # Get playlist info to get the name
    playlist_info = spotify_client.playlist(playlist_id)
    playlist_name = playlist_info['name']
    
    # Get playlist tracks
    results = spotify_client.playlist_tracks(playlist_id)
    tracks = results['items']
    
    # Handle pagination if playlist has more than 100 tracks
    while results['next']:
        results = spotify_client.next(results)
        tracks.extend(results['items'])
    
    # Extract basic track information (no audio features)
    track_info_list = []
    
    for item in tracks:
        if item['track'] is None:
            continue
            
        track = item['track']
        track_id = track.get('id')
        
        # Skip tracks without IDs
        if not track_id:
            continue
        
        # Extract album art URL
        album_art_url = get_album_art_url(track['album'])
        
        # Basic track information only
        track_info = {
            'title': track['name'],
            'artists': [artist['name'] for artist in track['artists']],
            'album': track['album']['name'],
            'album_art_url': album_art_url,
            'album_release_date': track['album']['release_date'],
            'duration_ms': track['duration_ms'],
            'duration_min': round(track['duration_ms'] / 60000, 2),
            'popularity': track['popularity'],
            'track_id': track_id,
            'track_url': track['external_urls']['spotify'],
            'preview_url': track.get('preview_url')
        }
        
        track_info_list.append(track_info)
    
    return track_info_list, playlist_name


def get_playlist_tracks(playlist_url, spotify_client=None, progress_callback=None):
    """
    Get all tracks and their information from a Spotify playlist, including audio features.
    
    Args:
        playlist_url: Spotify playlist URL or URI
        spotify_client: Optional Spotify client (creates new one if not provided)
        progress_callback: Optional callback for progress updates
    
    Returns:
        Tuple of (list of dictionaries containing track information, playlist_name)
    """
    # Get basic tracks first
    track_info_list, playlist_name = get_playlist_tracks_basic(playlist_url, spotify_client)
    
    # Calculate BPM from Spotify preview URLs using librosa
    # Use progress callback if provided (for streaming updates)
    track_info_list = add_audio_features_to_tracks(
        track_info_list, 
        max_workers=4,  # Reduced for CPU-intensive audio processing
        spotify_client=spotify_client,
        progress_callback=progress_callback
    )
    
    return track_info_list, playlist_name

