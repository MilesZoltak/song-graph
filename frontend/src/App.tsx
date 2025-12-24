import { useState, useRef, useEffect } from 'react';
import PlaylistInput from './components/PlaylistInput';
import SearchDrawer from './components/SearchDrawer';
import PlaylistWithSongs from './components/PlaylistWithSongs';
import ScatterPlot from './components/ScatterPlot';
import ProgressBar from './components/ProgressBar';
import Shimmer from './components/Shimmer';
import type { PlaylistData, PlaylistMetadata } from './types';

function App() {
  const [playlistData, setPlaylistData] = useState<PlaylistData | null>(null);
  const [playlistMetadata, setPlaylistMetadata] = useState<PlaylistMetadata | null>(null);
  const [loadingMetadata, setLoadingMetadata] = useState<boolean>(false);
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false);
  const [progress, setProgress] = useState<{ stage: string; current: number; total: number; message?: string } | null>(null);
  const [useRelativeSentiment, setUseRelativeSentiment] = useState(true); // true = playlist-relative, false = absolute
  
  // Ref to always have access to latest playlistData (avoids stale closure issues)
  const playlistDataRef = useRef<PlaylistData | null>(null);
  useEffect(() => {
    playlistDataRef.current = playlistData;
  }, [playlistData]);

  const handleTracksFetched = (data: PlaylistData) => {
    // Show tracks immediately (may have BPM or may be placeholders)
    playlistDataRef.current = data; // Update ref immediately
    setPlaylistData(data);
  };

  const handleMetadataFetchedWithPlaceholders = (metadata: PlaylistMetadata) => {
    setPlaylistMetadata(metadata);
    // Auto-collapse drawer when new playlist metadata is fetched
    setDrawerOpen(false);
  };

  const handlePlaylistProcessed = (data: PlaylistData) => {
    // Update with full data (includes sentiment)
    setPlaylistData(data);
    // Keep drawer closed after processing
    setDrawerOpen(false);
  };

  const handleMetadataFetched = (metadata: PlaylistMetadata) => {
    handleMetadataFetchedWithPlaceholders(metadata);
  };

  const handleMetadataLoading = (loading: boolean) => {
    setLoadingMetadata(loading);
  };

  const handleProgressUpdate = (progressUpdate: { stage: string; current: number; total: number; message?: string; track_update?: any }) => {
    setProgress(progressUpdate);
    
    // Update individual track if track_update is present
    // Use ref to get latest playlistData (avoids stale closure issue)
    if (progressUpdate.track_update && playlistDataRef.current) {
      // Use functional update to ensure we're working with latest state
      setPlaylistData(prevData => {
        if (!prevData) return prevData;
        
        const updatedTracks = prevData.tracks.map(track => 
          track.track_id === progressUpdate.track_update.track_id
            ? { ...track, ...progressUpdate.track_update }
            : track
        );
        
        // Return a completely new object to force re-render
        return {
          ...prevData,
          tracks: updatedTracks
        };
      });
    }
  };

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      {/* Flowing gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-950 via-green-900 to-black animate-gradient-flow"></div>
      <div className="absolute inset-0 bg-gradient-to-tr from-black via-emerald-900/50 to-green-800/30 animate-gradient-flow-reverse"></div>
      
      {/* Animated orbs for flowy effect */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-800/20 rounded-full blur-3xl animate-pulse-slow"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-green-900/20 rounded-full blur-3xl animate-pulse-slow-delayed"></div>
      
      {/* Search Drawer - appears at top when metadata exists */}
      {playlistMetadata && (
        <SearchDrawer
          onPlaylistProcessed={handlePlaylistProcessed}
          onMetadataFetched={handleMetadataFetched}
          onTracksFetched={handleTracksFetched}
          onMetadataLoading={handleMetadataLoading}
          onProgressUpdate={handleProgressUpdate}
          isCollapsed={!drawerOpen}
          onToggleCollapse={() => setDrawerOpen(!drawerOpen)}
        />
      )}

      <div className={`container mx-auto px-4 relative z-10 transition-all duration-300 ${
        playlistMetadata ? (drawerOpen ? 'pt-40' : 'pt-20') : ''
      }`}>
        {/* Centered Search Bar - Only show when no metadata yet */}
        {!playlistMetadata && !loadingMetadata && (
          <div className="flex items-center justify-center min-h-screen">
            <div className="w-full max-w-3xl">
              <PlaylistInput 
                onPlaylistProcessed={handlePlaylistProcessed}
                onMetadataFetched={handleMetadataFetched}
                onTracksFetched={handleTracksFetched}
                onMetadataLoading={handleMetadataLoading}
                onProgressUpdate={handleProgressUpdate}
              />
            </div>
          </div>
        )}

        {/* Playlist Section */}
        {(playlistMetadata || loadingMetadata) && (
          <div className="py-12">
            {/* Show shimmer while loading metadata */}
            {loadingMetadata && <Shimmer />}
            
            {/* Show progress bar when processing */}
            {progress && progress.stage !== 'complete' && (
              <div className="mb-8">
                <ProgressBar
                  stage={progress.stage}
                  current={progress.current}
                  total={progress.total}
                  message={progress.message}
                />
              </div>
            )}
            
            {/* Show combined header + songs when metadata is available */}
            {playlistMetadata && !loadingMetadata && (
              <div className="space-y-8 pb-12">
                {playlistData && (
                  <>
                    <PlaylistWithSongs
                      metadata={playlistMetadata}
                      tracks={playlistData.tracks}
                      runtimeMinutes={playlistData.tracks.reduce((sum, track) => sum + (track.duration_min || 0), 0)}
                      useRelativeSentiment={useRelativeSentiment}
                    />
                    {(() => {
                      // Check if all tracks have both BPM and sentiment resolved (either value or error)
                      const allFeaturesLoaded = playlistData.tracks.every(track =>
                        track.tempo !== undefined && track.sentiment_score !== undefined
                      );
                      
                      return allFeaturesLoaded && (
                        <>
                          <ScatterPlot 
                            playlistData={playlistData} 
                            useRelativeSentiment={useRelativeSentiment}
                          />
                          {/* Sentiment Mode Toggle - Below Graph */}
                          <div className="flex justify-center items-center gap-4 py-6">
                            <span className="text-emerald-200 font-medium">Absolute</span>
                            <button
                              onClick={() => setUseRelativeSentiment(!useRelativeSentiment)}
                              className={`relative inline-flex h-8 w-16 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 ${
                                useRelativeSentiment ? 'bg-emerald-600' : 'bg-gray-600'
                              }`}
                              role="switch"
                              aria-checked={useRelativeSentiment}
                            >
                              <span
                                className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-lg transition-transform ${
                                  useRelativeSentiment ? 'translate-x-9' : 'translate-x-1'
                                }`}
                              />
                            </button>
                            <span className="text-emerald-200 font-medium">Playlist-Relative</span>
                          </div>
                        </>
                      );
                    })()}
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

