# Advanced Filter Builder — Implementation Plan

## Context

The stock screener has **54 metrics** in the database and **24 filterable fields** in the backend (`FilterSpec`), but only **5 are exposed** in the UI: Sectors dropdown, P/E range, ROE min, Market Cap range, and Company search. The user wants access to all 24 filterable metrics through a modern filter-builder pattern similar to Airtable/Notion, where metrics are clickable chips that build up a query visually.

The natural language "Ask AI" input stays as an alternative entry mode. The sort ascending/descending needs to work correctly and be verified.

## What Changes

### Files to create:
- `frontend/lib/filter-registry.ts` — catalog of all 24 filterable metrics with metadata
- `frontend/components/filter-chip.tsx` — single filter pill (metric + operator + value + remove)
- `frontend/components/add-filter-dropdown.tsx` — searchable categorized popover to add new chips

### Files to modify:
- `frontend/lib/types.ts` — add `FilterChipState`, `FilterMetricDef`, `FilterOperator`, etc.
- `frontend/components/filter-bar.tsx` — replace hardcoded controls with dynamic chip rendering

### No changes:
- `frontend/app/page.tsx` — FilterBar contract (`options`, `filters`, `onChange`, `onClear`) stays identical
- All backend files — already handle all 24 FilterSpec fields
- `NaturalLanguageInput` component — unchanged, stays as-is

---

## Step 1: Extend `frontend/lib/types.ts`

Add these types:

```ts
export type FilterOperator = ">" | "<" | "=" | "!=" | "between" | "contains";

export type FilterFieldType =
  | "numeric_range"    // has _min + _max (pe_min/pe_max)
  | "numeric_min"      // only _min (roe_min)
  | "numeric_max"      // only _max (debt_to_equity_max)
  | "enum_multi"       // string[] (sectors, industries)
  | "boolean"          // toggle (price_above_50dma)
  | "text";            // free-text (search, ticker)

export type FilterCategory =
  | "Identity" | "Valuation" | "Profitability" | "Growth"
  | "Financial Health" | "Ownership" | "Price & Technical";

export interface FilterMetricDef {
  id: string;
  label: string;
  shortLabel: string;
  type: FilterFieldType;
  unit: string;           // "%", " Cr", "₹", "x", ""
  category: FilterCategory;
  operators: FilterOperator[];
  defaultOperator: FilterOperator;
  primaryField: keyof FilterSpec;     // maps to FilterSpec field
  secondaryField?: keyof FilterSpec;  // paired field for "between"
  placeholder?: string;
}

export interface FilterChipState {
  id: string;            // unique instance id
  metricId: string;      // references FilterMetricDef.id
  operator: FilterOperator;
  value: string;         // primary value (serialized to number/string/bool)
  valueEnd?: string;     // secondary value for "between"
}
```

---

## Step 2: Create `frontend/lib/filter-registry.ts`

**24 metrics** organized by category, each mapping to FilterSpec fields:

| metricId | shortLabel | type | primaryField | secondaryField | unit |
|----------|------------|------|--------------|----------------|------|
| sectors | Sector | enum_multi | sectors | -- | -- |
| industries | Industry | enum_multi | industries | -- | -- |
| ticker | Ticker | text | ticker | -- | -- |
| search | Company | text | search | -- | -- |
| pe_ratio | P/E | numeric_range | pe_min | pe_max | -- |
| market_cap_crore | Mkt Cap | numeric_range | market_cap_min | market_cap_max | Cr |
| pb_ratio | P/B | numeric_range | pb_min | pb_max | -- |
| peg_ratio | PEG | numeric_max | peg_max | -- | -- |
| price_to_sales | P/S | numeric_max | price_to_sales_max | -- | -- |
| roe_pct | ROE | numeric_min | roe_min | -- | % |
| roa_pct | ROA | numeric_min | roa_min | -- | % |
| profit_margins_pct | Profit Margin | numeric_min | profit_margin_min | -- | % |
| operating_margins_pct | Op. Margin | numeric_min | operating_margin_min | -- | % |
| revenue_growth_pct | Rev Growth | numeric_min | revenue_growth_min | -- | % |
| earnings_growth_pct | Earn Growth | numeric_min | earnings_growth_min | -- | % |
| debt_to_equity | D/E | numeric_max | debt_to_equity_max | -- | -- |
| current_ratio | Cur. Ratio | numeric_min | current_ratio_min | -- | -- |
| dividend_yield_pct | Div Yield | numeric_min | dividend_yield_min | -- | % |
| promoter_holding | Promoter % | numeric_min | promoter_holding_min | -- | % |
| pct_52w_high | % Below 52W H | numeric_max | price_pct_from_52w_high_max | -- | % |
| pct_52w_low | % Above 52W L | numeric_min | price_pct_from_52w_low_min | -- | % |
| above_50dma | >50 DMA | boolean | price_above_50dma | -- | -- |
| above_200dma | >200 DMA | boolean | price_above_200dma | -- | -- |
| vol_gt_20d_avg | Vol >20D Avg | boolean | volume_above_20d_avg | -- | -- |

