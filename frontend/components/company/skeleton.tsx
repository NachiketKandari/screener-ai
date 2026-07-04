export function CompanySkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6 animate-pulse">
      <div className="h-4 w-32 bg-muted rounded" />
      <div className="space-y-2">
        <div className="h-8 w-64 bg-muted rounded" />
        <div className="h-5 w-48 bg-muted rounded" />
      </div>
      <div className="flex gap-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-9 w-20 bg-muted rounded" />
        ))}
      </div>
      <div className="h-[350px] bg-muted rounded-lg" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="h-20 bg-muted rounded-lg" />
        ))}
      </div>
    </div>
  );
}
