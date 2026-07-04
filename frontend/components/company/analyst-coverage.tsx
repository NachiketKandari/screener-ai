import { AnalystData, PriceData } from "@/lib/types";
import { fmtPrice } from "@/lib/format";

interface Props {
  analyst: AnalystData;
  price: PriceData;
}

export function AnalystCoverage({ analyst, price }: Props) {
  if (!analyst.number_of_analysts || analyst.number_of_analysts === 0) {
    return null;
  }

  const currentPrice = price.current;
  const targetMean = analyst.target_mean;
  const upside = currentPrice && targetMean
    ? ((targetMean - currentPrice) / currentPrice * 100)
    : null;

  const recColor = analyst.recommendation === "Buy" ? "bg-green-100 text-green-700"
    : analyst.recommendation === "Sell" ? "bg-red-100 text-red-700"
    : "bg-amber-100 text-amber-700";

  const low = analyst.target_low ?? 0;
  const high = analyst.target_high ?? 100;
  const range = high - low || 1;
  const markerPct = targetMean ? ((targetMean - low) / range) * 100 : 50;
  const pricePct = currentPrice && range > 0 ? ((currentPrice - low) / range) * 100 : 50;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Analyst Coverage</h2>

      <div className="flex flex-wrap items-center gap-3">
        {analyst.recommendation && (
          <span className={`px-2.5 py-1 rounded text-sm font-medium ${recColor}`}>
            {analyst.recommendation.toUpperCase()}
          </span>
        )}
        {analyst.number_of_analysts && (
          <span className="text-sm text-muted-foreground">
            Based on {analyst.number_of_analysts} analysts
          </span>
        )}
      </div>

      {targetMean && (
        <div className="space-y-2 max-w-lg">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Low: {fmtPrice(analyst.target_low)}</span>
            <span>Target: {fmtPrice(targetMean)}</span>
            <span>High: {fmtPrice(analyst.target_high)}</span>
          </div>
          <div className="relative h-2 bg-muted rounded-full">
            <div
              className="absolute top-0 h-full bg-primary/20 rounded-full"
              style={{ left: "0%", width: "100%" }}
            />
            {currentPrice && (
              <div
                className="absolute top-1/2 -translate-y-1/2 h-4 w-0.5 bg-foreground"
                style={{ left: `${Math.max(0, Math.min(100, pricePct))}%` }}
                title={`Current: ${fmtPrice(currentPrice)}`}
              />
            )}
            <div
              className="absolute top-1/2 -translate-y-1/2 h-3 w-3 bg-primary rounded-full border-2 border-background"
              style={{ left: `${Math.max(0, Math.min(100, markerPct))}%` }}
            />
          </div>
          {upside != null && (
            <p className={`text-sm font-medium ${upside > 0 ? "text-green-600" : "text-red-600"}`}>
              {upside > 0 ? "Upside" : "Downside"}: {upside > 0 ? "+" : ""}{upside.toFixed(1)}%
            </p>
          )}
        </div>
      )}
    </div>
  );
}
