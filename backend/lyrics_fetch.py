import time
from lyricsgenius import Genius
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable

# Load environment variables from .env file
load_dotenv()

def get_genius_client():
    """
    Create and return a Genius client instance.
    
    Returns:
        Genius client instance
    """
    genius_token = os.getenv('GENIUS_ACCESS_TOKEN')
    if not genius_token:
        raise ValueError("GENIUS_ACCESS_TOKEN not found in environment variables")
    
    genius = Genius(genius_token)
    # Configure options
    genius.verbose = False  # Turn off status messages
    genius.remove_section_headers = True  # Remove [Chorus], [Verse] etc.
    genius.skip_non_songs = False  # Include all results
    
    return genius

def fetch_lyrics_single(track: Dict, genius_client: Genius) -> Dict:
    """
    Fetch lyrics for a single track.
    
    Args:
        track: Track dictionary with 'title' and 'artists' fields
        genius_client: Genius client instance
    
    Returns:
        Updated track dictionary with lyrics added
    """
    title = track.get('title', '')
    artists = track.get('artists', [])
    artist = artists[0] if artists else ''
    
    # Skip if lyrics already exist
    if 'lyrics' in track and track['lyrics']:
        return track
    
    try:
        # Search for the song using Genius
        song = genius_client.search_song(title, artist)
        
        if song and song.lyrics:
            # Clean up the lyrics
            lyrics = song.lyrics.strip()
            lyrics = lyrics.split('Embed')[0].strip() if 'Embed' in lyrics else lyrics
            
            track['lyrics'] = lyrics
            track['lyrics_source'] = 'genius'
            track['genius_url'] = song.url if hasattr(song, 'url') else None
        else:
            track['lyrics'] = None
            track['lyrics_source'] = None
            
    except Exception as e:
        track['lyrics'] = None
        track['lyrics_source'] = None
    
    # Small delay for rate limiting (reduced since we're parallelizing)
    time.sleep(0.1)
    
    return track

def fetch_lyrics_for_tracks(tracks: List[Dict], genius_client=None, max_workers: int = 8, progress_callback: Optional[Callable] = None):
    """
    Fetch lyrics for all tracks in a list using Genius API with parallel processing.
    
    Args:
        tracks: List of track dictionaries (must have 'title' and 'artists' fields)
        genius_client: Optional Genius client (creates new one if not provided)
        max_workers: Maximum number of worker threads (default 8 to respect rate limits)
        progress_callback: Optional callback function(current, total) for progress updates
    
    Returns:
        Updated tracks list with lyrics added
    """
    if genius_client is None:
        genius_client = get_genius_client()
    
    total_tracks = len(tracks)
    completed = 0
    
    # Create a dictionary to store results with index as key
    results_dict = {}
    
    def fetch_with_index(index: int, track: Dict) -> tuple:
        """Fetch lyrics and return tuple of (index, updated_track)"""
        return (index, fetch_lyrics_single(track.copy(), genius_client))
    
    # Use ThreadPoolExecutor to fetch in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_index = {
            executor.submit(fetch_with_index, i, track): i 
            for i, track in enumerate(tracks)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_index):
            index, updated_track = future.result()
            results_dict[index] = updated_track
            completed += 1
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(completed, total_tracks, 'lyrics')
    
    # Return results in the same order as input
    return [results_dict[i] for i in range(len(tracks))]

