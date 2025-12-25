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
  const [tempoProgress, setTempoProgress] = useState<{ current: number; total: number; complete: boolean } | null>(null);
  const [sentimentProgress, setSentimentProgress] = useState<{ current: number; total: number; complete: boolean } | null>(null);
  
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
    // Update individual track if track_update is present
    if (progressUpdate.track_update && playlistDataRef.current) {
      setPlaylistData(prevData => {
        if (!prevData) {
          console.log('[App] handleProgressUpdate: prevData is null, skipping update');
          return prevData;
        }
        
        const trackUpdate = progressUpdate.track_update;
        const foundTrack = prevData.tracks.find(t => t.track_id === trackUpdate.track_id);
        if (!foundTrack) {
          console.log('[App] Track not found in current data:', trackUpdate.track_id);
        }
        
        const updatedTracks = prevData.tracks.map(track => 
          track.track_id === trackUpdate.track_id
            ? { ...track, ...trackUpdate }
            : track
        );
        
        // Count how many tracks have been processed (have BPM and sentiment or errors)
        const bpmCompleted = updatedTracks.filter(t => t.tempo !== undefined || t.audio_features_error).length;
        const sentimentCompleted = updatedTracks.filter(t => t.sentiment_score !== undefined || t.sentiment_error).length;
        const totalTracks = updatedTracks.length;
        
        console.log(`[App] Track update applied. BPM: ${bpmCompleted}/${totalTracks}, Sentiment: ${sentimentCompleted}/${totalTracks}`);
        
        // Update tempo progress
        setTempoProgress({
          current: bpmCompleted,
          total: totalTracks,
          complete: bpmCompleted === totalTracks
        });
        
        // Update sentiment progress
        setSentimentProgress({
          current: sentimentCompleted,
          total: totalTracks,
          complete: sentimentCompleted === totalTracks
        });
        
        return {
          ...prevData,
          tracks: updatedTracks
        };
      });
    } else {
      // Initialize progress bars when tracks are first loaded
      if (progressUpdate.stage === 'tracks' || progressUpdate.stage === 'processing') {
        const total = progressUpdate.total || 0;
        console.log(`[App] Initializing progress bars with ${total} tracks`);
        setTempoProgress({ current: 0, total, complete: false });
        setSentimentProgress({ current: 0, total, complete: false });
      }
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
            
            {/* Show progress bars when processing */}
            {(tempoProgress || sentimentProgress) && !(tempoProgress?.complete && sentimentProgress?.complete) && (
              <div className="mb-8 space-y-4">
                {/* Show tempo progress */}
                {tempoProgress && (
                  tempoProgress.complete ? (
                    // Show completion message only if sentiment is still working
                    sentimentProgress && !sentimentProgress.complete && (
                      <div className="w-full max-w-4xl mx-auto bg-emerald-950/30 backdrop-blur-sm rounded-xl border border-green-500/50 p-4">
                        <div className="flex items-center gap-2 text-green-400 font-medium">
                          <span>✓</span>
                          <span>Tempo detection complete</span>
                        </div>
                      </div>
                    )
                  ) : (
                    <ProgressBar
                      label="Detecting tempo"
                      current={tempoProgress.current}
                      total={tempoProgress.total}
                      complete={tempoProgress.complete}
                    />
                  )
                )}
                
                {/* Show sentiment progress */}
                {sentimentProgress && (
                  sentimentProgress.complete ? (
                    // Show completion message only if tempo is still working
                    tempoProgress && !tempoProgress.complete && (
                      <div className="w-full max-w-4xl mx-auto bg-emerald-950/30 backdrop-blur-sm rounded-xl border border-green-500/50 p-4">
                        <div className="flex items-center gap-2 text-green-400 font-medium">
                          <span>✓</span>
                          <span>Sentiment analysis complete</span>
                        </div>
                      </div>
                    )
                  ) : (
                    <ProgressBar
                      label="Analyzing sentiment"
                      current={sentimentProgress.current}
                      total={sentimentProgress.total}
                      complete={sentimentProgress.complete}
                    />
                  )
                )}
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
                    />
                    {(() => {
                      // Check if all tracks have both BPM and sentiment resolved (either value or error)
                      const allFeaturesLoaded = playlistData.tracks.every(track => {
                        const hasTempo = track.tempo !== undefined || track.audio_features_error;
                        const hasSentiment = track.sentiment_score !== undefined || track.sentiment_error;
                        return hasTempo && hasSentiment;
                      });
                      
                      return allFeaturesLoaded && (
                        <ScatterPlot playlistData={playlistData} />
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

