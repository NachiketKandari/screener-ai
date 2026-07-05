import { memo } from "react";
import * as Popover from "@radix-ui/react-popover";
import { Info } from "lucide-react";

interface Props {
  label: string;
  value: string;
  signal?: "green" | "red" | "neutral";
  description?: string;
}

export const MetricCard = memo(function MetricCard({ label, value, signal = "neutral", description }: Props) {
  return (
    <div className="bg-muted/30 border rounded-lg p-3">
      <div className="flex items-center gap-1.5">
        {signal !== "neutral" && (
          <span className={`h-2 w-2 rounded-full ${signal === "green" ? "bg-green-500" : "bg-red-500"}`} />
        )}
        <span className="text-xs text-muted-foreground uppercase tracking-wide">{label}</span>
        {description && (
          <Popover.Root>
            <Popover.Trigger asChild>
              <button
                type="button"
                className="inline-flex items-center justify-center rounded-full p-0.5 hover:bg-muted/80 transition-colors"
                aria-label={`What is ${label}?`}
                onClick={(e) => e.stopPropagation()}
              >
                <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground transition-colors" />
              </button>
            </Popover.Trigger>
            <Popover.Portal>
              <Popover.Content
                className="z-50 w-72 rounded-md border bg-background p-4 text-sm leading-relaxed shadow-lg"
                side="top"
                align="center"
                sideOffset={8}
                collisionPadding={12}
              >
                <p>{description}</p>
                <Popover.Arrow className="fill-border" />
              </Popover.Content>
            </Popover.Portal>
          </Popover.Root>
        )}
      </div>
      <div className="text-lg font-semibold tabular-nums mt-1">{value}</div>
    </div>
  );
});
