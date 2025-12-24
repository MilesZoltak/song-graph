interface CellShimmerProps {
  width?: string;
}

function CellShimmer({ width = "w-12" }: CellShimmerProps) {
  return (
    <div className="flex justify-center items-center">
      <div className={`${width} h-4 bg-emerald-800/30 rounded animate-pulse`}></div>
    </div>
  );
}

export default CellShimmer;

