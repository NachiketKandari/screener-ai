const WIDTHS = [72, 63, 86, 89, 90, 65, 68, 80, 78, 94, 71, 88, 91, 99, 69, 82, 77, 85, 87, 92, 76, 83, 70, 95, 98, 67, 73, 93, 75, 84];

export function SkeletonTable({ rows = 5, cols = 8 }: { rows?: number; cols?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <tr key={i}>
          {Array.from({ length: cols }).map((_, j) => (
            <td key={j} className="px-4 py-2.5">
              <div className="h-4 bg-muted rounded animate-pulse" style={{ width: `${WIDTHS[(i * cols + j) % WIDTHS.length]}%` }} />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}
