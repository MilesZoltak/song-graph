import type { PlaylistMetadata } from '../types';

interface PlaylistHeaderProps {
  metadata: PlaylistMetadata;
  runtimeMinutes?: number;
}

function PlaylistHeader({ metadata, runtimeMinutes }: PlaylistHeaderProps) {
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
    <div className="w-full max-w-4xl mx-auto mb-8 animate-fade-in">
      <div className="bg-emerald-950/30 backdrop-blur-sm rounded-xl p-6 border border-emerald-800/30">
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
    </div>
  );
}

export default PlaylistHeader;

