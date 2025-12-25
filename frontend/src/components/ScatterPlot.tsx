import { useState, useEffect } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { PlaylistData, PlotDataPoint, Track } from '../types';

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: PlotDataPoint;
  }>;
}

const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-4 border border-gray-300 rounded-lg shadow-lg">
        {data.album_art_url && (
          <img 
            src={data.album_art_url} 
            alt={`${data.title} album art`}
            className="w-32 h-32 object-cover rounded mb-2"
          />
        )}
        <p className="font-bold text-lg">{data.title}</p>
        <p className="text-gray-600">{data.artists.join(', ')}</p>
        <div className="mt-2 space-y-1 text-sm">
          <p><span className="font-semibold">Tempo:</span> {data.tempo ? `${data.tempo.toFixed(1)} BPM` : 'N/A'}</p>
          <p>
            <span className="font-semibold">Sentiment:</span> {
              data.sentiment_score !== null && data.sentiment_score !== undefined
                ? `${(data.sentiment_score * 100).toFixed(1)}% (${data.sentiment_score > 0.5 ? 'Happy' : 'Sad'})`
                : 'N/A'
            }
          </p>
        </div>
      </div>
    );
  }
  return null;
};

interface CustomDotProps {
  cx?: number;
  cy?: number;
  payload?: PlotDataPoint;
}

const CustomDot = ({ cx, cy, payload }: CustomDotProps) => {
  if (!cx || !cy || !payload) return null;
  
  return (
    <g>
      <circle cx={cx} cy={cy} r={6} fill="#3b82f6" opacity={0.7} />
      <text
        x={cx}
        y={cy - 10}
        textAnchor="middle"
        fontSize="10"
        fill="#374151"
        className="font-medium"
      >
        {payload.title.length > 15 ? payload.title.substring(0, 15) + '...' : payload.title}
      </text>
    </g>
  );
};

interface ScatterPlotProps {
  playlistData: PlaylistData | null;
}

