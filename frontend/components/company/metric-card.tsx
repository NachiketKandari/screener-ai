import { colorSignal } from "@/lib/format";

interface Props {
  label: string;
  value: string;
  signal?: "green" | "red" | "neutral";
}

export function MetricCard({ label, value, signal = "neutral" }: Props) {
  return (
    <div className="bg-muted/30 border rounded-lg p-3">
      <div className="flex items-center gap-1.5">
        {signal !== "neutral" && (
          <span className={`h-2 w-2 rounded-full ${signal === "green" ? "bg-green-500" : "bg-red-500"}`} />
        )}
        <span className="text-xs text-muted-foreground uppercase tracking-wide">{label}</span>
      </div>
      <div className="text-lg font-semibold tabular-nums mt-1">{value}</div>
    </div>
  );
}
