import type { PlaylistData } from '../types';

interface PlaylistPreviewProps {
  playlistData: PlaylistData | null;
}

function PlaylistPreview({ playlistData }: PlaylistPreviewProps) {
  if (!playlistData) return null;

  return (
    <div className="w-full max-w-4xl mx-auto mb-8 bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">{playlistData.playlist_name}</h2>
      <p className="text-gray-600 mb-4">{playlistData.track_count} tracks</p>
      
      <div className="max-h-96 overflow-y-auto">
        <table className="w-full text-left">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              <th className="px-4 py-2 font-semibold">#</th>
              <th className="px-4 py-2 font-semibold">Title</th>
              <th className="px-4 py-2 font-semibold">Artist</th>
              <th className="px-4 py-2 font-semibold">Tempo</th>
              <th className="px-4 py-2 font-semibold">Sentiment</th>
            </tr>
          </thead>
          <tbody>
            {playlistData.tracks.map((track, index) => (
              <tr key={track.track_id || index} className="border-b hover:bg-gray-50">
                <td className="px-4 py-2 text-gray-600">{index + 1}</td>
                <td className="px-4 py-2 font-medium">{track.title}</td>
                <td className="px-4 py-2 text-gray-600">{track.artists.join(', ')}</td>
                <td className="px-4 py-2">
                  {track.tempo ? `${track.tempo.toFixed(1)} BPM` : 'N/A'}
                </td>
                <td className="px-4 py-2">
                  {track.sentiment_score !== null && track.sentiment_score !== undefined ? (
                    <span className={`px-2 py-1 rounded text-sm ${
                      track.sentiment_score > 0.5 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {(track.sentiment_score * 100).toFixed(1)}%
                    </span>
                  ) : (
                    'N/A'
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

export default PlaylistPreview;

