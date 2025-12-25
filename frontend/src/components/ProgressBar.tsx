import React from 'react';

interface ProgressBarProps {
  label: string;
  current: number;
  total: number;
  complete: boolean;
}

function ProgressBar({ label, current, total, complete }: ProgressBarProps) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;

  return (
    <div className={`w-full max-w-4xl mx-auto bg-emerald-950/30 backdrop-blur-sm rounded-xl border ${
      complete ? 'border-green-500/50' : 'border-emerald-800/30'
    } p-6 transition-all duration-300`}>
      <div className="flex items-center justify-between mb-2">
        <span className={`font-medium ${complete ? 'text-green-400' : 'text-emerald-200'}`}>
          {label}
          {complete && (
            <span className="ml-2 inline-block">✓</span>
          )}
        </span>
        <span className="text-emerald-300 text-sm">{current} / {total}</span>
      </div>
      
      <div className="w-full bg-emerald-900/30 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ease-out rounded-full ${
            complete 
              ? 'bg-gradient-to-r from-green-600 to-emerald-600' 
              : 'bg-gradient-to-r from-emerald-600 to-green-600'
          }`}
          style={{ width: `${percentage}%` }}
        >
          {!complete && (
            <div className="h-full w-full bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
          )}
        </div>
      </div>
      
      <div className="mt-2 text-right">
        <span className="text-emerald-300 text-sm font-medium">{percentage}%</span>
      </div>
    </div>
  );
}

export default ProgressBar;

