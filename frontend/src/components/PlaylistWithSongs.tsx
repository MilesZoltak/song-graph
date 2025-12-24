import type { Track, PlaylistMetadata } from '../types';
import CellShimmer from './CellShimmer';

interface PlaylistWithSongsProps {
  metadata: PlaylistMetadata;
  tracks: Track[];
  runtimeMinutes?: number;
  useRelativeSentiment?: boolean;
}

function PlaylistWithSongs({ metadata, tracks, runtimeMinutes, useRelativeSentiment = true }: PlaylistWithSongsProps) {
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
      <div className="p-6 border-b border-emerald-800/30">
        <div className="flex gap-6">
          {/* Thumbnail */}
          {metadata.thumbnail_url && (
            <img
              src={metadata.thumbnail_url}
              alt={metadata.name}
              className="w-48 h-48 rounded-lg object-cover flex-shrink-0 shadow-lg"
            />
          )}
          
          {/* Content */}
          <div className="flex-1 flex flex-col justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">{metadata.name}</h1>
              
              {metadata.owner && (
                <p className="text-emerald-300 mb-4">By {metadata.owner}</p>
              )}
              
              {metadata.description && (
                <p className="text-emerald-200/80 text-sm mb-4 line-clamp-2">
                  {metadata.description}
                </p>
              )}
            </div>
            
            {/* Stats */}
            <div className="flex gap-6 text-emerald-300">
              <div className="text-sm">
                <span className="font-semibold">{metadata.total_tracks}</span> tracks
              </div>
              {runtimeMinutes !== undefined && (
                <div className="text-sm">
                  <span className="font-semibold">{formatRuntime(runtimeMinutes)}</span>
                </div>
              )}
              {metadata.followers > 0 && (
                <div className="text-sm">
                  {formatFollowers(metadata.followers)}
                </div>
              )}
              {metadata.public && (
                <div className="text-sm">
                  Public
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Songs Table Section */}
      <div className="max-h-96 overflow-y-auto">
        <table className="w-full">
          <thead className="bg-emerald-950 sticky top-0 z-10 shadow-sm">
            <tr>
              <th className="px-4 py-3 text-center text-sm font-semibold text-emerald-200 bg-emerald-950">Art</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-emerald-200 bg-emerald-950">Track</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-emerald-200 bg-emerald-950">Album</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-emerald-200 bg-emerald-950">Runtime</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-emerald-200 bg-emerald-950">BPM</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-emerald-200 bg-emerald-950">Sentiment</th>
            </tr>
          </thead>
          <tbody>
            {tracks.map((track, index) => (
              <tr 
                key={track.track_id || index} 
                className="border-b border-emerald-800/20 hover:bg-emerald-900/20 transition-colors"
              >
                <td className="px-4 py-3">
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
                <td className="px-4 py-3">
                  <div className="flex flex-col">
                    <span className="text-white font-medium">{track.title}</span>
                    <span className="text-emerald-300/70 text-sm">{track.artists.join(', ')}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-emerald-300/80 text-sm text-center">{track.album}</td>
                <td className="px-4 py-3 text-emerald-300/70 text-sm text-center">
                  {formatDuration(track.duration_min)}
                </td>
                <td className="px-4 py-3 text-emerald-300/70 text-sm text-center">
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
                    <CellShimmer width="w-12" />
                  )}
                </td>
                <td className="px-4 py-3 text-emerald-300/70 text-sm text-center">
                  {(() => {
                    const score = useRelativeSentiment 
                      ? track.sentiment_score 
                      : (track as any).raw_sentiment || track.sentiment_score;
                    
                    if (score !== undefined) {
                      // Score is defined (either has value or is null/error)
                      if (score !== null) {
                        return `${(score * 100).toFixed(0)}%`;
                      } else if ((track as any).sentiment_error) {
                        return (
                          <span className="text-red-400" title={(track as any).sentiment_error}>
                            ⚠️
                          </span>
                        );
                      } else {
                        return <span className="text-emerald-400/50">-</span>;
                      }
                    } else {
                      // Score is undefined - still loading
                      return <CellShimmer width="w-12" />;
                    }
                  })()}
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

