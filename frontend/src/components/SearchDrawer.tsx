import { useState } from 'react';
import PlaylistInput from './PlaylistInput';
import type { PlaylistData, PlaylistMetadata } from '../types';

interface SearchDrawerProps {
  onPlaylistProcessed: (data: PlaylistData) => void;
  onMetadataFetched: (metadata: PlaylistMetadata) => void;
  onTracksFetched?: (data: PlaylistData) => void;
  onMetadataLoading?: (loading: boolean) => void;
  onProgressUpdate?: (progress: { stage: string; current: number; total: number; message?: string; track_update?: any }) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

function SearchDrawer({ 
  onPlaylistProcessed, 
  onMetadataFetched,
  onTracksFetched,
  onMetadataLoading,
  onProgressUpdate,
  isCollapsed,
  onToggleCollapse 
}: SearchDrawerProps) {
  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      {/* Collapsed state - just a button/bar at top */}
      <div className={`bg-emerald-950/90 backdrop-blur-md border-b border-emerald-800/50 shadow-lg transition-all duration-300 ease-in-out overflow-hidden ${
        isCollapsed ? 'max-h-16' : 'max-h-screen'
      }`}>
        {isCollapsed ? (
          <div className="container mx-auto px-4 py-3">
            <button
              onClick={onToggleCollapse}
              className="w-full flex items-center justify-between text-emerald-300 hover:text-emerald-200 transition-colors group"
            >
              <span className="text-sm font-medium flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Search for another playlist
              </span>
              <svg 
                className="w-5 h-5 transform transition-transform group-hover:scale-110" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        ) : (
          <div className="container mx-auto px-4 py-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-emerald-200 font-semibold flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Search Playlist
              </h3>
              <button
                onClick={onToggleCollapse}
                className="text-emerald-400 hover:text-emerald-300 transition-colors p-2 hover:bg-emerald-900/30 rounded-lg"
                aria-label="Close search"
              >
                <svg 
                  className="w-6 h-6" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="max-w-3xl mx-auto">
              <PlaylistInput 
                onPlaylistProcessed={onPlaylistProcessed}
                onMetadataFetched={onMetadataFetched}
                onTracksFetched={onTracksFetched}
                onMetadataLoading={onMetadataLoading}
                onProgressUpdate={onProgressUpdate}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SearchDrawer;

