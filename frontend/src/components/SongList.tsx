import type { Track } from '../types';

interface SongListProps {
  tracks: Track[];
}

function SongList({ tracks }: SongListProps) {
  const formatDuration = (minutes: number): string => {
    const mins = Math.floor(minutes);
    const secs = Math.floor((minutes - mins) * 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-emerald-950/30 backdrop-blur-sm rounded-xl border border-emerald-800/30 shadow-lg overflow-hidden">
      <div className="p-4 border-b border-emerald-800/30">
        <h3 className="text-xl font-bold text-white">Songs</h3>
      </div>
      
      <div className="max-h-96 overflow-y-auto">
        <table className="w-full">
          <thead className="bg-emerald-900/30 sticky top-0 z-10">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold text-emerald-200">#</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-emerald-200">Title</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-emerald-200">Artist</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-emerald-200">Album</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-emerald-200">Runtime</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-emerald-200">BPM</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-emerald-200">Sentiment</th>
            </tr>
          </thead>
          <tbody>
            {tracks.map((track, index) => (
              <tr 
                key={track.track_id || index} 
                className="border-b border-emerald-800/20 hover:bg-emerald-900/20 transition-colors"
              >
                <td className="px-4 py-3 text-emerald-300/70 text-sm">{index + 1}</td>
                <td className="px-4 py-3 text-white font-medium">{track.title}</td>
                <td className="px-4 py-3 text-emerald-200">{track.artists.join(', ')}</td>
                <td className="px-4 py-3 text-emerald-300/80 text-sm">{track.album}</td>
                <td className="px-4 py-3 text-emerald-300/70 text-sm">
                  {formatDuration(track.duration_min)}
                </td>
                <td className="px-4 py-3 text-emerald-300/70 text-sm">
                  {track.tempo ? `${Math.round(track.tempo)}` : '-'}
                </td>
                <td className="px-4 py-3 text-emerald-300/70 text-sm">
                  {track.sentiment_score !== null && track.sentiment_score !== undefined 
                    ? `${(track.sentiment_score * 100).toFixed(0)}%` 
                    : '-'
                  }
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default SongList;

