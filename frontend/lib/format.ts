const CRORE = 10_000_000;

export function fmtPrice(value: number | null | undefined): string {
  if (value == null) return "—";
  return "₹" + value.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function fmtLargeNumber(value: number | null | undefined, decimals: number = 2): string {
  if (value == null) return "—";
  return value.toLocaleString("en-IN", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

export function fmtPercent(value: number | null | undefined): string {
  if (value == null) return "—";
  const sign = value > 0 ? "+" : "";
  return sign + value.toFixed(1) + "%";
}

export function fmtMarketCap(crore: number | null | undefined): string {
  if (crore == null) return "—";
  if (crore >= 1_00_000) return "₹" + (crore / 1_00_000).toFixed(1) + "L Cr";
  return "₹" + fmtLargeNumber(crore, 0) + " Cr";
}

export function fmtVolume(volume: number | null | undefined): string {
  if (volume == null) return "—";
  if (volume >= 1_000_000) return (volume / 1_000_000).toFixed(1) + "M";
  if (volume >= 1_000) return (volume / 1_000).toFixed(1) + "K";
  return String(volume);
}

export function fmtChangePct(value: number | null | undefined): { text: string; isPositive: boolean; isNegative: boolean } {
  if (value == null) return { text: "—", isPositive: false, isNegative: false };
  const sign = value > 0 ? "+" : "";
  return { text: sign + value.toFixed(2) + "%", isPositive: value > 0, isNegative: value < 0 };
}

export function fmtValue(value: number | null | undefined, unit: string): string {
  if (value == null) return "—";
  return fmtLargeNumber(value) + (unit ? " " + unit : "");
}

export function colorSignal(value: number | null | undefined, thresholds: { green?: number; red?: number }): "green" | "red" | "neutral" {
  if (value == null) return "neutral";
  if (thresholds.green !== undefined && value >= thresholds.green) return "green";
  if (thresholds.red !== undefined && value <= thresholds.red) return "red";
  return "neutral";
}
