"use client";

import { useEffect, useCallback } from "react";
import { PeerResponse } from "@/lib/types";
import { fmtLargeNumber, fmtPrice, fmtPercent, fmtMarketCap } from "@/lib/format";
import { DataTable, type Column } from "@/components/data-table";

interface Props {
  peers: PeerResponse | null;
  ticker: string;
  sector: string | null;
  onLoad: () => void;
}

const COLUMNS: Column[] = [
  { key: "ticker", label: "Ticker", linkable: true },
  { key: "company_name", label: "Company", linkable: true },
  { key: "current_price", label: "CMP (₹)" },
  { key: "market_cap_crore", label: "Market Cap" },
  { key: "pe_ratio", label: "P/E" },
  { key: "roe_pct", label: "ROE %" },
  { key: "revenue_growth_pct", label: "Rev Growth %" },
  { key: "debt_to_equity", label: "D/E" },
];

function formatPeerCell(key: string, value: string | number | null): string {
  if (value == null) return "—";
  if (key === "current_price") return fmtPrice(value as number);
  if (key === "market_cap_crore") return fmtMarketCap(value as number);
  if (key === "roe_pct" || key === "revenue_growth_pct") return fmtPercent(value as number);
  if (typeof value === "number") return fmtLargeNumber(value);
  return String(value);
}

export function PeerComparison({ peers, ticker, sector, onLoad }: Props) {
  useEffect(() => {
    if (!peers) onLoad();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const getRowHref = useCallback(
    (row: Record<string, any>) => `/company/${encodeURIComponent(row.ticker)}`,
    [],
  );

  if (!peers) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-8 bg-muted rounded animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">
        Peer Comparison{sector ? ` — ${sector}` : ""}
      </h2>

      {peers.peers.length === 0 ? (
        <p className="text-sm text-muted-foreground py-4">
          No direct peers {sector ? `in ${sector}` : "found"}.
        </p>
      ) : (
        <DataTable
          columns={COLUMNS}
          rows={peers.peers}
          loading={false}
          formatCell={formatPeerCell}
          getRowHref={getRowHref}
        />
      )}
    </div>
  );
}
