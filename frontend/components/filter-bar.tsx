"use client";

import { FilterSpec, FilterOptions } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { MultiSelect } from "@/components/ui/multi-select";
import { X } from "lucide-react";

interface Props {
  options: FilterOptions;
  filters: FilterSpec;
  onChange: (partial: Partial<FilterSpec>) => void;
  onClear: () => void;
}

export function FilterBar({ options, filters, onChange, onClear }: Props) {
  const hasFilters = Object.entries(filters).some(([k, v]) => {
    if (["sort_by", "sort_dir", "limit", "offset"].includes(k)) return false;
    if (Array.isArray(v)) return v.length > 0;
    return v !== undefined && v !== null && v !== "" && v !== false;
  });

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-3 items-end">
        <MultiSelect
          label="Sectors"
          options={options.sectors}
          selected={filters.sectors || []}
          onChange={(selected) => onChange({ sectors: selected.length > 0 ? selected : undefined })}
        />

        {/* P/E Range */}
        <RangeFilter
          label="P/E"
          minValue={filters.pe_min}
          maxValue={filters.pe_max}
          onMinChange={v => onChange({ pe_min: v || undefined })}
          onMaxChange={v => onChange({ pe_max: v || undefined })}
        />

        {/* ROE */}
        <RangeFilter
          label="ROE %"
          minValue={filters.roe_min}
          maxValue={undefined}
          onMinChange={v => onChange({ roe_min: v || undefined })}
          onMaxChange={() => {}}
        />

        {/* Market Cap */}
        <RangeFilter
          label="Market Cap (Cr)"
          minValue={filters.market_cap_min}
          maxValue={filters.market_cap_max}
          onMinChange={v => onChange({ market_cap_min: v || undefined })}
          onMaxChange={v => onChange({ market_cap_max: v || undefined })}
        />

        {/* Search */}
        <div className="flex flex-col gap-1 min-w-[160px]">
          <label className="text-xs font-medium text-muted-foreground">Company</label>
          <input
            type="text"
            placeholder="Search..."
            className="border rounded-md px-2 py-1.5 text-sm bg-background"
            value={filters.search || ""}
            onChange={e => onChange({ search: e.target.value || undefined })}
          />
        </div>

        {hasFilters && (
          <Button variant="outline" size="sm" onClick={onClear} className="gap-1">
            <X className="h-3 w-3" /> Clear All
          </Button>
        )}
      </div>
    </div>
  );
}

function RangeFilter({
  label,
  minValue,
  maxValue,
  onMinChange,
  onMaxChange,
}: {
  label: string;
  minValue?: number;
  maxValue?: number;
  onMinChange: (v: number | undefined) => void;
  onMaxChange: (v: number | undefined) => void;
}) {
  return (
    <div className="flex flex-col gap-1 min-w-[140px]">
      <label className="text-xs font-medium text-muted-foreground">{label}</label>
      <div className="flex gap-1 items-center">
        <input
          type="number"
          placeholder="Min"
          className="border rounded-md px-2 py-1.5 text-sm bg-background w-full"
          value={minValue ?? ""}
          onChange={e => onMinChange(e.target.value ? parseFloat(e.target.value) : undefined)}
        />
        <span className="text-muted-foreground text-xs">—</span>
        <input
          type="number"
          placeholder="Max"
          className="border rounded-md px-2 py-1.5 text-sm bg-background w-full"
          value={maxValue ?? ""}
          onChange={e => onMaxChange(e.target.value ? parseFloat(e.target.value) : undefined)}
        />
      </div>
    </div>
  );
}
