-- Strattest: Unified yfinance-sourced schema
-- All data sourced from yfinance for consistency

CREATE TABLE IF NOT EXISTS eod_prices (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,            -- ISO format: '2021-07-02'
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    dividends REAL DEFAULT 0,
    stock_splits REAL DEFAULT 0,
    PRIMARY KEY (ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_eod_ticker ON eod_prices(ticker);
CREATE INDEX IF NOT EXISTS idx_eod_date ON eod_prices(date);

-- Flattened latest fundamentals snapshot per stock
-- Refreshed periodically (weekly/monthly)
CREATE TABLE IF NOT EXISTS stock_fundamentals (
    ticker TEXT PRIMARY KEY,
    as_of_date TEXT NOT NULL,

    -- Identity
    company_name TEXT,
    sector TEXT,
    industry TEXT,
    exchange TEXT,

    -- Valuation
    current_price REAL,
    market_cap_crore REAL,          -- marketCap / 1e7
    pe_ratio REAL,                  -- trailingPE
    forward_pe REAL,                -- forwardPE
    pb_ratio REAL,                  -- priceToBook
    peg_ratio REAL,
    price_to_sales REAL,

    -- Profitability
    roe_pct REAL,                   -- returnOnEquity * 100
    roa_pct REAL,                   -- returnOnAssets * 100
    profit_margins_pct REAL,        -- profitMargins * 100
    operating_margins_pct REAL,     -- operatingMargins * 100
    gross_margins_pct REAL,         -- grossMargins * 100
    ebitda_margins_pct REAL,        -- ebitdaMargins * 100

    -- Per-share
    eps_ttm REAL,                   -- trailingEps
    eps_forward REAL,               -- forwardEps
    book_value_per_share REAL,      -- bookValue
    revenue_per_share REAL,

    -- Growth
    revenue_growth_pct REAL,        -- revenueGrowth * 100
    earnings_growth_pct REAL,       -- earningsGrowth * 100
    earnings_quarterly_growth_pct REAL,

    -- Financial health
    debt_to_equity REAL,
    current_ratio REAL,
    quick_ratio REAL,
    payout_ratio REAL,

    -- Returns & yield
    dividend_yield_pct REAL,
    five_year_avg_dividend_yield_pct REAL,

    -- Price history
    high_52w REAL,                  -- fiftyTwoWeekHigh
    low_52w REAL,                   -- fiftyTwoWeekLow
    beta REAL,

    -- Targets & ratings
    target_mean_price REAL,
    target_high_price REAL,
    target_low_price REAL,
    recommendation TEXT,            -- buy/hold/sell
    number_of_analysts INTEGER,

    -- Ownership
    held_pct_insiders REAL,
    held_pct_institutions REAL,

    -- Cash flows
    free_cashflow REAL,
    operating_cashflow REAL,
    total_cash_per_share REAL,
    total_debt REAL,
    total_revenue REAL,
    ebitda REAL
);
