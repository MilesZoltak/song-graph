import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import os
import json
import re
from dotenv import load_dotenv

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

def get_playlist_tracks(playlist_url):
    """
    Get all tracks and their information from a Spotify playlist.
    
    Args:
        playlist_url: Spotify playlist URL or URI
    
    Returns:
        Tuple of (list of dictionaries containing track information, playlist_name)
    """
    # Set up Spotify client with user authentication
    # This allows access to more playlists including Spotify-curated ones
    # Spotify requires 127.0.0.1 (not localhost) for loopback addresses
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:3000/callback')
    
    print(f"Using redirect URI: {redirect_uri}")
    print("Make sure this EXACT URI is added in your Spotify app settings!\n")
    
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=redirect_uri,
        scope='playlist-read-private playlist-read-collaborative',
        cache_path='.spotify_cache',
        open_browser=True
    ))
    
    # Extract playlist ID from URL
    if 'spotify.com' in playlist_url:
        playlist_id = playlist_url.split('playlist/')[-1].split('?')[0]
    else:
        playlist_id = playlist_url
    
    # Get playlist info to get the name
    print("Fetching playlist information...")
    playlist_info = sp.playlist(playlist_id)
    playlist_name = playlist_info['name']
    print(f"Playlist: {playlist_name}")
    
    # Get playlist tracks
    print("Fetching playlist tracks...")
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    
    # Handle pagination if playlist has more than 100 tracks
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    
    print(f"Found {len(tracks)} tracks. Fetching detailed information...")
    
    # Extract track information
    track_info_list = []
    track_ids = []
    
    for item in tracks:
        if item['track'] is None:
            continue
            
        track = item['track']
        track_ids.append(track['id'])
        
        # Basic track information
        track_info = {
            'title': track['name'],
            'artists': [artist['name'] for artist in track['artists']],
            'album': track['album']['name'],
            'album_release_date': track['album']['release_date'],
            'duration_ms': track['duration_ms'],
            'duration_min': round(track['duration_ms'] / 60000, 2),
            'popularity': track['popularity'],
            'track_id': track['id'],
            'track_url': track['external_urls']['spotify']
        }
        track_info_list.append(track_info)
    
    # Get audio features for all tracks (includes tempo, energy, etc.)
    print("Fetching audio features (tempo, energy, danceability, etc.)...")
    
    # Try using the same authenticated client first
    # If that fails with 403, fall back to client credentials
    audio_features = []
    use_client_creds = False
    
    # Spotify API allows max 100 tracks per request
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        try:
            if use_client_creds:
                # Use client credentials if OAuth failed
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
                )
                sp_features = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
                features = sp_features.audio_features(batch)
            else:
                # Try OAuth token first
                features = sp.audio_features(batch)
            audio_features.extend(features)
        except Exception as e:
            error_str = str(e)
            if ("403" in error_str or "401" in error_str) and not use_client_creds:
                # First failure - try client credentials
                print("OAuth token failed for audio features, trying client credentials...")
                use_client_creds = True
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
                )
                sp_features = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
                try:
                    features = sp_features.audio_features(batch)
                    audio_features.extend(features)
                except Exception as e2:
                    print(f"Error fetching audio features: {e2}")
                    audio_features.extend([None] * len(batch))
            else:
                print(f"Error fetching audio features: {e}")
                audio_features.extend([None] * len(batch))
    
    # Add audio features to track information
    for i, features in enumerate(audio_features):
        if features and isinstance(features, dict):  # Some tracks might not have audio features
            track_info_list[i].update({
                'tempo': features.get('tempo'),
                'key': features.get('key'),
                'mode': features.get('mode'),  # 0 = minor, 1 = major
                'time_signature': features.get('time_signature'),
                'energy': features.get('energy'),
                'danceability': features.get('danceability'),
                'acousticness': features.get('acousticness'),
                'instrumentalness': features.get('instrumentalness'),
                'liveness': features.get('liveness'),
                'loudness': features.get('loudness'),
                'speechiness': features.get('speechiness'),
                'valence': features.get('valence')  # musical positiveness
            })
    
    return track_info_list, playlist_name


def main():
    # Check for credentials
    if not os.getenv('SPOTIFY_CLIENT_ID') or not os.getenv('SPOTIFY_CLIENT_SECRET'):
        print("ERROR: Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your .env file")
        print("\nTo get credentials:")
        print("1. Go to https://developer.spotify.com/dashboard")
        print("2. Log in and create an app")
        print("3. In app settings, add Redirect URI: http://127.0.0.1:3000/callback")
        print("   IMPORTANT: Spotify requires 127.0.0.1 (NOT localhost) for loopback addresses")
        print("   - Copy and paste exactly: http://127.0.0.1:3000/callback")
        print("   - Click 'Add' then 'Save'")
        print("4. Copy the Client ID and Client Secret")
        print("5. Create a .env file in this directory with:")
        print("   SPOTIFY_CLIENT_ID=your-client-id")
        print("   SPOTIFY_CLIENT_SECRET=your-client-secret")
        print("   (Optional) SPOTIFY_REDIRECT_URI=http://127.0.0.1:3000/callback")
        return
    
    print("Note: A browser window will open for Spotify authentication on first run.")
    print("After authenticating, you'll be redirected - just copy the full URL from your browser.\n")
    
    # Get playlist URL from user
    playlist_url = input("Enter Spotify playlist URL: ").strip()
    
    try:
        # Get track information and playlist name
        tracks, playlist_name = get_playlist_tracks(playlist_url)
        
        # Display results
        print(f"\n{'='*80}")
        print(f"Playlist: {playlist_name}")
        print(f"Contains {len(tracks)} tracks")
        print(f"{'='*80}\n")
        
        for i, track in enumerate(tracks, 1):
            print(f"{i}. {track['title']}")
            print(f"   Artists: {', '.join(track['artists'])}")
            print(f"   Album: {track['album']}")
            print(f"   Duration: {track['duration_min']} min")
            print(f"   Popularity: {track['popularity']}/100")
            
            if 'tempo' in track and track['tempo'] is not None:
                print(f"   Tempo: {track['tempo']:.1f} BPM")
                print(f"   Energy: {track['energy']:.2f}")
                print(f"   Danceability: {track['danceability']:.2f}")
                print(f"   Key: {track['key']} ({'Major' if track['mode'] == 1 else 'Minor'})")
            print()
        
        # Create playlists directory if it doesn't exist
        playlists_dir = 'playlists'
        os.makedirs(playlists_dir, exist_ok=True)
        
        # Sanitize playlist name for filename
        safe_filename = sanitize_filename(playlist_name)
        output_file = os.path.join(playlists_dir, f'{safe_filename}.json')
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tracks, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*80}")
        print(f"Data saved to {output_file}")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("1. The playlist URL is correct")
        print("2. The playlist is public or you have access to it")
        print("3. Your Spotify API credentials are valid")


if __name__ == "__main__":
    main()
