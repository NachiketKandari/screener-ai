"use client";

import { useEffect } from "react";
import Link from "next/link";
import { PeerResponse } from "@/lib/types";
import { fmtLargeNumber, fmtPrice, fmtPercent, fmtMarketCap } from "@/lib/format";

interface Props {
  peers: PeerResponse | null;
  ticker: string;
  sector: string | null;
  onLoad: () => void;
}

const COLUMNS = [
  { key: "ticker", label: "Ticker" },
  { key: "company_name", label: "Company" },
  { key: "current_price", label: "CMP (₹)" },
  { key: "market_cap_crore", label: "Market Cap" },
  { key: "pe_ratio", label: "P/E" },
  { key: "roe_pct", label: "ROE %" },
  { key: "revenue_growth_pct", label: "Rev Growth %" },
  { key: "debt_to_equity", label: "D/E" },
] as const;

type SortKey = typeof COLUMNS[number]["key"];

function formatPeerCell(key: SortKey, value: string | number | null): string {
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
        <div className="overflow-x-auto border rounded-lg">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-muted/50 border-b">
                {COLUMNS.map((col) => (
                  <th key={col.key} className="text-left px-4 py-2.5 font-medium text-muted-foreground whitespace-nowrap">
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {peers.peers.map((peer) => (
                <tr key={peer.ticker} className="border-b last:border-0 hover:bg-muted/30 transition-colors cursor-pointer"
                  onClick={() => window.location.href = `/company/${encodeURIComponent(peer.ticker)}`}>
                  {COLUMNS.map((col) => (
                    <td key={col.key} className={`px-4 py-2.5 whitespace-nowrap ${col.key === "ticker" || col.key === "company_name" ? "text-primary" : ""}`}>
                      {col.key === "ticker" || col.key === "company_name" ? (
                        <Link
                          href={`/company/${encodeURIComponent(peer.ticker)}`}
                          className="hover:underline"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {formatPeerCell(col.key, peer[col.key])}
                        </Link>
                      ) : (
                        formatPeerCell(col.key, peer[col.key])
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
