"use client";

import { HealthResponse } from "@/lib/types";

export function DataFreshnessFooter({ health }: { health: HealthResponse }) {
  return (
    <footer className="text-center text-xs text-muted-foreground py-4 border-t">
      {health.latest_data_date && (
        <span>Data as of {new Date(health.latest_data_date).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}</span>
      )}
      {health.stock_count && (
        <span> · {health.stock_count.toLocaleString()} stocks</span>
      )}
      {health.stale && (
        <span className="text-amber-600"> · Data may be stale — last sync was &gt;2 days ago</span>
      )}
    </footer>
  );
}
