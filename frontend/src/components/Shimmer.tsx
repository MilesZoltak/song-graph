function Shimmer() {
  return (
    <div className="w-full max-w-4xl mx-auto mb-8">
      <div className="bg-emerald-950/30 backdrop-blur-sm rounded-xl p-6 border border-emerald-800/30">
        <div className="flex gap-6">
          {/* Thumbnail shimmer */}
          <div className="w-48 h-48 bg-emerald-900/50 rounded-lg flex-shrink-0 animate-shimmer"></div>
          
          {/* Content shimmer */}
          <div className="flex-1 space-y-4">
            {/* Title */}
            <div className="h-8 bg-emerald-900/50 rounded w-3/4 animate-shimmer"></div>
            
            {/* Owner */}
            <div className="h-5 bg-emerald-900/50 rounded w-1/2 animate-shimmer-delayed"></div>
            
            {/* Description */}
            <div className="space-y-2">
              <div className="h-4 bg-emerald-900/50 rounded w-full animate-shimmer"></div>
              <div className="h-4 bg-emerald-900/50 rounded w-5/6 animate-shimmer-delayed"></div>
            </div>
            
            {/* Stats */}
            <div className="flex gap-6 pt-4">
              <div className="h-6 bg-emerald-900/50 rounded w-24 animate-shimmer"></div>
              <div className="h-6 bg-emerald-900/50 rounded w-24 animate-shimmer-delayed"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Shimmer;