function ScatterPlot({ playlistData }: ScatterPlotProps) {
  const [isPortrait, setIsPortrait] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const checkOrientation = () => {
      const portrait = window.innerHeight > window.innerWidth;
      const mobile = window.innerWidth < 768;
      setIsPortrait(portrait);
      setIsMobile(mobile);
    };

    checkOrientation();
    window.addEventListener('resize', checkOrientation);
    window.addEventListener('orientationchange', checkOrientation);

    return () => {
      window.removeEventListener('resize', checkOrientation);
      window.removeEventListener('orientationchange', checkOrientation);
    };
  }, []);

  const toggleFullscreen = () => {
    if (!isFullscreen) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
    setIsFullscreen(!isFullscreen);
  };

  if (!playlistData || !playlistData.tracks || playlistData.tracks.length === 0) {
    return (
      <div className="w-full h-96 flex items-center justify-center bg-gray-50 rounded-lg">
        <p className="text-gray-500">No data to display. Process a playlist to see the visualization.</p>
      </div>
    );
  }

  // Filter tracks that have both tempo and sentiment_score
  const plotData: PlotDataPoint[] = playlistData.tracks
    .filter((track: Track) => 
      track.tempo !== null && 
      track.tempo !== undefined && 
      track.sentiment_score !== null && 
      track.sentiment_score !== undefined
    )
    .map((track: Track) => ({
      ...track,
      x: track.sentiment_score!,
      y: track.tempo!,
    }));

  if (plotData.length === 0) {
    return (
      <div className="w-full h-96 flex items-center justify-center bg-gray-50 rounded-lg">
        <p className="text-gray-500">No tracks with both tempo and sentiment data available.</p>
      </div>
    );
  }

  // Show rotation prompt on mobile portrait
  if (isMobile && isPortrait) {
    return (
      <div className="w-full bg-gradient-to-br from-emerald-900 to-green-800 rounded-lg shadow-md p-8">
        <div className="flex flex-col items-center justify-center text-center text-white space-y-6">
          <svg 
            className="w-24 h-24 animate-bounce" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" 
            />
          </svg>
          <div>
            <h3 className="text-2xl font-bold mb-2">Rotate Your Device</h3>
            <p className="text-emerald-100">
              For the best graph viewing experience, please rotate your device to landscape mode.
            </p>
          </div>
          <div className="flex items-center space-x-4 text-emerald-200">
            <svg className="w-16 h-16" fill="currentColor" viewBox="0 0 24 24">
              <rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" strokeWidth="2" fill="none"/>
            </svg>
            <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
              <path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z"/>
            </svg>
            <svg className="w-16 h-16" fill="currentColor" viewBox="0 0 24 24">
              <rect x="3" y="3" width="14" height="18" rx="2" stroke="currentColor" strokeWidth="2" fill="none"/>
            </svg>
          </div>
        </div>
      </div>
    );
  }

  // Calculate height based on device and fullscreen state
  const chartHeight = isMobile 
    ? (isFullscreen ? window.innerHeight - 80 : window.innerHeight - 200)
    : 600;

  return (
    <div className={`w-full bg-white ${
      isFullscreen 
        ? 'fixed inset-0 z-50 rounded-none p-0' 
        : 'rounded-lg shadow-md ' + (isMobile && !isPortrait ? 'p-2' : 'p-6')
    }`}>
      <div className={`flex items-center justify-between ${isFullscreen ? 'p-2 mb-1' : 'mb-4'}`}>
        <div>
          {!isFullscreen && (
            <>
              <h2 className={`font-bold ${isMobile ? 'text-lg' : 'text-2xl'}`}>Song Analysis</h2>
              {!isMobile && (
                <p className="text-gray-600 text-sm mt-1">
                  Tempo vs Sentiment: Each dot represents a song. Hover to see details.
                </p>
              )}
            </>
          )}
        </div>
        {isMobile && !isPortrait && (
          <button
            onClick={toggleFullscreen}
            className="px-3 py-2 bg-emerald-600 text-white rounded-lg text-sm hover:bg-emerald-700 transition-colors flex-shrink-0 ml-auto"
          >
            {isFullscreen ? 'Exit' : 'Fullscreen'}
          </button>
        )}
      </div>
      
      <ResponsiveContainer width="100%" height={chartHeight}>
        <ScatterChart
          margin={{ 
            top: (isMobile || isFullscreen) ? 2 : 20, 
            right: (isMobile || isFullscreen) ? 2 : 20, 
            bottom: (isMobile || isFullscreen) ? 2 : 60, 
            left: (isMobile || isFullscreen) ? 2 : 60 
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            type="number" 
            dataKey="x" 
            name="Sentiment"
            domain={[0, 1]}
            hide={(isMobile || isFullscreen)}
            label={!isMobile && !isFullscreen ? {
              value: 'Sentiment (Sad → Happy)', 
              position: 'insideBottom', 
              offset: -10,
              style: { fontSize: 12 }
            } : undefined}
            tickFormatter={(value: number) => (value * 100).toFixed(0) + '%'}
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            type="number" 
            dataKey="y" 
            name="Tempo"
            hide={(isMobile || isFullscreen)}
            label={!isMobile && !isFullscreen ? {
              value: 'Tempo (BPM)', 
              angle: -90, 
              position: 'insideLeft',
              style: { fontSize: 12 }
            } : undefined}
            tick={{ fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Scatter 
            name="Songs" 
            data={plotData} 
            shape={<CustomDot />}
          >
            {plotData.map((_, index) => (
              <Cell key={`cell-${index}`} fill="#3b82f6" />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      
      {!isFullscreen && (
        <div className={`mt-4 text-gray-600 ${isMobile ? 'text-xs' : 'text-sm'}`}>
          <p>Showing {plotData.length} of {playlistData.track_count} tracks</p>
        </div>
      )}
    </div>
  );
}

export default ScatterPlot;