Export two functions:
- `serializeChipsToFilterSpec(chips, registry)` — converts chip array to `Partial<FilterSpec>`
- `createEmptyChip(metricId, registry)` — creates a new chip with default operator and empty value

Default visible chips on load: `sectors`, `pe_ratio`, `roe_pct`, `market_cap_crore`, `search`.

---

## Step 3: Create `frontend/components/filter-chip.tsx`

A pill-shaped control rendering one active filter. Layout:

```
┌──────────────────────────────────────────────────────────┐
│ [Metric Label]  [Op ▼]  [ Value input(s) ]  [unit]  [×] │
└──────────────────────────────────────────────────────────┘
```

Rendering by type:
- **numeric_min/max**: Locked operator text + number input + unit
- **numeric_range (> / <)**: Operator dropdown + number input + unit
- **numeric_range (between)**: Two number inputs separated by "—"
- **enum_multi**: Operator (= / !=) + MultiSelect dropdown
- **boolean**: Label + colored indicator dot, no inputs (remove to deactivate)
- **text**: Operator (contains/=) + text input

When operator changes, clear valueEnd unless switching to "between".

---

## Step 4: Create `frontend/components/add-filter-dropdown.tsx`

Uses `@radix-ui/react-popover` (already in dependencies). Trigger: "+ Add filter" button (outline, sm).

Popover content:
- Sticky search bar at top
- Metrics grouped by category (Valuation, Profitability, Growth, etc.)
- Already-active metrics shown as disabled/muted
- Click a metric → calls onAdd(metricId) → closes popover
- Category headers hidden if no results in that category after search

---

## Step 5: Refactor `frontend/components/filter-bar.tsx`

Replace all hardcoded controls with dynamic chip rendering:

- Internal state: `FilterChipState[]` initialized with 5 default metrics
- `dispatchAndSync(action)` — applies reducer then synchronously calls `onChange(serializedSpec)`
- Render loop: map chips → `<FilterChip>` + `<AddFilterDropdown>` at the end
- "Clear All" resets chips to defaults and calls parent's `onClear()`
- Active chips not yet filled in render but don't contribute to FilterSpec (graceful)

No stale closure issues — use `chipsRef` for synchronous reads during dispatch.

---

## Step 6: Verify sort ascending/descending

Current SummaryBar has a sort dropdown with hardcoded options. Need to verify:
1. Changing sort triggers `onSortChange(sort_by, sort_dir)` → parent's `updateFilters` → API call
2. The API respects `sort_by` and `sort_dir` (already verified — tested in audit)
3. Column headers in ResultsTable should also be clickable for sort (client-side for current page, API refetch for full dataset)

Fix: Add `cursor-pointer select-none` to table headers and wire `onClick` to toggle sort on that column. Clicking a column header:
- If not current sort column → set as sort column (asc for first click)
- If current sort column → toggle asc/desc

---

## Step 7: Verification

1. **Frontend compiles**: `npm run build` or check dev server recompiles
2. **All 24 metrics appear** in AddFilterDropdown, searchable, grouped by category
3. **Default 5 chips** visible on load: Sector, P/E, ROE, Mkt Cap, Company
4. **Add a filter**: click "+ Add filter" → select "P/B Ratio" → chip appears → enter value → API call fires with `pb_min` or `pb_max`
5. **Remove a filter**: click × on chip → chip removed → API refires without that filter
6. **Clear all**: reset to default 5 chips, refetch with DEFAULT_FILTERS
7. **Sort**: click column headers to sort, dropdown changes sort, API re-fetches correctly
8. **NL input** still works alongside chips — type query → Ask AI → results replace table
9. **No regressions**: existing 103 tests still pass

## Edge Cases Handled

- Duplicate metric prevented (except enum_multi)
- Invalid number input silently skipped in serialization
- Empty value chip doesn't contribute to query
- "between" min > max swapped automatically in serialization
- Operator change clears valueEnd when not "between"
