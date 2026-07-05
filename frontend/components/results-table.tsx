"use client";

import { useMemo, useCallback } from "react";
import { DataTable, type Column } from "./data-table";
import { fmtPrice, fmtMarketCap, fmtPercent, fmtLargeNumber } from "@/lib/format";

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

const COLUMN_LABELS: Record<string, string> = {
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

function formatCell(key: string, value: any): string {
  if (value === null || value === undefined) return "—";
  const num = Number(value);
  if (isNaN(num)) return String(value);
  switch (key) {
    case "current_price":
      return fmtPrice(num);
    case "market_cap_crore":
      return fmtMarketCap(num);
    case "roe_pct":
    case "revenue_growth_pct":
    case "earnings_growth_pct":
    case "dividend_yield_pct":
      return fmtPercent(num);
    case "pe_ratio":
    case "pb_ratio":
    case "eps_ttm":
    case "debt_to_equity":
      return fmtLargeNumber(num);
    default:
      return fmtLargeNumber(num);
  }
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
  const columnDefs: Column[] = useMemo(
    () =>
      columns.map((col) => ({
        key: col,
        label: COLUMN_LABELS[col] || col.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        sortable: SORTABLE_COLUMNS.has(col),
        linkable: col === "ticker" || col === "company_name",
      })),
    [columns],
  );

  const mappedRows: Record<string, any>[] = useMemo(
    () =>
      rows.map((row) => {
        const obj: Record<string, any> = {};
        columns.forEach((col, i) => {
          obj[col] = row[i];
        });
        return obj;
      }),
    [rows, columns],
  );

  const getRowHref = useCallback(
    (row: Record<string, any>) => `/company/${encodeURIComponent(row.ticker)}`,
    [],
  );

  return (
    <DataTable
      columns={columnDefs}
      rows={mappedRows}
      loading={loading}
      emptyMessage="No stocks match your filters."
      emptyDetail="Try broadening your criteria."
      sortBy={sortBy}
      sortDir={sortDir}
      onSort={onSort}
      limit={limit}
      offset={offset}
      totalCount={totalCount}
      onPageChange={onPageChange}
      formatCell={formatCell}
      getRowHref={getRowHref}
    />
  );
}
