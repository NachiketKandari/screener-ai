import {
  FilterChipState,
  FilterMetricDef,
  FilterOperator,
  FilterSpec,
} from "@/lib/types";

let _chipCounter = 0;

export function nextChipId(): string {
  _chipCounter += 1;
  return `chip_${_chipCounter}`;
}

// ── Registry ──────────────────────────────────────────────────────────

export const FILTER_REGISTRY: FilterMetricDef[] = [
  // ── Identity ────────────────────────────────────────────────────────
  {
    id: "sectors",
    label: "Sector",
    shortLabel: "Sector",
    type: "enum_multi",
    unit: "",
    category: "Identity",
    operators: ["="],
    defaultOperator: "=",
    primaryField: "sectors",
  },
  {
    id: "industries",
    label: "Industry",
    shortLabel: "Industry",
    type: "enum_multi",
    unit: "",
    category: "Identity",
    operators: ["="],
    defaultOperator: "=",
    primaryField: "industries",
  },
  {
    id: "ticker",
    label: "Ticker",
    shortLabel: "Ticker",
    type: "text",
    unit: "",
    category: "Identity",
    operators: ["="],
    defaultOperator: "=",
    primaryField: "ticker",
  },
  {
    id: "search",
    label: "Company",
    shortLabel: "Company",
    type: "text",
    unit: "",
    category: "Identity",
    operators: ["contains"],
    defaultOperator: "contains",
    primaryField: "search",
    placeholder: "Search by name...",
  },

  // ── Valuation ───────────────────────────────────────────────────────
  {
    id: "pe_ratio",
    label: "P/E Ratio",
    shortLabel: "P/E",
    type: "numeric_range",
    unit: "",
    category: "Valuation",
    operators: [">", "<", "between"],
    defaultOperator: "between",
    primaryField: "pe_min",
    secondaryField: "pe_max",
  },
  {
    id: "market_cap_crore",
    label: "Market Cap",
    shortLabel: "Mkt Cap",
    type: "numeric_range",
    unit: "Cr",
    category: "Valuation",
    operators: [">", "<", "between"],
    defaultOperator: "between",
    primaryField: "market_cap_min",
    secondaryField: "market_cap_max",
  },
  {
    id: "pb_ratio",
    label: "P/B Ratio",
    shortLabel: "P/B",
    type: "numeric_range",
    unit: "",
    category: "Valuation",
    operators: [">", "<", "between"],
    defaultOperator: "between",
    primaryField: "pb_min",
    secondaryField: "pb_max",
  },
  {
    id: "peg_ratio",
    label: "PEG Ratio",
    shortLabel: "PEG",
    type: "numeric_max",
    unit: "",
    category: "Valuation",
    operators: ["<"],
    defaultOperator: "<",
    primaryField: "peg_max",
    placeholder: "Max PEG",
  },
  {
    id: "price_to_sales",
    label: "Price / Sales",
    shortLabel: "P/S",
    type: "numeric_max",
    unit: "",
    category: "Valuation",
    operators: ["<"],
    defaultOperator: "<",
    primaryField: "price_to_sales_max",
    placeholder: "Max P/S",
  },

  // ── Profitability ───────────────────────────────────────────────────
  {
    id: "roe_pct",
    label: "ROE",
    shortLabel: "ROE",
    type: "numeric_min",
    unit: "%",
    category: "Profitability",
    operators: [">"],
    defaultOperator: ">",
    primaryField: "roe_min",
    placeholder: "Min ROE %",
  },
  {
    id: "roa_pct",
    label: "ROA",
    shortLabel: "ROA",
    type: "numeric_min",
    unit: "%",
    category: "Profitability",
    operators: [">"],
    defaultOperator: ">",
    primaryField: "roa_min",
    placeholder: "Min ROA %",
  },
  {
    id: "profit_margins_pct",
    label: "Profit Margin",
    shortLabel: "Profit Margin",
    type: "numeric_min",
    unit: "%",
    category: "Profitability",
    operators: [">"],
    defaultOperator: ">",
    primaryField: "profit_margin_min",
    placeholder: "Min margin %",
  },
  {
    id: "operating_margins_pct",
    label: "Operating Margin",
    shortLabel: "Op. Margin",
    type: "numeric_min",
    unit: "%",
    category: "Profitability",
    operators: [">"],
    defaultOperator: ">",
    primaryField: "operating_margin_min",
    placeholder: "Min op. margin %",
  },

  // ── Growth ──────────────────────────────────────────────────────────
  {
    id: "revenue_growth_pct",
    label: "Revenue Growth",
    shortLabel: "Rev Growth",
    type: "numeric_min",
    unit: "%",
    category: "Growth",
    operators: [">"],
    defaultOperator: ">",
    primaryField: "revenue_growth_min",
    placeholder: "Min rev. growth %",
  },
  {
    id: "earnings_growth_pct",
    label: "Earnings Growth",
    shortLabel: "Earn Growth",
    type: "numeric_min",
    unit: "%",
    category: "Growth",
    operators: [">"],
    defaultOperator: ">",
    primaryField: "earnings_growth_min",
    placeholder: "Min earn. growth %",
  },

  // ── Financial Health ────────────────────────────────────────────────
  {
    id: "debt_to_equity",
    label: "Debt / Equity",
    shortLabel: "D/E",
    type: "numeric_max",
    unit: "",
    category: "Financial Health",
    operators: ["<"],
    defaultOperator: "<",
    primaryField: "debt_to_equity_max",
    placeholder: "Max D/E",
  },
  {
    id: "current_ratio",
    label: "Current Ratio",
    shortLabel: "Cur. Ratio",
    type: "numeric_min",
    unit: "",
    category: "Financial Health",
    operators: [">"],
    defaultOperator: ">",
    primaryField: "current_ratio_min",
    placeholder: "Min ratio",
  },
  {
    id: "dividend_yield_pct",
    label: "Dividend Yield",
    shortLabel: "Div Yield",
    type: "numeric_min",
    unit: "%",
    category: "Financial Health",
    operators: [">"],
    defaultOperator: ">",
    primaryField: "dividend_yield_min",
    placeholder: "Min yield %",
  },

  // ── Ownership ───────────────────────────────────────────────────────
  {
    id: "promoter_holding",
    label: "Promoter Holding",
    shortLabel: "Promoter %",
    type: "numeric_min",
    unit: "%",
    category: "Ownership",
    operators: [">"],
    defaultOperator: ">",
    primaryField: "promoter_holding_min",
    placeholder: "Min promoter %",
  },

  // ── Price & Technical ───────────────────────────────────────────────
  {
    id: "pct_52w_high",
    label: "% Below 52W High",
    shortLabel: "% Below 52W H",
    type: "numeric_max",
    unit: "%",
    category: "Price & Technical",
    operators: ["<"],
    defaultOperator: "<",
    primaryField: "price_pct_from_52w_high_max",
    placeholder: "Max % below high",
  },
  {
    id: "pct_52w_low",
    label: "% Above 52W Low",
    shortLabel: "% Above 52W L",
    type: "numeric_min",
    unit: "%",
    category: "Price & Technical",
    operators: [">"],
    defaultOperator: ">",
    primaryField: "price_pct_from_52w_low_min",
    placeholder: "Min % above low",
  },
  {
    id: "above_50dma",
    label: "Price Above 50 DMA",
    shortLabel: ">50 DMA",
    type: "boolean",
    unit: "",
    category: "Price & Technical",
    operators: ["="],
    defaultOperator: "=",
    primaryField: "price_above_50dma",
  },
  {
    id: "above_200dma",
    label: "Price Above 200 DMA",
    shortLabel: ">200 DMA",
    type: "boolean",
    unit: "",
    category: "Price & Technical",
    operators: ["="],
    defaultOperator: "=",
    primaryField: "price_above_200dma",
  },
  {
    id: "vol_gt_20d_avg",
    label: "Volume > 20D Avg",
    shortLabel: "Vol >20D Avg",
    type: "boolean",
    unit: "",
    category: "Price & Technical",
    operators: ["="],
    defaultOperator: "=",
    primaryField: "volume_above_20d_avg",
  },
];

