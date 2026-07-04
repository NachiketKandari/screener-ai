"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { ChartResponse } from "@/lib/types";

const RANGES = [
  { value: "1mo", label: "1M" },
  { value: "6mo", label: "6M" },
  { value: "1y", label: "1Y" },
  { value: "3y", label: "3Y" },
  { value: "5y", label: "5Y" },
  { value: "max", label: "MAX" },
];

interface Props {
  chart: ChartResponse | null;
  ticker: string;
  onRangeChange: (range: string) => void;
  onLoad: () => void;
  expanded?: boolean;
}

export function CompanyChart({ chart, ticker, onRangeChange, onLoad, expanded }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [range, setRange] = useState("1y");
  const [chartType, setChartType] = useState<"line" | "candlestick">("line");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    onLoad();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleRangeChange = useCallback((newRange: string) => {
    setRange(newRange);
    setError(null);
    onRangeChange(newRange);
  }, [onRangeChange]);

  useEffect(() => {
    if (!chart || !containerRef.current) return;

    const loadChart = async () => {
      const { createChart, ColorType, LineSeries, CandlestickSeries } = await import("lightweight-charts");
      const el = containerRef.current;
      if (!el) return;

      el.innerHTML = "";

      const chartInstance = createChart(el, {
        layout: {
          background: { type: ColorType.Solid, color: "transparent" },
          textColor: "#64748b",
        },
        grid: {
          vertLines: { color: "#f1f5f9" },
          horzLines: { color: "#f1f5f9" },
        },
        crosshair: { mode: 0 },
        rightPriceScale: { borderColor: "#e2e8f0" },
        timeScale: { borderColor: "#e2e8f0" },
        width: el.clientWidth,
        height: expanded ? 500 : 350,
      });

      const series = chartType === "line"
        ? chartInstance.addSeries(LineSeries, {
            color: "#2563eb",
            lineWidth: 2,
            priceFormat: { type: "price", precision: 2, minMove: 0.01 },
          })
        : chartInstance.addSeries(CandlestickSeries, {
            upColor: "#16a34a",
            downColor: "#dc2626",
            borderUpColor: "#16a34a",
            borderDownColor: "#dc2626",
            wickUpColor: "#16a34a",
            wickDownColor: "#dc2626",
          });

      if (chartType === "line") {
        series.setData(
          chart.data
            .filter((d) => d.close != null)
            .map((d) => ({ time: d.date, value: d.close! }))
        );
      } else {
        series.setData(
          chart.data
            .filter((d) => d.open != null && d.high != null && d.low != null && d.close != null)
            .map((d) => ({
              time: d.date,
              open: d.open!,
              high: d.high!,
              low: d.low!,
              close: d.close!,
            }))
        );
      }

      chartInstance.timeScale().fitContent();
      chartInstance.timeScale().applyOptions({
        fixLeftEdge: true,
        fixRightEdge: true,
      });

      const handleResize = () => {
        chartInstance.applyOptions({ width: el.clientWidth });
      };
      window.addEventListener("resize", handleResize);

      return () => {
        window.removeEventListener("resize", handleResize);
        chartInstance.remove();
      };
    };

    loadChart().catch((err) => {
      setError("Failed to load chart");
      console.error(err);
    });
  }, [chart, chartType, expanded]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex gap-1">
          {RANGES.map((r) => (
            <button
              key={r.value}
              onClick={() => handleRangeChange(r.value)}
              className={`px-2.5 py-1 text-xs font-medium rounded border transition-colors ${
                range === r.value
                  ? "bg-primary text-primary-foreground border-primary"
                  : "border-muted hover:bg-muted"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
        <div className="flex gap-1">
          {(["line", "candlestick"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setChartType(t)}
              className={`px-2.5 py-1 text-xs font-medium rounded border transition-colors capitalize ${
                chartType === t
                  ? "bg-primary text-primary-foreground border-primary"
                  : "border-muted hover:bg-muted"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="text-sm text-destructive py-4 text-center">
          {error} <button onClick={() => onRangeChange(range)} className="text-primary hover:underline ml-1">Retry</button>
        </div>
      )}

      {!chart && !error && (
        <div className="h-[350px] bg-muted rounded-lg animate-pulse" />
      )}

      {chart && chart.data.length === 0 && (
        <div className="text-sm text-muted-foreground py-12 text-center">
          No price data available for {ticker}.
        </div>
      )}

      <div ref={containerRef} className="w-full" />
    </div>
  );
}
