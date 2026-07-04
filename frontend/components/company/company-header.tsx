import { CompanyResponse } from "@/lib/types";
import { fmtPrice, fmtChangePct, fmtVolume } from "@/lib/format";
import { TrendingUp, TrendingDown } from "lucide-react";

const EXCHANGE_LABELS: Record<string, string> = {
  NSI: "NSE",
  BSE: "BSE",
};

function exchangeLabel(code: string): string {
  return EXCHANGE_LABELS[code] || code;
}

export function CompanyHeader({ company }: { company: CompanyResponse }) {
  const { price } = company;
  const changeInfo = fmtChangePct(price.change_pct);
  const isUp = changeInfo.isPositive;
  const isDown = changeInfo.isNegative;
  const Arrow = isUp ? TrendingUp : isDown ? TrendingDown : null;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h1 className="text-2xl font-bold">{company.company_name || company.ticker}</h1>
        <span className="text-sm text-muted-foreground font-mono bg-muted px-2 py-0.5 rounded">
          {company.ticker}
        </span>
        {company.exchange && (
          <span className="text-xs text-muted-foreground border px-1.5 py-0.5 rounded">
            {exchangeLabel(company.exchange)}
          </span>
        )}
        {company.sector && (
          <span className="text-xs text-muted-foreground border px-1.5 py-0.5 rounded">
            {company.sector}
          </span>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
        {price.current != null ? (
          <>
            <span className="text-3xl font-bold tabular-nums">{fmtPrice(price.current)}</span>
            <span className={`inline-flex items-center gap-1 font-medium ${isUp ? "text-green-600" : isDown ? "text-red-600" : "text-muted-foreground"}`}>
              {Arrow && <Arrow className="h-4 w-4" />}
              {price.change != null ? (price.change > 0 ? "+" : "") + price.change.toFixed(2) : "—"}
            </span>
            <span className={`font-medium ${isUp ? "text-green-600" : isDown ? "text-red-600" : "text-muted-foreground"}`}>
              ({changeInfo.text})
            </span>
          </>
        ) : (
          <span className="text-muted-foreground">Price unavailable</span>
        )}
        {price.volume_today != null && (
          <span className="text-muted-foreground">
            Vol: {fmtVolume(price.volume_today)}
          </span>
        )}
        {company.as_of_date && (
          <span className="text-muted-foreground">
            {new Date(company.as_of_date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
          </span>
        )}
      </div>
    </div>
  );
}
