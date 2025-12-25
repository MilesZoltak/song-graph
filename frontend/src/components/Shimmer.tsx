function Shimmer() {
  return (
    <div className="w-full max-w-4xl mx-auto mb-8">
      <div className="bg-emerald-950/30 backdrop-blur-sm rounded-xl p-4 sm:p-6 border border-emerald-800/30">
        <div className="flex flex-col landscape:flex-row sm:flex-row gap-4 sm:gap-6">
          {/* Thumbnail shimmer */}
          <div className="flex-shrink-0 w-full landscape:w-auto sm:w-auto flex justify-center landscape:justify-start sm:justify-start">
            <div className="w-64 h-64 landscape:w-40 landscape:h-40 sm:w-56 sm:h-56 bg-emerald-900/50 rounded-lg animate-shimmer"></div>
          </div>
          
          {/* Content shimmer */}
          <div className="flex-1 space-y-3 sm:space-y-4">
            {/* Title */}
            <div className="h-6 sm:h-8 bg-emerald-900/50 rounded w-3/4 animate-shimmer"></div>
            
            {/* Owner */}
            <div className="h-4 sm:h-5 bg-emerald-900/50 rounded w-1/2 animate-shimmer-delayed"></div>
            
            {/* Description - hidden on mobile */}
            <div className="space-y-2 hidden sm:block">
              <div className="h-4 bg-emerald-900/50 rounded w-full animate-shimmer"></div>
              <div className="h-4 bg-emerald-900/50 rounded w-5/6 animate-shimmer-delayed"></div>
            </div>
            
            {/* Stats */}
            <div className="flex flex-wrap gap-3 sm:gap-6 pt-2 sm:pt-4">
              <div className="h-5 sm:h-6 bg-emerald-900/50 rounded w-20 sm:w-24 animate-shimmer"></div>
              <div className="h-5 sm:h-6 bg-emerald-900/50 rounded w-20 sm:w-24 animate-shimmer-delayed"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Shimmer;

