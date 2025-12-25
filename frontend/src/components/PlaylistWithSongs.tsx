import type { Track, PlaylistMetadata } from '../types';
import CellShimmer from './CellShimmer';

interface PlaylistWithSongsProps {
  metadata: PlaylistMetadata;
  tracks: Track[];
  runtimeMinutes?: number;
}

function PlaylistWithSongs({ metadata, tracks, runtimeMinutes }: PlaylistWithSongsProps) {
  const formatDuration = (minutes: number): string => {
    const mins = Math.floor(minutes);
    const secs = Math.floor((minutes - mins) * 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatFollowers = (count: number): string => {
    if (count >= 1000000) {
      return `${(count / 1000000).toFixed(1)}M followers`;
    } else if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K followers`;
    }
    return `${count} followers`;
  };

  const formatRuntime = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-emerald-950/30 backdrop-blur-sm rounded-xl border border-emerald-800/30 shadow-lg overflow-hidden animate-fade-in">
      {/* Playlist Header Section */}
      <div className="p-4 sm:p-6 border-b border-emerald-800/30">
        <div className="flex flex-col landscape:flex-row sm:flex-row gap-4 sm:gap-6">
          {/* Thumbnail */}
          {metadata.thumbnail_url && (
            <div className="flex-shrink-0 w-full landscape:w-auto sm:w-auto flex justify-center landscape:justify-start sm:justify-start">
              <img
                src={metadata.thumbnail_url}
                alt={metadata.name}
                className="w-64 h-64 landscape:w-40 landscape:h-40 sm:w-56 sm:h-56 rounded-lg object-cover shadow-lg"
              />
            </div>
          )}
          
          {/* Content */}
          <div className="flex-1 flex flex-col justify-between">
            <div>
              <h1 className="text-xl landscape:text-lg sm:text-3xl font-bold text-white mb-2">{metadata.name}</h1>
              
              {metadata.owner && (
                <p className="text-emerald-300 text-sm sm:text-base mb-2 sm:mb-4">By {metadata.owner}</p>
              )}
              
              {metadata.description && (
                <p className="text-emerald-200/80 text-sm mb-2 sm:mb-4 line-clamp-2 hidden sm:block">
                  {metadata.description}
                </p>
              )}
            </div>
            
            {/* Stats */}
            <div className="flex flex-wrap gap-3 sm:gap-6 text-emerald-300">
              <div className="text-xs sm:text-sm">
                <span className="font-semibold">{metadata.total_tracks}</span> tracks
              </div>
              {runtimeMinutes !== undefined && (
                <div className="text-xs sm:text-sm">
                  <span className="font-semibold">{formatRuntime(runtimeMinutes)}</span>
                </div>
              )}
              {metadata.followers > 0 && (
                <div className="text-xs sm:text-sm hidden sm:block">
                  {formatFollowers(metadata.followers)}
                </div>
              )}
              {metadata.public && (
                <div className="text-xs sm:text-sm hidden sm:block">
                  Public
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Songs Table Section */}
      <div className="max-h-96 overflow-y-auto overflow-x-auto">
        <table className="w-full">
          <thead className="bg-emerald-950 sticky top-0 z-10 shadow-sm">
            <tr>
              <th className="hidden md:table-cell px-4 py-3 text-center text-sm font-semibold text-emerald-200 bg-emerald-950">Art</th>
              <th className="px-2 md:px-4 py-3 text-left text-sm font-semibold text-emerald-200 bg-emerald-950">Track</th>
              <th className="hidden md:table-cell px-4 py-3 text-center text-sm font-semibold text-emerald-200 bg-emerald-950">Album</th>
              <th className="hidden md:table-cell px-4 py-3 text-center text-sm font-semibold text-emerald-200 bg-emerald-950">Runtime</th>
              <th className="px-2 md:px-4 py-3 text-center text-sm font-semibold text-emerald-200 bg-emerald-950">BPM</th>
              <th className="px-2 md:px-4 py-3 text-center text-sm font-semibold text-emerald-200 bg-emerald-950">Sentiment</th>
            </tr>
          </thead>
          <tbody>
            {tracks.map((track, index) => (
              <tr 
                key={track.track_id || index} 
                className="border-b border-emerald-800/20 hover:bg-emerald-900/20 transition-colors"
              >
                <td className="hidden md:table-cell px-4 py-3">
                  {track.album_art_url ? (
                    <img 
                      src={track.album_art_url} 
                      alt={track.album}
                      className="w-12 h-12 rounded object-cover shadow-md"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded bg-emerald-800/30 flex items-center justify-center">
                      <svg className="w-6 h-6 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z" />
                      </svg>
                    </div>
                  )}
                </td>
                <td className="px-2 md:px-4 py-3">
                  <div className="flex flex-col">
                    <span className="text-white font-medium text-sm md:text-base">{track.title}</span>
                    <span className="text-emerald-300/70 text-xs md:text-sm">{track.artists.join(', ')}</span>
                  </div>
                </td>
                <td className="hidden md:table-cell px-4 py-3 text-emerald-300/80 text-sm text-center">{track.album}</td>
                <td className="hidden md:table-cell px-4 py-3 text-emerald-300/70 text-sm text-center">
                  {formatDuration(track.duration_min)}
                </td>
                <td className="px-2 md:px-4 py-3 text-emerald-300/70 text-xs md:text-sm text-center">
                  {track.tempo !== undefined ? (
                    track.audio_features_error ? (
                      <span className="text-red-400" title={track.audio_features_error}>
                        ⚠️
                      </span>
                    ) : track.tempo !== null ? (
                      `${Math.round(track.tempo)}`
                    ) : (
                      <span className="text-emerald-400/50">-</span>
                    )
                  ) : (
                    <CellShimmer width="w-8 md:w-12" />
                  )}
                </td>
                <td className="px-2 md:px-4 py-3 text-emerald-300/70 text-xs md:text-sm text-center">
                  {track.sentiment_score !== undefined ? (
                    track.sentiment_score !== null ? (
                      `${(track.sentiment_score * 100).toFixed(0)}%`
                    ) : (track as any).sentiment_error ? (
                      <span className="text-red-400" title={(track as any).sentiment_error}>
                        ⚠️
                      </span>
                    ) : (
                      <span className="text-emerald-400/50">-</span>
                    )
                  ) : (
                    <CellShimmer width="w-8 md:w-12" />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default PlaylistWithSongs;

