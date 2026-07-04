"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import { Plus, Search } from "lucide-react";
import { FILTER_REGISTRY, getMetricsByCategory, getMetric } from "@/lib/filter-registry";
import { FilterChipState } from "@/lib/types";

interface Props {
  activeChips: FilterChipState[];
  onAdd: (metricId: string) => void;
}

const CATEGORY_ORDER = [
  "Identity",
  "Valuation",
  "Profitability",
  "Growth",
  "Financial Health",
  "Ownership",
  "Price & Technical",
];

export function AddFilterDropdown({ activeChips, onAdd }: Props) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  const activeIds = new Set(activeChips.map((c) => c.metricId));

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setSearch("");
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const grouped = useMemo(() => {
    const byCategory = getMetricsByCategory();
    const result: { category: string; metrics: typeof FILTER_REGISTRY }[] = [];

    for (const cat of CATEGORY_ORDER) {
      const metrics = byCategory.get(cat);
      if (!metrics || metrics.length === 0) continue;

      if (search) {
        const filtered = metrics.filter(
          (m) =>
            m.label.toLowerCase().includes(search.toLowerCase()) ||
            m.shortLabel.toLowerCase().includes(search.toLowerCase()),
        );
        if (filtered.length > 0) {
          result.push({ category: cat, metrics: filtered });
        }
      } else {
        result.push({ category: cat, metrics });
      }
    }
    return result;
  }, [search]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 border border-dashed rounded-lg px-2.5 py-1 text-xs font-medium text-muted-foreground hover:text-foreground hover:border-foreground/30 transition-colors h-8"
      >
        <Plus className="h-3 w-3" />
        Add filter
      </button>

      {open && (
        <div className="absolute top-full mt-1 left-0 z-50 w-72 bg-background border rounded-lg shadow-lg overflow-hidden">
          {/* Search */}
          <div className="flex items-center gap-1.5 px-2.5 py-2 border-b sticky top-0 bg-background">
            <Search className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
            <input
              type="text"
              placeholder="Search metrics..."
              className="w-full text-sm bg-transparent outline-none"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />
          </div>

          {/* Metric list */}
          <div className="max-h-64 overflow-y-auto py-1">
            {grouped.length === 0 ? (
              <p className="px-3 py-3 text-xs text-muted-foreground text-center">
                No metrics found
              </p>
            ) : (
              grouped.map(({ category, metrics }) => (
                <div key={category}>
                  <div className="px-2.5 py-1 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider bg-muted/30">
                    {category}
                  </div>
                  {metrics.map((m) => {
                    const alreadyActive = activeIds.has(m.id);
                    return (
                      <button
                        key={m.id}
                        type="button"
                        disabled={alreadyActive}
                        className={`w-full text-left px-3 py-1.5 text-sm transition-colors flex items-center justify-between ${
                          alreadyActive
                            ? "text-muted-foreground/40 cursor-not-allowed"
                            : "hover:bg-muted cursor-pointer"
                        }`}
                        onClick={() => {
                          if (!alreadyActive) {
                            onAdd(m.id);
                            setOpen(false);
                            setSearch("");
                          }
                        }}
                      >
                        <span>{m.label}</span>
                        <span className="text-[10px] text-muted-foreground ml-2 shrink-0">
                          {m.unit || m.type === "boolean" ? (m.unit || "✓") : ""}
                        </span>
                      </button>
                    );
                  })}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
