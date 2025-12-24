from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import json
import asyncio
import uuid
import numpy as np
from typing import Dict, Any, Optional, List
from .pipeline import process_playlist, save_playlist_json
from .playlist_fetch import get_spotify_client, get_playlist_metadata, get_playlist_tracks, get_playlist_tracks_basic
from .audio_features import add_audio_features_to_tracks
from .lyrics_fetch import get_genius_client, fetch_lyrics_for_tracks
from .sentiment_analysis import create_sentiment_classifier, add_sentiment_to_tracks

app = FastAPI(title="Song Graph API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",  # Alternative React port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",  # Vercel preview deployments
        os.getenv("FRONTEND_URL", ""),  # Production frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration for worker counts
BPM_MAX_WORKERS = int(os.getenv('BPM_MAX_WORKERS', '8'))
SENTIMENT_MAX_WORKERS = int(os.getenv('SENTIMENT_MAX_WORKERS', '8'))

# Initialize shared clients (loaded once at startup)
spotify_client = None
genius_client = None
sentiment_classifier = None

# Progress tracking for streaming updates
progress_store: Dict[str, Dict[str, Any]] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize shared clients on startup."""
    global spotify_client, genius_client, sentiment_classifier
    
    print("Initializing clients...")
    try:
        # Load sentiment model once (this takes time, so do it at startup)
        print("Loading sentiment analysis model...")
        sentiment_classifier = create_sentiment_classifier()
        print("✓ Sentiment model loaded")
    except Exception as e:
        print(f"Warning: Could not load sentiment model: {e}")
        print("Model will be loaded on first request")


def normalize_sentiment_scores(tracks: List[Dict]) -> List[Dict]:
    """
    Apply robust playlist-relative normalization to sentiment scores.
    
    Uses median/IQR (robust to outliers) + sigmoid squashing.
    Result: 0.5 = playlist average, not absolute neutral.
    
    This makes visualization more meaningful by showing relative
    emotional positioning within the playlist context.
    
    Args:
        tracks: List of track dictionaries with sentiment_score
    
    Returns:
        Updated tracks with normalized_sentiment and raw_sentiment fields
    """
    # Extract raw scores (only from tracks that have sentiment)
    scores = [t.get('sentiment_score') for t in tracks 
              if t.get('sentiment_score') is not None]
    
    if len(scores) < 2:
        # Need at least 2 songs to normalize - leave as is
        return tracks
    
    # Robust center and scale using median and IQR
    median = np.median(scores)
    q75, q25 = np.percentile(scores, [75, 25])
    iqr = q75 - q25
    
    # Avoid division by zero
    if iqr < 1e-6:
        # All songs have similar sentiment - map everything to 0.5
        for track in tracks:
            if track.get('sentiment_score') is not None:
                track['raw_sentiment'] = track['sentiment_score']
                track['normalized_sentiment'] = 0.5
                track['sentiment_score'] = 0.5  # Replace with normalized
        return tracks
    
    # Z-score normalization + sigmoid squashing to [0, 1]
    for track in tracks:
        if track.get('sentiment_score') is not None:
            # Calculate z-score using robust statistics
            z = (track['sentiment_score'] - median) / iqr
            
            # Sigmoid function: maps (-inf, inf) to (0, 1)
            # Center point (z=0) maps to 0.5
            normalized = 1 / (1 + np.exp(-z))
            
            # Store both raw and normalized
            track['raw_sentiment'] = track['sentiment_score']
            track['normalized_sentiment'] = normalized
            track['sentiment_score'] = normalized  # Replace with normalized for display
    
    return tracks


class PlaylistRequest(BaseModel):
    playlist_url: str

class TrackListRequest(BaseModel):
    tracks: List[Dict[str, Any]]
    playlist_name: Optional[str] = "Unknown Playlist"

@app.post("/api/process-playlist")
async def process_playlist_endpoint(request: PlaylistRequest):
    """
    Process a Spotify playlist through the full pipeline.
    
    Returns playlist data with tracks, lyrics, and sentiment analysis.
    """
    global spotify_client, genius_client, sentiment_classifier
    
    try:
        # Use shared clients or create new ones
        sp_client = spotify_client or get_spotify_client()
        gen_client = genius_client or get_genius_client()
        sent_classifier = sentiment_classifier or create_sentiment_classifier()
        
        # Process playlist
        result = await process_playlist(
            request.playlist_url,
            spotify_client=sp_client,
            genius_client=gen_client,
            sentiment_classifier=sent_classifier
        )
        
        # Store clients for reuse
        if spotify_client is None:
            spotify_client = sp_client
        if genius_client is None:
            genius_client = gen_client
        if sentiment_classifier is None:
            sentiment_classifier = sent_classifier
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing playlist: {str(e)}")

async def process_playlist_with_progress(playlist_url: str, job_id: str):
    """Background task to process playlist and update progress."""
    global spotify_client, genius_client, sentiment_classifier, progress_store
    
    try:
        # Initialize progress
        progress_store[job_id] = {
            'stage': 'tracks',
            'current': 0,
            'total': 0,
            'message': 'Starting...',
            'tracks': [],
            'error': None
        }
        
        # Use shared clients
        sp_client = spotify_client or get_spotify_client()
        gen_client = genius_client or get_genius_client()
        sent_classifier = sentiment_classifier or create_sentiment_classifier()
        
        if spotify_client is None:
            spotify_client = sp_client
        if genius_client is None:
            genius_client = gen_client
        if sentiment_classifier is None:
            sentiment_classifier = sent_classifier
        
        # Step 1: Fetch basic track info (no BPM yet)
        print(f"\nStep 1: Fetching basic track information...")
        tracks, playlist_name = get_playlist_tracks_basic(
            playlist_url,
            spotify_client=sp_client
        )
        
        progress_store[job_id]['total'] = len(tracks)
        progress_store[job_id]['tracks'] = tracks
        progress_store[job_id]['playlist_name'] = playlist_name
        progress_store[job_id].update({
            'stage': 'tracks',
            'message': 'Tracks loaded'
        })
        print(f"✓ Fetched {len(tracks)} tracks\n")
        
        # Step 2: Calculate BPM with streaming updates
        def audio_progress(current, total, stage):
            progress_store[job_id].update({
                'stage': 'audio_features',
                'current': current,
                'total': total,
                'message': f'Calculating BPM: {current}/{total}'
            })
        
        print(f"\nStep 2: Starting BPM calculation for {len(tracks)} tracks...")
        tracks = add_audio_features_to_tracks(
            tracks,
            max_workers=4,
            spotify_client=sp_client,
            progress_callback=audio_progress
        )
        progress_store[job_id]['tracks'] = tracks
        print(f"✓ BPM calculation complete\n")
        
        progress_store[job_id].update({
            'stage': 'lyrics',
            'message': 'Fetching lyrics...'
        })
        
        # Step 3: Fetch lyrics with progress
        def lyrics_progress(current, total, stage):
            progress_store[job_id].update({
                'stage': 'lyrics',
                'current': current,
                'total': total,
                'message': f'Fetching lyrics: {current}/{total}'
            })
        
        print(f"\nStep 3: Starting lyrics fetch for {len(tracks)} tracks...")
        tracks = fetch_lyrics_for_tracks(tracks, gen_client, max_workers=8, progress_callback=lyrics_progress)
        print(f"✓ Lyrics fetch complete for {len(tracks)} tracks\n")
        progress_store[job_id]['tracks'] = tracks
        progress_store[job_id].update({
            'stage': 'sentiment',
            'current': 0,
            'message': 'Analyzing sentiment...'
        })
        
        # Step 4: Analyze sentiment (one by one)
        def sentiment_progress(current, total, stage, track=None):
            # Update the specific track in the tracks list FIRST
            if track:
                track_id = track.get('track_id')
                tracks_list = progress_store[job_id]['tracks']
                for i, t in enumerate(tracks_list):
                    if t.get('track_id') == track_id:
                        # Update the track with sentiment data
                        tracks_list[i] = track.copy()  # Make a copy to ensure update
                        # Force update the progress_store reference
                        progress_store[job_id]['tracks'] = tracks_list
                        break
            
            # Then update progress counters (this triggers SSE update)
            progress_store[job_id].update({
                'stage': 'sentiment',
                'current': current,
                'total': total,
                'message': f'Analyzing sentiment: {current}/{total}'
            })
        
        print(f"\nStep 4: Starting sentiment analysis for {len(tracks)} tracks...")
        tracks = add_sentiment_to_tracks(tracks, sent_classifier, progress_callback=sentiment_progress)
        print(f"✓ Sentiment analysis complete for {len(tracks)} tracks\n")
        
        # Step 5: Normalize sentiment scores (playlist-relative)
        print(f"\nStep 5: Normalizing sentiment scores across playlist...")
        tracks = normalize_sentiment_scores(tracks)
        progress_store[job_id]['tracks'] = tracks
        print(f"✓ Sentiment normalization complete\n")
        
        # Step 6: Save to JSON
        from .pipeline import save_playlist_json
        output_file = save_playlist_json(tracks, playlist_name)
        
        # Final result - explicitly include tracks with normalized sentiment
        progress_store[job_id]['tracks'] = tracks  # Update tracks reference first
        progress_store[job_id].update({
            'stage': 'complete',
            'current': len(tracks),
            'total': len(tracks),
            'message': 'Complete',
            'playlist_name': playlist_name,
            'output_file': output_file
        })
        
        print(f"✓ Processing complete. Tracks with sentiment: {sum(1 for t in tracks if t.get('sentiment_score') is not None)}/{len(tracks)}")
        
    except Exception as e:
        import traceback
        error_message = str(e)
        error_trace = traceback.format_exc()
        print(f"\n{'='*80}")
        print(f"ERROR in process_playlist_with_progress:")
        print(f"{'='*80}")
        print(error_message)
        print(error_trace)
        print(f"{'='*80}\n")
        progress_store[job_id]['error'] = error_message
        progress_store[job_id]['stage'] = 'error'

async def process_features_with_progress(tracks: List[Dict[str, Any]], job_id: str):
    """Background task to process BPM and sentiment in parallel."""
    global spotify_client, genius_client, sentiment_classifier, progress_store
    
    try:
        # Initialize progress
        progress_store[job_id] = {
            'stage': 'processing',
            'current': 0,
            'total': len(tracks),
            'message': 'Starting feature extraction...',
            'tracks': tracks,
            'bpm_completed': 0,
            'sentiment_completed': 0,
            'error': None
        }
        
        # Use shared clients
        sp_client = spotify_client or get_spotify_client()
        gen_client = genius_client or get_genius_client()
        sent_classifier = sentiment_classifier or create_sentiment_classifier()
        
        if spotify_client is None:
            spotify_client = sp_client
        if genius_client is None:
            genius_client = gen_client
        if sentiment_classifier is None:
            sentiment_classifier = sent_classifier
        
        # Create callback functions that update individual tracks
        def bpm_track_callback(index, updated_track):
            """Called when a single track's BPM is calculated"""
            tracks_list = progress_store[job_id]['tracks']
            tracks_list[index] = updated_track
            progress_store[job_id]['tracks'] = tracks_list
            progress_store[job_id]['bpm_completed'] = progress_store[job_id].get('bpm_completed', 0) + 1
        
        def sentiment_track_callback(index, updated_track):
            """Called when a single track's sentiment is calculated"""
            tracks_list = progress_store[job_id]['tracks']
            tracks_list[index] = updated_track
            progress_store[job_id]['tracks'] = tracks_list
            progress_store[job_id]['sentiment_completed'] = progress_store[job_id].get('sentiment_completed', 0) + 1
        
        # Run BPM and sentiment extraction in parallel
        print(f"\nStarting parallel feature extraction for {len(tracks)} tracks...")
        print(f"  - BPM workers: {BPM_MAX_WORKERS}")
        print(f"  - Sentiment workers: {SENTIMENT_MAX_WORKERS}")
        
        # Execute in parallel using asyncio.gather
        import concurrent.futures
        from concurrent.futures import ThreadPoolExecutor
        
        def run_bpm_pipeline():
            """Run BPM pipeline in thread pool"""
            from .audio_features import analyze_track_with_index
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            spotify_credentials = (client_id, client_secret) if client_id and client_secret else None
            
            results = {}
            with ThreadPoolExecutor(max_workers=BPM_MAX_WORKERS) as executor:
                future_to_index = {
                    executor.submit(analyze_track_with_index, i, track, spotify_credentials): i 
                    for i, track in enumerate(tracks)
                }
                
                for future in concurrent.futures.as_completed(future_to_index):
                    try:
                        index, updated_track = future.result()
                        results[index] = updated_track
                        bpm_track_callback(index, updated_track)
                    except Exception as e:
                        print(f"Error processing BPM for track: {e}")
            
            return results
        
        def run_sentiment_pipeline():
            """Run sentiment pipeline (lyrics + analysis) in thread pool"""
            from .sentiment_analysis import analyze_sentiment_single
            from .lyrics_fetch import fetch_lyrics_single
            
            results = {}
            with ThreadPoolExecutor(max_workers=SENTIMENT_MAX_WORKERS) as executor:
                def process_sentiment_for_track(index, track):
                    # First fetch lyrics
                    track_with_lyrics = fetch_lyrics_single(track.copy(), gen_client)
                    # Then analyze sentiment
                    track_with_sentiment = analyze_sentiment_single(track_with_lyrics, sent_classifier)
                    return (index, track_with_sentiment)
                
                future_to_index = {
                    executor.submit(process_sentiment_for_track, i, track): i 
                    for i, track in enumerate(tracks)
                }
                
                for future in concurrent.futures.as_completed(future_to_index):
                    try:
                        index, updated_track = future.result()
                        results[index] = updated_track
                        sentiment_track_callback(index, updated_track)
                    except Exception as e:
                        print(f"Error processing sentiment for track: {e}")
            
            return results
        
        # Run both pipelines concurrently using asyncio
        loop = asyncio.get_event_loop()
        bpm_results, sentiment_results = await asyncio.gather(
            loop.run_in_executor(None, run_bpm_pipeline),
            loop.run_in_executor(None, run_sentiment_pipeline)
        )
        
        print(f"✓ Feature extraction complete")
        print(f"  - BPM: {len(bpm_results)}/{len(tracks)} tracks")
        print(f"  - Sentiment: {len(sentiment_results)}/{len(tracks)} tracks")
        
        # Merge results back into tracks
        final_tracks = []
        for i in range(len(tracks)):
            track = tracks[i].copy()
            if i in bpm_results:
                track.update(bpm_results[i])
            if i in sentiment_results:
                track.update(sentiment_results[i])
            final_tracks.append(track)
        
        # Normalize sentiment scores
        final_tracks = normalize_sentiment_scores(final_tracks)
        
        # Save to JSON
        from .pipeline import save_playlist_json
        playlist_name = progress_store[job_id].get('playlist_name', 'Unknown Playlist')
        output_file = save_playlist_json(final_tracks, playlist_name)
        
        # Mark as complete
        progress_store[job_id]['tracks'] = final_tracks
        progress_store[job_id].update({
            'stage': 'complete',
            'current': len(final_tracks),
            'total': len(final_tracks),
            'message': 'Complete',
            'output_file': output_file
        })
        
        print(f"✓ Processing complete. Output: {output_file}")
        
    except Exception as e:
        import traceback
        error_message = str(e)
        error_trace = traceback.format_exc()
        print(f"\n{'='*80}")
        print(f"ERROR in process_features_with_progress:")
        print(f"{'='*80}")
        print(error_message)
        print(error_trace)
        print(f"{'='*80}\n")
        progress_store[job_id]['error'] = error_message
        progress_store[job_id]['stage'] = 'error'

@app.post("/api/process-playlist-stream")
async def process_playlist_stream_endpoint(request: PlaylistRequest, background_tasks: BackgroundTasks):
    """Start processing playlist and return job ID for polling."""
    job_id = str(uuid.uuid4())
    
    # Start background task
    background_tasks.add_task(process_playlist_with_progress, request.playlist_url, job_id)
    
    return {'job_id': job_id}

@app.post("/api/process-features")
async def process_features_endpoint(request: TrackListRequest, background_tasks: BackgroundTasks):
    """
    Start parallel BPM and sentiment processing for provided tracks.
    Returns job_id for SSE streaming progress updates.
    """
    job_id = str(uuid.uuid4())
    
    # Use playlist name from request
    playlist_name = request.playlist_name or 'Unknown Playlist'
    
    # Store playlist name in progress for later
    progress_store[job_id] = {
        'stage': 'initializing',
        'playlist_name': playlist_name,
        'tracks': request.tracks,
        'current': 0,
        'total': len(request.tracks)
    }
    
    # Start background task for parallel processing
    background_tasks.add_task(process_features_with_progress, request.tracks, job_id)
    
    return {'job_id': job_id}

@app.get("/api/progress/{job_id}")
async def get_progress(job_id: str):
    """Get progress for a processing job."""
    if job_id not in progress_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    progress = progress_store[job_id]
    
    # Clean up completed jobs after 1 hour (simplified - in production use TTL)
    if progress['stage'] == 'complete':
        return progress
    
    return progress

@app.get("/api/progress-stream/{job_id}")
async def stream_progress(job_id: str):
    """Stream progress updates using Server-Sent Events."""
    async def generate():
        last_stage = None
        last_current = -1
        last_bpm_updates = set()  # Track which tracks have BPM sent
        last_sentiment_updates = set()  # Track which tracks have sentiment sent
        tracks_sent = False  # Track whether we've sent the initial track list
        
        while True:
            if job_id not in progress_store:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found'})}\n\n"
                break
            
            progress = progress_store[job_id]
            stage = progress.get('stage')
            current = progress.get('current', 0)
            tracks = progress.get('tracks', [])
            
            # Check for new BPM updates (works for both old and new flow)
            if tracks:
                for i, track in enumerate(tracks):
                    track_id = track.get('track_id')
                    if not track_id:
                        continue
                    
                    # Check for BPM updates
                    if track_id not in last_bpm_updates:
                        tempo = track.get('tempo')
                        audio_error = track.get('audio_features_error')
                        # Send update if BPM is calculated or error occurred
                        if tempo is not None or audio_error:
                            track_update = {
                                'track_id': track_id,
                                'tempo': tempo,
                                'audio_features_error': audio_error
                            }
                            yield f"data: {json.dumps({
                                'type': 'track_update',
                                'field': 'tempo',
                                'track_update': track_update
                            })}\n\n"
                            last_bpm_updates.add(track_id)
                    
                    # Check for sentiment updates
                    if track_id not in last_sentiment_updates:
                        sentiment_score = track.get('sentiment_score')
                        sentiment_error = track.get('sentiment_error')
                        if sentiment_score is not None or sentiment_error:
                            # Send individual track update immediately
                            track_update = {
                                'track_id': track_id,
                                'sentiment_score': sentiment_score,
                                'sentiment_label': track.get('sentiment_label'),
                                'sentiment_error': sentiment_error
                            }
                            yield f"data: {json.dumps({
                                'type': 'track_update',
                                'field': 'sentiment',
                                'track_update': track_update
                            })}\n\n"
                            last_sentiment_updates.add(track_id)
            
            # Send initial tracks as soon as they're available
            if tracks and len(tracks) > 0 and not tracks_sent:
                update = {
                    'type': 'progress',
                    'stage': stage or 'tracks',
                    'current': current,
                    'total': len(tracks),
                    'message': progress.get('message', 'Tracks loaded'),
                    'tracks': tracks,
                    'playlist_name': progress.get('playlist_name', '')
                }
                yield f"data: {json.dumps(update)}\n\n"
                tracks_sent = True
                last_stage = stage
                last_current = current
            
            # Send update if stage or progress changed (and we've already sent tracks)
            elif stage != last_stage or current != last_current:
                # Create update payload
                update_payload = {
                    'type': 'progress',
                    'stage': stage,
                    'current': current,
                    'total': progress.get('total', 0),
                    'message': progress.get('message', '')
                }
                yield f"data: {json.dumps(update_payload)}\n\n"
                last_stage = stage
                last_current = current
            
            # Stop if complete or error
            if stage in ['complete', 'error']:
                # Send final complete message with all tracks (including sentiment)
                complete_data = {
                    'type': 'progress',
                    'stage': stage,
                    'current': progress.get('current', 0),
                    'total': progress.get('total', 0),
                    'message': progress.get('message', ''),
                    'tracks': tracks,  # Include full track list with sentiment
                    'playlist_name': progress.get('playlist_name', ''),
                    'output_file': progress.get('output_file', '')
                }
                yield f"data: {json.dumps(complete_data)}\n\n"
                break
            
            await asyncio.sleep(0.05)  # Poll every 50ms for very responsive updates
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/api/playlists")
async def list_playlists():
    """List all processed playlists."""
    playlists_dir = 'playlists'
    
    if not os.path.exists(playlists_dir):
        return {"playlists": []}
    
    playlist_files = [f for f in os.listdir(playlists_dir) if f.endswith('.json')]
    
    playlists = []
    for filename in playlist_files:
        filepath = os.path.join(playlists_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                playlists.append({
                    'name': filename.replace('.json', '').replace('_', ' '),
                    'filename': filename,
                    'track_count': len(data) if isinstance(data, list) else 0
                })
        except Exception:
            continue
    
    return {"playlists": playlists}

@app.get("/api/playlists/{name}")
async def get_playlist(name: str):
    """Get a specific playlist by name."""
    playlists_dir = 'playlists'
    
    # Sanitize name to match filename format
    safe_name = name.replace(' ', '_')
    filename = f"{safe_name}.json"
    filepath = os.path.join(playlists_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tracks = json.load(f)
        
        # Extract playlist name from first track or filename
        playlist_name = name.replace('_', ' ')
        
        return {
            'playlist_name': playlist_name,
            'track_count': len(tracks),
            'tracks': tracks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading playlist: {str(e)}")

@app.get("/api/playlist-metadata")
async def get_playlist_metadata_endpoint(playlist_url: str):
    """
    Get playlist metadata (name, thumbnail, owner, etc.) without processing tracks.
    Query parameter: playlist_url
    """
    global spotify_client
    
    try:
        # Use shared client or create new one
        sp_client = spotify_client or get_spotify_client()
        
        # Get metadata
        metadata = get_playlist_metadata(playlist_url, sp_client)
        
        # Store client for reuse
        if spotify_client is None:
            spotify_client = sp_client
        
        return metadata
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching playlist metadata: {str(e)}")

@app.get("/api/playlist-with-tracks")
async def get_playlist_with_tracks_endpoint(playlist_url: str):
    """
    Get playlist metadata AND full track list in a single request.
    Returns basic track info (title, artist, album, duration) without BPM or sentiment.
    Query parameter: playlist_url
    """
    global spotify_client
    
    try:
        # Use shared client or create new one
        sp_client = spotify_client or get_spotify_client()
        
        # Get metadata
        metadata = get_playlist_metadata(playlist_url, sp_client)
        
        # Get basic track info (no BPM, no sentiment)
        tracks, playlist_name = get_playlist_tracks_basic(playlist_url, sp_client)
        
        # Store client for reuse
        if spotify_client is None:
            spotify_client = sp_client
        
        # Return combined response
        return {
            "metadata": metadata,
            "tracks": tracks,
            "playlist_name": playlist_name,
            "track_count": len(tracks)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching playlist with tracks: {str(e)}")

@app.get("/api/playlist-tracks")
async def get_playlist_tracks_endpoint(playlist_url: str):
    """
    Get playlist tracks with audio features (BPM/tempo) but without lyrics or sentiment.
    This allows the UI to show tracks immediately while sentiment analysis runs in background.
    Query parameter: playlist_url
    """
    global spotify_client
    
    try:
        # Use shared client or create new one
        sp_client = spotify_client or get_spotify_client()
        
        # Get tracks (includes tempo/BPM from audio features)
        tracks, playlist_name = get_playlist_tracks(playlist_url, sp_client)
        
        # Store client for reuse
        if spotify_client is None:
            spotify_client = sp_client
        
        return {
            'playlist_name': playlist_name,
            'track_count': len(tracks),
            'tracks': tracks
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching playlist tracks: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

