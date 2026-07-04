"use client";

import { useState, useRef, useEffect } from "react";
import { X, ChevronDown, Search } from "lucide-react";
import { FilterChipState, FilterOperator, FilterOptions } from "@/lib/types";
import { getMetric } from "@/lib/filter-registry";

interface Props {
  chip: FilterChipState;
  options: FilterOptions;
  onChange: (id: string, updates: Partial<FilterChipState>) => void;
  onRemove: (id: string) => void;
}

const OP_LABELS: Record<FilterOperator, string> = {
  ">": ">",
  "<": "<",
  "=": "is",
  "!=": "≠",
  between: "between",
  contains: "contains",
};

export function FilterChip({ chip, options, onChange, onRemove }: Props) {
  const metric = getMetric(chip.metricId);
  if (!metric) return null;

  return (
    <div className="flex items-center gap-0.5 border rounded-lg bg-background px-1.5 py-1 text-sm shadow-sm">
      <span className="text-xs font-medium text-muted-foreground whitespace-nowrap px-1 select-none">
        {metric.shortLabel}
      </span>

      {/* Operator selector — visible for types with multiple operators */}
      {metric.operators.length > 1 && (
        <select
          className="text-xs bg-transparent border-0 px-0.5 py-0 focus:outline-none text-muted-foreground font-medium cursor-pointer"
          value={chip.operator}
          onChange={(e) =>
            onChange(chip.id, {
              operator: e.target.value as FilterOperator,
              valueEnd: e.target.value !== "between" ? undefined : chip.valueEnd,
            })
          }
        >
          {metric.operators.map((op) => (
            <option key={op} value={op}>
              {OP_LABELS[op]}
            </option>
          ))}
        </select>
      )}

      {/* Value input — type-dependent */}
      <FilterValue
        chip={chip}
        metric={metric}
        options={options}
        onChange={onChange}
      />

      {/* Unit */}
      {metric.unit && (
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {metric.unit}
        </span>
      )}

      {/* Remove */}
      <button
        type="button"
        onClick={() => onRemove(chip.id)}
        className="ml-0.5 p-0.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
        aria-label={`Remove ${metric.label} filter`}
      >
        <X className="h-3 w-3" />
      </button>
    </div>
  );
}

// ── Value input dispatcher ────────────────────────────────────────────

function FilterValue({
  chip,
  metric,
  options,
  onChange,
}: {
  chip: FilterChipState;
  metric: NonNullable<ReturnType<typeof getMetric>>;
  options: FilterOptions;
  onChange: (id: string, updates: Partial<FilterChipState>) => void;
}) {
  switch (metric.type) {
    case "enum_multi":
      return <EnumValue chip={chip} metric={metric} options={options} onChange={onChange} />;
    case "boolean":
      return <BooleanValue chip={chip} metric={metric} onChange={onChange} />;
    case "text":
      return <TextValue chip={chip} metric={metric} onChange={onChange} />;
    case "numeric_min":
    case "numeric_max":
      return <SingleNumberValue chip={chip} metric={metric} onChange={onChange} />;
    case "numeric_range":
      return <RangeValue chip={chip} metric={metric} onChange={onChange} />;
  }
}

// ── Enum (sectors, industries) — compact inline dropdown ─────────────

