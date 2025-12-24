import json
import os
import time
from dotenv import load_dotenv
from lyricsgenius import Genius

# Load environment variables from .env file
load_dotenv()

def fetch_lyrics_for_playlist(playlist_file, genius_client):
    """
    Fetch lyrics for all tracks in a playlist JSON file using Genius API.
    
    Args:
        playlist_file: Path to the playlist JSON file
        genius_client: Genius client instance
    
    Returns:
        Updated tracks list with lyrics added
    """
    # Read the playlist JSON
    with open(playlist_file, 'r', encoding='utf-8') as f:
        tracks = json.load(f)
    
    print(f"Processing {len(tracks)} tracks from {playlist_file}...")
    
    # Process each track
    for i, track in enumerate(tracks, 1):
        title = track.get('title', '')
        artists = track.get('artists', [])
        # Use first artist for search (Genius works better with single artist)
        artist = artists[0] if artists else ''
        
        print(f"[{i}/{len(tracks)}] Searching for: {title} by {artist}")
        
        # Skip if lyrics already exist
        if 'lyrics' in track and track['lyrics']:
            print("  ✓ Lyrics already exist, skipping...")
            continue
        
        try:
            # Search for the song using Genius
            # genius.search_song(title, artist_name)
            song = genius_client.search_song(title, artist)
            
            if song and song.lyrics:
                # Clean up the lyrics (remove section headers if desired)
                lyrics = song.lyrics.strip()
                
                # Remove common Genius footer text
                lyrics = lyrics.split('Embed')[0].strip() if 'Embed' in lyrics else lyrics
                
                track['lyrics'] = lyrics
                track['lyrics_source'] = 'genius'
                track['genius_url'] = song.url if hasattr(song, 'url') else None
                print(f"  ✓ Lyrics fetched successfully ({len(lyrics)} characters)")
            else:
                track['lyrics'] = None
                track['lyrics_source'] = None
                print("  ✗ No lyrics found")
                
        except Exception as e:
            track['lyrics'] = None
            track['lyrics_source'] = None
            print(f"  ✗ Error: {e}")
        
        # Rate limiting - Genius API has rate limits
        # Add a small delay to be respectful
        time.sleep(0.5)
    
    return tracks

def main():
    # Check for Genius access token
    genius_token = os.getenv('GENIUS_ACCESS_TOKEN')
    if not genius_token:
        print("ERROR: Please set GENIUS_ACCESS_TOKEN in your .env file")
        print("\nTo get an access token:")
        print("1. Go to https://genius.com/api-clients")
        print("2. Sign up for a free account (or log in)")
        print("3. Create a new API client")
        print("4. Copy your Client Access Token")
        print("5. Add to your .env file: GENIUS_ACCESS_TOKEN=your-access-token")
        return
    
    # Initialize Genius client
    genius = Genius(genius_token)
    # Configure options
    genius.verbose = False  # Turn off status messages
    genius.remove_section_headers = True  # Remove [Chorus], [Verse] etc.
    genius.skip_non_songs = False  # Include all results
    
    # Get playlist file path
    playlists_dir = 'playlists'
    if not os.path.exists(playlists_dir):
        print(f"Error: {playlists_dir} directory not found!")
        print("Please run playlist_fetch.py first to create playlist JSON files.")
        return
    
    # List available playlist files
    playlist_files = [f for f in os.listdir(playlists_dir) if f.endswith('.json')]
    
    if not playlist_files:
        print(f"No JSON files found in {playlists_dir}/")
        print("Please run playlist_fetch.py first to create playlist JSON files.")
        return
    
    print("Available playlists:")
    for i, filename in enumerate(playlist_files, 1):
        print(f"  {i}. {filename}")
    
    # Let user choose a playlist
    choice = input("\nEnter playlist number (or 'all' to process all playlists): ").strip()
    
    if choice.lower() == 'all':
        files_to_process = [os.path.join(playlists_dir, f) for f in playlist_files]
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(playlist_files):
                files_to_process = [os.path.join(playlists_dir, playlist_files[idx])]
            else:
                print("Invalid selection!")
                return
        except ValueError:
            print("Invalid input!")
            return
    
    # Process each selected playlist
    for playlist_file in files_to_process:
        print(f"\n{'='*80}")
        print(f"Processing: {os.path.basename(playlist_file)}")
        print(f"{'='*80}\n")
        
        try:
            # Fetch lyrics
            updated_tracks = fetch_lyrics_for_playlist(playlist_file, genius)
            
            # Save updated playlist with lyrics
            with open(playlist_file, 'w', encoding='utf-8') as f:
                json.dump(updated_tracks, f, indent=2, ensure_ascii=False)
            
            # Count success rate
            tracks_with_lyrics = sum(1 for t in updated_tracks if t.get('lyrics'))
            print(f"\n{'='*80}")
            print(f"Completed: {os.path.basename(playlist_file)}")
            print(f"Lyrics found: {tracks_with_lyrics}/{len(updated_tracks)} tracks")
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"Error processing {playlist_file}: {e}")

if __name__ == "__main__":
    main()
