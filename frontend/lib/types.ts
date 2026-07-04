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
