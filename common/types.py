"""Pydantic models for the stock screener API."""

from typing import Literal

from pydantic import BaseModel, Field


class ScreenError(Exception):
    """Base exception for screener errors."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class FilterValidationError(ScreenError):
    """Raised when a filter combination is invalid."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=2)


class FilterSpec(BaseModel):
    """Specification for screening/filtering stocks.

    All filter fields are optional.  Only populated fields contribute
    conditions to the generated SQL WHERE clause.
    """

    # ── Identity ──────────────────────────────────────────────────────
    sectors: list[str] | None = None
    industries: list[str] | None = None
    ticker: str | None = None
    search: str | None = None

    # ── Valuation ─────────────────────────────────────────────────────
    pe_min: float | None = None
    pe_max: float | None = None
    market_cap_min: float | None = None
    market_cap_max: float | None = None
    pb_min: float | None = None
    pb_max: float | None = None
    peg_max: float | None = None
    price_to_sales_max: float | None = None

    # ── Profitability ─────────────────────────────────────────────────
    roe_min: float | None = None
    roa_min: float | None = None
    profit_margin_min: float | None = None
    operating_margin_min: float | None = None

    # ── Growth ────────────────────────────────────────────────────────
    revenue_growth_min: float | None = None
    earnings_growth_min: float | None = None

    # ── Financial health ──────────────────────────────────────────────
    debt_to_equity_max: float | None = None
    current_ratio_min: float | None = None
    dividend_yield_min: float | None = None

    # ── Ownership ─────────────────────────────────────────────────────
    promoter_holding_min: float | None = None

    # ── Price-based (use stock_fundamentals columns for 52w; JOIN eod_prices for DMA) ──
    price_pct_from_52w_high_max: float | None = None
    price_pct_from_52w_low_min: float | None = None
    price_above_50dma: bool = False
    price_above_200dma: bool = False
    volume_above_20d_avg: bool = False

    # ── Sorting & pagination ──────────────────────────────────────────
    sort_by: str = "market_cap_crore"
    sort_dir: Literal["asc", "desc"] = "desc"
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class ScreenResponse(BaseModel):
    """Response from a screen query."""

    columns: list[str]
    rows: list[list]
    total_count: int
    query_time_ms: float
    warnings: list[str] = []


class FilterOptions(BaseModel):
    """Available filter options for the UI."""

    sectors: list[str]
    industries: list[str]
    sort_columns: list[dict]  # [{"value": "...", "label": "..."}]


class HealthResponse(BaseModel):
    """Health-check response for the API."""

    status: str
    latest_data_date: str | None = None
    stock_count: int | None = None
    db_size_mb: float | None = None
    stale: bool = False


class NLScreenRequest(BaseModel):
    """Natural-language screen request."""

    query: str


class NLScreenResponse(ScreenResponse):
    """Natural-language screen response, extending ScreenResponse."""

    interpreted_as: str | None = None


class PriceData(BaseModel):
    current: float | None = None
    change: float | None = None
    change_pct: float | None = None
    prev_close: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    high_52w: float | None = None
    low_52w: float | None = None
    volume_today: int | None = None


class ValuationData(BaseModel):
    market_cap_crore: float | None = None
    pe_ratio: float | None = None
    forward_pe: float | None = None
    pb_ratio: float | None = None
    peg_ratio: float | None = None
    price_to_sales: float | None = None
    eps_ttm: float | None = None
    eps_forward: float | None = None
    book_value_per_share: float | None = None


class ProfitabilityData(BaseModel):
    roe_pct: float | None = None
    roa_pct: float | None = None
    profit_margins_pct: float | None = None
    operating_margins_pct: float | None = None
    gross_margins_pct: float | None = None
    ebitda_margins_pct: float | None = None


class GrowthData(BaseModel):
    revenue_growth_pct: float | None = None
    earnings_growth_pct: float | None = None
    earnings_quarterly_growth_pct: float | None = None


class FinancialHealthData(BaseModel):
    debt_to_equity: float | None = None
    current_ratio: float | None = None
    quick_ratio: float | None = None
    payout_ratio: float | None = None
    dividend_yield_pct: float | None = None
    five_year_avg_dividend_yield_pct: float | None = None
    free_cashflow: float | None = None
    operating_cashflow: float | None = None
    total_debt: float | None = None
    total_revenue: float | None = None
    ebitda: float | None = None
    total_cash_per_share: float | None = None


class OwnershipData(BaseModel):
    promoter_pct: float | None = None
    institutional_pct: float | None = None
    public_pct: float | None = None


class TechnicalsData(BaseModel):
    beta: float | None = None
    price_pct_from_52w_high: float | None = None
    price_pct_from_52w_low: float | None = None


class AnalystData(BaseModel):
    recommendation: str | None = None
    number_of_analysts: int | None = None
    target_mean: float | None = None
    target_high: float | None = None
    target_low: float | None = None


class CompanyResponse(BaseModel):
    ticker: str
    company_name: str | None = None
    sector: str | None = None
    industry: str | None = None
    exchange: str | None = None
    as_of_date: str | None = None
    price: PriceData = PriceData()
    valuation: ValuationData = ValuationData()
    profitability: ProfitabilityData = ProfitabilityData()
    growth: GrowthData = GrowthData()
    financial_health: FinancialHealthData = FinancialHealthData()
    ownership: OwnershipData = OwnershipData()
    technicals: TechnicalsData = TechnicalsData()
    analyst_coverage: AnalystData = AnalystData()


class ChartDataPoint(BaseModel):
    date: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None


class ChartResponse(BaseModel):
    ticker: str
    range: str
    data: list[ChartDataPoint]


class PeerEntry(BaseModel):
    ticker: str
    company_name: str | None = None
    current_price: float | None = None
    market_cap_crore: float | None = None
    pe_ratio: float | None = None
    roe_pct: float | None = None
    revenue_growth_pct: float | None = None
    debt_to_equity: float | None = None


class PeerResponse(BaseModel):
    ticker: str
    peers: list[PeerEntry]
