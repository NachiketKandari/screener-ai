"use client";

interface Props {
  totalCount: number;
  queryTimeMs: number;
  sortBy: string;
  sortDir: string;
  warnings: string[];
  onSortChange: (sortBy: string, sortDir: "asc" | "desc") => void;
  sortColumns?: { value: string; label: string }[];
}

const DEFAULT_SORT_COLUMNS = [
  { value: "market_cap_crore", label: "Market Cap" },
  { value: "pe_ratio", label: "P/E" },
  { value: "roe_pct", label: "ROE" },
  { value: "current_price", label: "Price" },
  { value: "revenue_growth_pct", label: "Revenue Growth" },
  { value: "earnings_growth_pct", label: "Earnings Growth" },
  { value: "debt_to_equity", label: "D/E" },
  { value: "dividend_yield_pct", label: "Div Yield" },
  { value: "pb_ratio", label: "P/B" },
  { value: "eps_ttm", label: "EPS" },
];

export function SummaryBar({
  totalCount,
  queryTimeMs,
  sortBy,
  sortDir,
  warnings,
  onSortChange,
  sortColumns,
}: Props) {
  const columns = sortColumns && sortColumns.length > 0 ? sortColumns : DEFAULT_SORT_COLUMNS;

  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-3 text-sm text-muted-foreground">
        <span className="font-medium text-foreground">
          {totalCount.toLocaleString()} stocks match
        </span>
        <span>·</span>
        <span>{queryTimeMs.toFixed(1)}ms</span>
        <span>·</span>
        Sorted by{" "}
        <select
          className="border rounded px-2 py-1 text-xs bg-background"
          value={`${sortBy}-${sortDir}`}
          onChange={(e) => {
            const [by, dir] = e.target.value.split("-");
            onSortChange(by, dir as "asc" | "desc");
          }}
        >
          {columns.map((col) => (
            <option key={`${col.value}-desc`} value={`${col.value}-desc`}>
              {col.label} ↓
            </option>
          ))}
          {columns.map((col) => (
            <option key={`${col.value}-asc`} value={`${col.value}-asc`}>
              {col.label} ↑
            </option>
          ))}
        </select>
      </div>
      {warnings.length > 0 && (
        <div className="text-xs text-amber-600">
          {warnings.length} warning{warnings.length > 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
}
