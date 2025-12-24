import { useState, FormEvent } from 'react';
import axios from 'axios';
import apiClient from '../api';
import type { PlaylistData, PlaylistMetadata } from '../types';

interface PlaylistInputProps {
  onPlaylistProcessed: (data: PlaylistData) => void;
  onMetadataFetched: (metadata: PlaylistMetadata) => void;
  onTracksFetched?: (data: PlaylistData) => void;
  onMetadataLoading?: (loading: boolean) => void;
  onProgressUpdate?: (progress: { stage: string; current: number; total: number; message?: string; track_update?: any }) => void;
}

function PlaylistInput({ onPlaylistProcessed, onMetadataFetched, onTracksFetched, onMetadataLoading, onProgressUpdate }: PlaylistInputProps) {
  const [playlistUrl, setPlaylistUrl] = useState<string>('');
  const [loadingMetadata, setLoadingMetadata] = useState<boolean>(false);
  const [loadingProcessing, setLoadingProcessing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!playlistUrl.trim()) {
      setError('Please enter a playlist URL');
      return;
    }

    setError(null);
    setLoadingMetadata(true);
    onMetadataLoading?.(true);

    try {
      // Phase 1: Fetch metadata + tracks in a single request
      const response = await apiClient.get('/api/playlist-with-tracks', {
        params: { playlist_url: playlistUrl.trim() }
      });
      
      const { metadata, tracks, playlist_name, track_count } = response.data;
      
      // Display metadata
      onMetadataFetched(metadata);
      
      // Display tracks immediately (with BPM/sentiment as undefined = loading)
      onTracksFetched?.({
        playlist_name: playlist_name,
        track_count: track_count,
        tracks: tracks,
        output_file: ''
      });
      
      setLoadingMetadata(false);
      onMetadataLoading?.(false);
      
      // Phase 2: Start feature processing (BPM + sentiment in parallel)
      setLoadingProcessing(true);
      
      const jobResponse = await apiClient.post<{ job_id: string }>('/api/process-features', {
        tracks: tracks,
        playlist_name: playlist_name
      });
      
      const jobId = jobResponse.data.job_id;
      
      // Connect to progress stream for real-time updates
      const apiBaseUrl = import.meta.env.VITE_API_URL || '';
      const eventSource = new EventSource(`${apiBaseUrl}/api/progress-stream/${jobId}`);
      
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        // Handle track_update messages (sent individually for BPM and sentiment)
        if (data.type === 'track_update' && data.track_update) {
          onProgressUpdate?.({
            stage: data.stage || 'processing',
            current: 0,
            total: 0,
            track_update: data.track_update
          });
          return;
        }
        
        // Handle progress updates
        if (data.type === 'progress' || data.stage) {
          onProgressUpdate?.(data);
        }
        
        // If complete, get final data
        if (data.stage === 'complete') {
          eventSource.close();
          setLoadingProcessing(false);
          
          // Create PlaylistData from progress
          const finalData: PlaylistData = {
            playlist_name: data.playlist_name || playlist_name,
            track_count: data.tracks.length,
            tracks: data.tracks,
            output_file: data.output_file
          };
          
          onPlaylistProcessed(finalData);
        }
        
        // Handle errors
        if (data.stage === 'error' || data.error) {
          eventSource.close();
          setLoadingProcessing(false);
          setError(data.error || data.message || 'Processing failed');
        }
      };
      
      eventSource.onerror = () => {
        eventSource.close();
        setLoadingProcessing(false);
        setError('Connection error. Please try again.');
      };
    } catch (err) {
      setLoadingMetadata(false);
      onMetadataLoading?.(false);
      setLoadingProcessing(false);
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Failed to process playlist. Please try again.');
      } else {
        setError('Failed to process playlist. Please try again.');
      }
      console.error('Error processing playlist:', err);
    }
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Search bar with button inside */}
        <div className="relative">
          <input
            id="playlist-url"
            type="text"
            value={playlistUrl}
            onChange={(e) => setPlaylistUrl(e.target.value)}
            placeholder="Playlist URL..."
            className="w-full px-5 py-4 pr-20 text-lg bg-emerald-950/50 backdrop-blur-sm border-2 border-emerald-800/50 rounded-xl text-white placeholder-emerald-400/60 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all shadow-lg hover:shadow-emerald-900/50 hover:border-emerald-700"
            disabled={loadingMetadata || loadingProcessing}
          />
          <button
            type="submit"
            disabled={loadingMetadata || loadingProcessing || !playlistUrl.trim()}
            className={`absolute right-2 top-2 px-6 py-2 bg-gradient-to-r from-emerald-600 to-green-700 text-white font-semibold rounded-lg hover:from-emerald-500 hover:to-green-600 disabled:from-gray-700 disabled:to-gray-800 disabled:cursor-not-allowed transition-all transform hover:scale-105 disabled:transform-none ${
              playlistUrl.trim() 
                ? 'shadow-lg shadow-emerald-500/50 ring-2 ring-emerald-500/50' 
                : 'shadow-md shadow-emerald-500/20'
            }`}
          >
            {loadingMetadata || loadingProcessing ? (
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              '→'
            )}
          </button>
        </div>
        {error && (
          <div className="p-4 bg-red-900/30 backdrop-blur-sm border-l-4 border-red-500 text-red-200 rounded-lg shadow-lg animate-fade-in">
            <p className="font-medium">{error}</p>
          </div>
        )}
        {loadingProcessing && (
          <div className="text-center py-6">
            <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-emerald-500 border-t-transparent"></div>
            <p className="mt-4 text-emerald-300 font-medium">Analyzing sentiment... This may take a few minutes.</p>
            <p className="mt-2 text-sm text-emerald-400/70">Tracks are shown above. Fetching lyrics and analyzing sentiment...</p>
          </div>
        )}
      </form>
    </div>
  );
}

export default PlaylistInput;