// ── Lookup helpers ────────────────────────────────────────────────────

export function getMetric(id: string): FilterMetricDef | undefined {
  return FILTER_REGISTRY.find((m) => m.id === id);
}

export function getMetricsByCategory(): Map<string, FilterMetricDef[]> {
  const map = new Map<string, FilterMetricDef[]>();
  for (const m of FILTER_REGISTRY) {
    const list = map.get(m.category) || [];
    list.push(m);
    map.set(m.category, list);
  }
  return map;
}

// ── Default visible chips ─────────────────────────────────────────────

export const DEFAULT_METRIC_IDS = [
  "sectors",
  "pe_ratio",
  "roe_pct",
  "market_cap_crore",
  "search",
];

// ── Serialization ─────────────────────────────────────────────────────

function toNum(v: string): number | undefined {
  const n = parseFloat(v);
  if (isNaN(n) || !isFinite(n)) return undefined;
  return n;
}

export function serializeChipsToFilterSpec(
  chips: FilterChipState[],
): Partial<FilterSpec> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const spec: Record<string, any> = {};

  for (const chip of chips) {
    const metric = getMetric(chip.metricId);
    if (!metric) continue;

    switch (metric.type) {
      case "numeric_range": {
        const op = chip.operator;
        if (op === "between") {
          const lo = toNum(chip.value);
          const hi = toNum(chip.valueEnd ?? "");
          if (lo !== undefined && hi !== undefined) {
            const min = Math.min(lo, hi);
            const max = Math.max(lo, hi);
            spec[metric.primaryField] = min;
            if (metric.secondaryField) spec[metric.secondaryField] = max;
          }
        } else if (op === ">") {
          const n = toNum(chip.value);
          if (n !== undefined) spec[metric.primaryField] = n;
        } else if (op === "<") {
          const n = toNum(chip.value);
          if (n !== undefined) {
            const target = metric.secondaryField ?? metric.primaryField;
            spec[target] = n;
          }
        }
        break;
      }

      case "numeric_min": {
        const n = toNum(chip.value);
        if (n !== undefined) spec[metric.primaryField] = n;
        break;
      }

      case "numeric_max": {
        const n = toNum(chip.value);
        if (n !== undefined) spec[metric.primaryField] = n;
        break;
      }

      case "enum_multi": {
        const values = chip.value
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
        if (values.length > 0) {
          spec[metric.primaryField] = values;
        }
        break;
      }

      case "text": {
        if (chip.value.trim()) {
          spec[metric.primaryField] = chip.value.trim();
        }
        break;
      }

      case "boolean": {
        spec[metric.primaryField] = true;
        break;
      }
    }
  }

  return spec as Partial<FilterSpec>;
}

export function createEmptyChip(metricId: string): FilterChipState | null {
  const metric = getMetric(metricId);
  if (!metric) return null;

  return {
    id: nextChipId(),
    metricId,
    operator: metric.defaultOperator,
    value: "",
    valueEnd: undefined,
  };
}
