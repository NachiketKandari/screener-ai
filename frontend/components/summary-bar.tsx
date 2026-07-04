"use client";

interface Props {
  totalCount: number;
  queryTimeMs: number;
  sortBy: string;
  sortDir: string;
  warnings: string[];
  onSortChange: (sortBy: string, sortDir: "asc" | "desc") => void;
}

export function SummaryBar({ totalCount, queryTimeMs, sortBy, sortDir, warnings, onSortChange }: Props) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-3 text-sm text-muted-foreground">
        <span className="font-medium text-foreground">{totalCount.toLocaleString()} stocks match</span>
        <span>·</span>
        <span>{queryTimeMs.toFixed(1)}ms</span>
        <span>·</span>
        <select
          className="border rounded px-2 py-1 text-xs bg-background"
          value={`${sortBy}-${sortDir}`}
          onChange={e => {
            const [by, dir] = e.target.value.split("-");
            onSortChange(by, dir as "asc" | "desc");
          }}
        >
          <option value="market_cap_crore-desc">Market Cap ↓</option>
          <option value="market_cap_crore-asc">Market Cap ↑</option>
          <option value="pe_ratio-asc">P/E ↓</option>
          <option value="pe_ratio-desc">P/E ↑</option>
          <option value="roe_pct-desc">ROE ↓</option>
          <option value="roe_pct-asc">ROE ↑</option>
          <option value="revenue_growth_pct-desc">Revenue Growth ↓</option>
          <option value="current_price-desc">Price ↓</option>
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
