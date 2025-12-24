import React from 'react';

interface ProgressBarProps {
  stage: string;
  current: number;
  total: number;
  message?: string;
}

function ProgressBar({ stage, current, total, message }: ProgressBarProps) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
  
  const getStageLabel = (stage: string): string => {
    switch (stage) {
      case 'tracks':
        return 'Fetching tracks';
      case 'audio_features':
        return 'Fetching audio features';
      case 'lyrics':
        return 'Fetching lyrics';
      case 'sentiment':
        return 'Analyzing sentiment';
      case 'complete':
        return 'Complete';
      case 'error':
        return 'Error';
      default:
        return 'Processing';
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto mb-6 bg-emerald-950/30 backdrop-blur-sm rounded-xl border border-emerald-800/30 p-6">
      <div className="flex items-center justify-between mb-2">
        <span className="text-emerald-200 font-medium">{getStageLabel(stage)}</span>
        <span className="text-emerald-300 text-sm">{current} / {total}</span>
      </div>
      
      {message && (
        <p className="text-emerald-300/70 text-sm mb-3">{message}</p>
      )}
      
      <div className="w-full bg-emerald-900/30 rounded-full h-3 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-emerald-600 to-green-600 transition-all duration-300 ease-out rounded-full"
          style={{ width: `${percentage}%` }}
        >
          <div className="h-full w-full bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
        </div>
      </div>
      
      <div className="mt-2 text-right">
        <span className="text-emerald-300 text-sm font-medium">{percentage}%</span>
      </div>
    </div>
  );
}

export default ProgressBar;

