"""
Calculate BPM using librosa by analyzing Spotify preview URLs (30-second clips).
Uses spotify-preview-finder to get preview URLs when Spotify API returns null.
"""
import librosa
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple, Callable
import tempfile
import os
from spotify_preview_finder import search_and_get_links

def get_preview_url_with_finder(title: str, artist: str, spotify_credentials: tuple) -> Optional[str]:
    """
    Get preview URL using spotify-preview-finder.
    
    Args:
        title: Song title
        artist: Artist name
        spotify_credentials: Tuple of (client_id, client_secret)
    
    Returns:
        Preview URL or None
    """
    try:
        client_id, client_secret = spotify_credentials
        query = f"{title} {artist}"
        
        result = search_and_get_links(query, client_id, client_secret, limit=1)
        
        # The function returns a dict with 'success' and 'results' keys
        if result and result.get('success') and result.get('results'):
            return result['results'][0]['previewUrl']
    except Exception as e:
        print(f"Error using spotify-preview-finder: {e}")
    
    return None

def calculate_bpm_from_preview_url(preview_url: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Download preview and calculate BPM using librosa.
    
    Args:
        preview_url: URL to the Spotify preview audio
    
    Returns:
        Tuple of (BPM value or None, error message or None)
    """
    if not preview_url:
        return None, "No preview URL available"
    
    audio_file = None
    try:
        # Download audio
        response = requests.get(preview_url, timeout=10)
        response.raise_for_status()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.write(response.content)
        temp_file.close()
        audio_file = temp_file.name
        
        # Load and analyze
        y, sr = librosa.load(audio_file, duration=30)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # Extract BPM value
        if isinstance(tempo, np.ndarray):
            bpm = float(tempo[0]) if len(tempo) > 0 else float(tempo)
        else:
            bpm = float(tempo)
        
        return bpm, None
        
    except Exception as e:
        return None, f"Error: {str(e)[:50]}"
    finally:
        # Clean up temporary file
        if audio_file and os.path.exists(audio_file):
            try:
                os.remove(audio_file)
            except:
                pass

def analyze_track_with_index(index: int, track: Dict, spotify_credentials: tuple = None) -> Tuple[int, Dict]:
    """
    Calculate BPM for a track and return tuple of (index, updated_track).
    
    Args:
        index: Track index in the list
        track: Track dictionary
        spotify_credentials: Optional tuple of (client_id, client_secret)
    
    Returns:
        Tuple of (index, updated_track_dict)
    """
    track_copy = track.copy()
    title = track_copy.get('title', 'Unknown')
    artists = track_copy.get('artists', [])
    artist = artists[0] if artists else 'Unknown'
    preview_url = track_copy.get('preview_url')
    
    # Try to get preview URL if not available from API
    if not preview_url and spotify_credentials:
        preview_url = get_preview_url_with_finder(title, artist, spotify_credentials)
    
    if preview_url:
        bpm, error = calculate_bpm_from_preview_url(preview_url)
        
        if bpm is not None:
            track_copy['tempo'] = bpm
            track_copy['audio_features_error'] = None
        else:
            track_copy['tempo'] = None
            track_copy['audio_features_error'] = error
    else:
        track_copy['tempo'] = None
        track_copy['audio_features_error'] = "No preview URL available"
    
    return (index, track_copy)

def add_audio_features_to_tracks(tracks: List[Dict], max_workers: int = 4, spotify_client=None, progress_callback: Optional[Callable] = None) -> List[Dict]:
    """
    Calculate BPM for all tracks using their preview URLs.
    Uses spotify-preview-finder to get preview URLs when Spotify API returns null.
    
    Args:
        tracks: List of track dictionaries
        max_workers: Maximum number of worker threads (default 4 for CPU-intensive work)
        spotify_client: Not used (kept for API compatibility)
        progress_callback: Optional callback function(current, total, stage) for progress updates
    
    Returns:
        Updated list of track dictionaries with tempo/BPM added
    """
    if not tracks:
        return tracks
    
    total_tracks = len(tracks)
    completed = 0
    results_dict = {}
    
    # Get Spotify credentials for spotify-preview-finder
    spotify_credentials = None
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    if client_id and client_secret:
        spotify_credentials = (client_id, client_secret)
    
    print(f"\nStarting BPM analysis for {total_tracks} tracks (parallel: {max_workers} workers)...")
    
    # Use ThreadPoolExecutor to analyze in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_index = {
            executor.submit(analyze_track_with_index, i, track, spotify_credentials): i 
            for i, track in enumerate(tracks)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_index):
            try:
                index, updated_track = future.result()
                results_dict[index] = updated_track
                completed += 1
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(completed, total_tracks, 'audio_features')
            except Exception as e:
                print(f"Error processing track: {e}")
    
    print(f"✓ Completed BPM analysis: {completed}/{total_tracks} tracks\n")
    
    # Return results in the same order as input
    return [results_dict[i] for i in range(len(tracks))]