function EnumValue({
  chip,
  metric,
  options,
  onChange,
}: {
  chip: FilterChipState;
  metric: NonNullable<ReturnType<typeof getMetric>>;
  options: FilterOptions;
  onChange: (id: string, updates: Partial<FilterChipState>) => void;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  const enumOptions =
    metric.id === "sectors"
      ? options.sectors
      : metric.id === "industries"
        ? options.industries
        : [];

  const selected = chip.value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

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

  const filtered = enumOptions.filter((o) =>
    o.toLowerCase().includes(search.toLowerCase()),
  );

  const toggle = (val: string) => {
    const next = selected.includes(val)
      ? selected.filter((s) => s !== val)
      : [...selected, val];
    onChange(chip.id, { value: next.join(",") });
  };

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-sm px-1 py-0 hover:bg-muted/50 rounded min-w-[60px]"
      >
        <span className={selected.length > 0 ? "text-foreground" : "text-muted-foreground/50"}>
          {selected.length > 0
            ? `${selected.length} selected`
            : "Any"}
        </span>
        <ChevronDown className={`h-3 w-3 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="absolute top-full mt-1 left-0 z-50 w-56 bg-background border rounded-lg shadow-lg overflow-hidden">
          <div className="flex items-center gap-1 px-2 py-1.5 border-b">
            <Search className="h-3 w-3 text-muted-foreground shrink-0" />
            <input
              type="text"
              placeholder="Search..."
              className="w-full text-sm bg-transparent outline-none"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />
          </div>
          <div className="max-h-48 overflow-y-auto py-1">
            {filtered.length === 0 ? (
              <p className="px-3 py-2 text-xs text-muted-foreground">No results</p>
            ) : (
              filtered.map((option) => (
                <label
                  key={option}
                  className="flex items-center gap-2 px-3 py-1.5 hover:bg-muted cursor-pointer text-sm"
                >
                  <input
                    type="checkbox"
                    checked={selected.includes(option)}
                    onChange={() => toggle(option)}
                    className="rounded"
                  />
                  {option}
                </label>
              ))
            )}
          </div>
          {selected.length > 0 && (
            <div className="border-t px-2 py-1">
              <button
                type="button"
                onClick={() => onChange(chip.id, { value: "" })}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                Clear
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Boolean ───────────────────────────────────────────────────────────

function BooleanValue({
  chip,
  metric,
  onChange,
}: {
  chip: FilterChipState;
  metric: NonNullable<ReturnType<typeof getMetric>>;
  onChange: (id: string, updates: Partial<FilterChipState>) => void;
}) {
  return (
    <span
      className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 ml-1"
      title={`${metric.label} active`}
    />
  );
}

// ── Text ──────────────────────────────────────────────────────────────

function TextValue({
  chip,
  metric,
  onChange,
}: {
  chip: FilterChipState;
  metric: NonNullable<ReturnType<typeof getMetric>>;
  onChange: (id: string, updates: Partial<FilterChipState>) => void;
}) {
  return (
    <input
      type="text"
      placeholder={metric.placeholder || "Value..."}
      className="text-sm bg-transparent border-0 px-1 py-0 focus:outline-none min-w-[80px] w-auto placeholder:text-muted-foreground/50"
      value={chip.value}
      onChange={(e) => onChange(chip.id, { value: e.target.value })}
    />
  );
}

// ── Single number (min or max) ────────────────────────────────────────

function SingleNumberValue({
  chip,
  metric,
  onChange,
}: {
  chip: FilterChipState;
  metric: NonNullable<ReturnType<typeof getMetric>>;
  onChange: (id: string, updates: Partial<FilterChipState>) => void;
}) {
  return (
    <input
      type="number"
      placeholder={metric.placeholder || "Value"}
      className="text-sm bg-transparent border-0 px-1 py-0 focus:outline-none w-20 placeholder:text-muted-foreground/50"
      value={chip.value}
      onChange={(e) =>
        onChange(chip.id, {
          value: e.target.value,
        })
      }
      min={0}
      step="any"
    />
  );
}

// ── Range (min / max pair for numeric_range with "between") ───────────

function RangeValue({
  chip,
  metric,
  onChange,
}: {
  chip: FilterChipState;
  metric: NonNullable<ReturnType<typeof getMetric>>;
  onChange: (id: string, updates: Partial<FilterChipState>) => void;
}) {
  if (chip.operator === "between") {
    return (
      <span className="flex items-center gap-0.5">
        <input
          type="number"
          placeholder="Min"
          className="text-sm bg-transparent border-0 px-1 py-0 focus:outline-none w-20 placeholder:text-muted-foreground/50"
          value={chip.value}
          onChange={(e) => onChange(chip.id, { value: e.target.value })}
          min={0}
          step="any"
        />
        <span className="text-muted-foreground text-xs">—</span>
        <input
          type="number"
          placeholder="Max"
          className="text-sm bg-transparent border-0 px-1 py-0 focus:outline-none w-20 placeholder:text-muted-foreground/50"
          value={chip.valueEnd ?? ""}
          onChange={(e) => onChange(chip.id, { valueEnd: e.target.value })}
          min={0}
          step="any"
        />
      </span>
    );
  }

  // Single operator (">" or "<")
  return (
    <input
      type="number"
      placeholder={metric.placeholder || "Value"}
      className="text-sm bg-transparent border-0 px-1 py-0 focus:outline-none w-20 placeholder:text-muted-foreground/50"
      value={chip.value}
      onChange={(e) => onChange(chip.id, { value: e.target.value })}
      min={0}
      step="any"
    />
  );
}
