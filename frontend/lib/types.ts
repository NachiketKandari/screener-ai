export interface FilterSpec {
  sectors?: string[];
  industries?: string[];
  ticker?: string;
  search?: string;
  pe_min?: number;
  pe_max?: number;
  market_cap_min?: number;
  market_cap_max?: number;
  pb_min?: number;
  pb_max?: number;
  peg_max?: number;
  price_to_sales_max?: number;
  roe_min?: number;
  roa_min?: number;
  profit_margin_min?: number;
  operating_margin_min?: number;
  revenue_growth_min?: number;
  earnings_growth_min?: number;
  debt_to_equity_max?: number;
  current_ratio_min?: number;
  dividend_yield_min?: number;
  promoter_holding_min?: number;
  price_pct_from_52w_high_max?: number;
  price_pct_from_52w_low_min?: number;
  price_above_50dma?: boolean;
  price_above_200dma?: boolean;
  volume_above_20d_avg?: boolean;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

export interface ScreenResponse {
  columns: string[];
  rows: (string | number | null)[][];
  total_count: number;
  query_time_ms: number;
  warnings: string[];
}

export interface FilterOptions {
  sectors: string[];
  industries: string[];
  sort_columns: { value: string; label: string }[];
}

export interface HealthResponse {
  status: string;
  latest_data_date: string | null;
  stock_count: number | null;
  db_size_mb: number | null;
  stale: boolean;
}

// ── Filter Builder types ─────────────────────────────────────────────

export type FilterOperator = ">" | "<" | "=" | "!=" | "between" | "contains";

export type FilterFieldType =
  | "numeric_range"
  | "numeric_min"
  | "numeric_max"
  | "enum_multi"
  | "boolean"
  | "text";

export type FilterCategory =
  | "Identity"
  | "Valuation"
  | "Profitability"
  | "Growth"
  | "Financial Health"
  | "Ownership"
  | "Price & Technical";

export interface FilterMetricDef {
  id: string;
  label: string;
  shortLabel: string;
  type: FilterFieldType;
  unit: string;
  category: FilterCategory;
  operators: FilterOperator[];
  defaultOperator: FilterOperator;
  primaryField: keyof FilterSpec;
  secondaryField?: keyof FilterSpec;
  placeholder?: string;
}

export interface FilterChipState {
  id: string;
  metricId: string;
  operator: FilterOperator;
  value: string;
  valueEnd?: string;
}

// ── Company Detail types ────────────────────────────────────────────────

export interface PriceData {
  current: number | null;
  change: number | null;
  change_pct: number | null;
  prev_close: number | null;
  open: number | null;
  high: number | null;
  low: number | null;
  high_52w: number | null;
  low_52w: number | null;
  volume_today: number | null;
}

export interface ValuationData {
  market_cap_crore: number | null;
  pe_ratio: number | null;
  forward_pe: number | null;
  pb_ratio: number | null;
  peg_ratio: number | null;
  price_to_sales: number | null;
  eps_ttm: number | null;
  eps_forward: number | null;
  book_value_per_share: number | null;
}

export interface ProfitabilityData {
  roe_pct: number | null;
  roa_pct: number | null;
  profit_margins_pct: number | null;
  operating_margins_pct: number | null;
  gross_margins_pct: number | null;
  ebitda_margins_pct: number | null;
}

export interface GrowthData {
  revenue_growth_pct: number | null;
  earnings_growth_pct: number | null;
  earnings_quarterly_growth_pct: number | null;
}

export interface FinancialHealthData {
  debt_to_equity: number | null;
  current_ratio: number | null;
  quick_ratio: number | null;
  payout_ratio: number | null;
  dividend_yield_pct: number | null;
  five_year_avg_dividend_yield_pct: number | null;
  free_cashflow: number | null;
  operating_cashflow: number | null;
  total_debt: number | null;
  total_revenue: number | null;
  ebitda: number | null;
  total_cash_per_share: number | null;
}

export interface OwnershipData {
  promoter_pct: number | null;
  institutional_pct: number | null;
  public_pct: number | null;
}

export interface TechnicalsData {
  beta: number | null;
  price_pct_from_52w_high: number | null;
  price_pct_from_52w_low: number | null;
}

export interface AnalystData {
  recommendation: string | null;
  number_of_analysts: number | null;
  target_mean: number | null;
  target_high: number | null;
  target_low: number | null;
}

export interface CompanyResponse {
  ticker: string;
  company_name: string | null;
  sector: string | null;
  industry: string | null;
  exchange: string | null;
  as_of_date: string | null;
  price: PriceData;
  valuation: ValuationData;
  profitability: ProfitabilityData;
  growth: GrowthData;
  financial_health: FinancialHealthData;
  ownership: OwnershipData;
  technicals: TechnicalsData;
  analyst_coverage: AnalystData;
}

export interface ChartDataPoint {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
}

export interface ChartResponse {
  ticker: string;
  range: string;
  data: ChartDataPoint[];
}

export interface PeerEntry {
  ticker: string;
  company_name: string | null;
  current_price: number | null;
  market_cap_crore: number | null;
  pe_ratio: number | null;
  roe_pct: number | null;
  revenue_growth_pct: number | null;
  debt_to_equity: number | null;
}

export interface PeerResponse {
  ticker: string;
  peers: PeerEntry[];
}
