"use client";

import { SkeletonTable } from "./skeleton-table";
import { ChevronLeft, ChevronRight, ArrowUp, ArrowDown } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  columns: string[];
  rows: (string | number | null)[][];
  loading: boolean;
  limit: number;
  offset: number;
  totalCount: number;
  onPageChange: (offset: number) => void;
  sortBy?: string;
  sortDir?: string;
  onSort?: (column: string) => void;
}

// Columns that can be sorted (must exist in the backend SORT_COLUMNS whitelist)
const SORTABLE_COLUMNS = new Set([
  "market_cap_crore",
  "pe_ratio",
  "roe_pct",
  "current_price",
  "revenue_growth_pct",
  "earnings_growth_pct",
  "debt_to_equity",
  "dividend_yield_pct",
  "pb_ratio",
  "eps_ttm",
]);

function formatCell(value: string | number | null): string {
  if (value === null) return "—";
  if (typeof value === "number") {
    if (Number.isInteger(value)) return value.toLocaleString();
    return value.toFixed(2);
  }
  return String(value);
}

function formatColumnLabel(col: string): string {
  const labels: Record<string, string> = {
    ticker: "Ticker",
    company_name: "Company",
    sector: "Sector",
    current_price: "CMP (₹)",
    pe_ratio: "P/E",
    roe_pct: "ROE %",
    market_cap_crore: "Market Cap (Cr)",
    revenue_growth_pct: "Revenue Growth %",
    debt_to_equity: "D/E",
    dividend_yield_pct: "Div Yield %",
    pb_ratio: "P/B",
    eps_ttm: "EPS",
    earnings_growth_pct: "Earnings Growth %",
  };
  return labels[col] || col.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function ResultsTable({
  columns,
  rows,
  loading,
  limit,
  offset,
  totalCount,
  onPageChange,
  sortBy,
  sortDir,
  onSort,
}: Props) {
  const totalPages = Math.ceil(totalCount / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  if (rows.length === 0 && !loading) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg font-medium">No stocks match your filters.</p>
        <p className="text-sm mt-1">Try broadening your criteria.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto border rounded-lg">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-muted/50 border-b">
              {columns.map((col) => {
                const isSortable = SORTABLE_COLUMNS.has(col);
                const isActive = sortBy === col;

                return (
                  <th
                    key={col}
                    className={`text-left px-4 py-2.5 font-medium text-muted-foreground whitespace-nowrap ${
                      isSortable
                        ? "cursor-pointer select-none hover:text-foreground hover:bg-muted transition-colors"
                        : ""
                    } ${isActive ? "text-foreground" : ""}`}
                    onClick={() => {
                      if (isSortable && onSort) onSort(col);
                    }}
                  >
                    <span className="inline-flex items-center gap-1">
                      {formatColumnLabel(col)}
                      {isActive && sortDir === "asc" && (
                        <ArrowUp className="h-3 w-3" />
                      )}
                      {isActive && sortDir === "desc" && (
                        <ArrowDown className="h-3 w-3" />
                      )}
                    </span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <SkeletonTable rows={Math.min(limit, 10)} cols={columns.length} />
            ) : (
              rows.map((row, i) => (
                <tr
                  key={i}
                  className="border-b last:border-0 hover:bg-muted/30 transition-colors"
                >
                  {row.map((cell, j) => (
                    <td key={j} className="px-4 py-2.5 whitespace-nowrap">
                      {formatCell(cell)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalCount > limit && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            Showing {offset + 1}–{Math.min(offset + limit, totalCount)} of{" "}
            {totalCount.toLocaleString()}
          </span>
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="sm"
              disabled={offset === 0}
              onClick={() => onPageChange(Math.max(0, offset - limit))}
            >
              <ChevronLeft className="h-4 w-4" /> Prev
            </Button>
            <span className="px-3 py-1.5 tabular-nums">
              {currentPage} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={offset + limit >= totalCount}
              onClick={() => onPageChange(offset + limit)}
            >
              Next <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
