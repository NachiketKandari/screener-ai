"""Few-shot examples for SQL generation, each tagged with keywords."""

EXAMPLES = [
    # --- Valuation screens ---
    {
        "tags": ["pe", "pe_ratio", "valuation", "cheap", "undervalued", "value"],
        "question": "Stocks with PE under 15 and market cap above 1000 crore",
        "sql": """SELECT ticker, company_name, pe_ratio, market_cap_crore
FROM stock_fundamentals
WHERE pe_ratio < 15 AND pe_ratio > 0
AND market_cap_crore > 1000
ORDER BY pe_ratio ASC
LIMIT 100""",
    },
    {
        "tags": ["pb", "book", "value", "undervalued", "bank", "financial"],
        "question": "Stocks trading below book value with positive earnings",
        "sql": """SELECT ticker, company_name, pb_ratio, pe_ratio, roe_pct
FROM stock_fundamentals
WHERE pb_ratio < 1 AND pb_ratio > 0
AND pe_ratio > 0
AND roe_pct > 0
ORDER BY pb_ratio ASC
LIMIT 100""",
    },
    {
        "tags": ["dividend", "yield", "income", "dividend_yield"],
        "question": "High dividend stocks with low debt and PE under 20",
        "sql": """SELECT ticker, company_name, dividend_yield_pct, pe_ratio, debt_to_equity
FROM stock_fundamentals
WHERE dividend_yield_pct > 3
AND pe_ratio < 20 AND pe_ratio > 0
AND debt_to_equity < 1
ORDER BY dividend_yield_pct DESC
LIMIT 100""",
    },

    # --- Growth screens ---
    {
        "tags": ["growth", "revenue", "earnings", "revenue_growth", "earnings_growth"],
        "question": "High growth stocks with revenue growth above 25% and earnings growth above 20%",
        "sql": """SELECT ticker, company_name, sector, revenue_growth_pct, earnings_growth_pct, pe_ratio
FROM stock_fundamentals
WHERE revenue_growth_pct > 25
AND earnings_growth_pct > 20
AND pe_ratio > 0
ORDER BY revenue_growth_pct DESC
LIMIT 100""",
    },
    {
        "tags": ["growth", "pe", "peg", "peg_ratio", "undervalued"],
        "question": "Growth at reasonable price: PEG ratio below 1 and ROE above 15",
        "sql": """SELECT ticker, company_name, peg_ratio, pe_ratio, earnings_growth_pct, roe_pct
FROM stock_fundamentals
WHERE peg_ratio < 1 AND peg_ratio > 0
AND roe_pct > 15
ORDER BY peg_ratio ASC
LIMIT 100""",
    },

    # --- Quality / Profitability screens ---
    {
        "tags": ["roe", "quality", "profitability", "roe_pct", "roa"],
        "question": "Companies with ROE above 20% and profit margins above 15%",
        "sql": """SELECT ticker, company_name, sector, roe_pct, profit_margins_pct, pe_ratio
FROM stock_fundamentals
WHERE roe_pct > 20
AND profit_margins_pct > 15
ORDER BY roe_pct DESC
LIMIT 100""",
    },
    {
        "tags": ["debt", "low", "debt_to_equity", "conservative", "safe"],
        "question": "Debt-free or low-debt companies with good profitability",
        "sql": """SELECT ticker, company_name, debt_to_equity, roe_pct, current_ratio
FROM stock_fundamentals
WHERE debt_to_equity < 0.5
AND roe_pct > 12
AND current_ratio > 1.5
ORDER BY roe_pct DESC
LIMIT 100""",
    },

    # --- Sector screens ---
    {
        "tags": ["sector", "technology", "tech", "IT", "it"],
        "question": "IT and technology stocks sorted by market cap",
        "sql": """SELECT ticker, company_name, sector, market_cap_crore, pe_ratio, revenue_growth_pct
FROM stock_fundamentals
WHERE sector = 'Technology'
ORDER BY market_cap_crore DESC
LIMIT 100""",
    },
    {
        "tags": ["sector", "bank", "banking", "financial", "nbfc"],
        "question": "Banking and financial stocks with low P/B and good ROE",
        "sql": """SELECT ticker, company_name, sector, pb_ratio, roe_pct, market_cap_crore
FROM stock_fundamentals
WHERE sector = 'Financial Services'
AND pb_ratio < 2 AND pb_ratio > 0
AND roe_pct > 10
ORDER BY pb_ratio ASC
LIMIT 100""",
    },

    # --- Screens using eod_prices (time-series) ---
    {
        "tags": ["52", "week", "high", "low", "52_week", "near", "52w"],
        "question": "Stocks near their 52-week low that are profitable",
        "sql": """SELECT ticker, company_name, current_price, low_52w,
       ROUND((current_price / low_52w - 1) * 100, 1) AS pct_above_low
FROM stock_fundamentals
WHERE current_price < low_52w * 1.1
AND pe_ratio > 0
AND roe_pct > 10
ORDER BY pct_above_low ASC
LIMIT 100""",
    },
    {
        "tags": ["volume", "liquid", "liquidity", "traded", "active"],
        "question": "Most actively traded stocks today with market cap above 5000 crore",
        "sql": """SELECT f.ticker, f.company_name, f.market_cap_crore, p.volume
FROM stock_fundamentals f
INNER JOIN eod_prices p ON f.ticker = p.ticker
WHERE p.date = (SELECT MAX(date) FROM eod_prices)
AND f.market_cap_crore > 5000
AND p.volume > 0
ORDER BY p.volume DESC
LIMIT 50""",
    },
    {
        "tags": ["average", "avg", "sector", "group", "aggregate"],
        "question": "Average PE ratio by sector",
        "sql": """SELECT sector,
       ROUND(AVG(pe_ratio), 1) AS avg_pe,
       COUNT(*) AS stock_count
FROM stock_fundamentals
WHERE pe_ratio > 0 AND pe_ratio IS NOT NULL
GROUP BY sector
ORDER BY avg_pe ASC""",
    },
    {
        "tags": ["moving", "average", "dma", "trend", "momentum"],
        "question": "Stocks trading at least 10% above their 50-day moving average",
        "sql": """SELECT f.ticker, f.company_name, f.current_price,
       ROUND(AVG(p.close), 1) AS avg_50d,
       ROUND((f.current_price / AVG(p.close) - 1) * 100, 1) AS pct_above_50dma
FROM stock_fundamentals f
INNER JOIN eod_prices p ON f.ticker = p.ticker
WHERE p.date >= date('now', '-50 days')
AND f.current_price > 0
GROUP BY f.ticker
HAVING pct_above_50dma > 10
ORDER BY pct_above_50dma DESC
LIMIT 50""",
    },
    {
        "tags": ["analyst", "target", "upside", "buy"],
        "question": "Stocks with analyst buy rating and at least 20% upside to target",
        "sql": """SELECT ticker, company_name, current_price, target_mean_price,
       ROUND((target_mean_price / current_price - 1) * 100, 1) AS upside_pct,
       recommendation, number_of_analysts
FROM stock_fundamentals
WHERE recommendation = 'buy'
AND target_mean_price > current_price * 1.2
AND number_of_analysts >= 3
ORDER BY upside_pct DESC
LIMIT 100""",
    },
    {
        "tags": ["small", "cap", "smallcap", "small-cap"],
        "question": "Small cap stocks with high growth and low debt",
        "sql": """SELECT ticker, company_name, market_cap_crore, revenue_growth_pct,
       roe_pct, debt_to_equity
FROM stock_fundamentals
WHERE market_cap_crore < 5000 AND market_cap_crore > 0
AND revenue_growth_pct > 15
AND debt_to_equity < 1
AND roe_pct > 10
ORDER BY revenue_growth_pct DESC
LIMIT 100""",
    },
    {
        "tags": ["large", "cap", "largecap", "large-cap", "bluechip", "blue"],
        "question": "Large cap bluechip stocks with consistent dividends",
        "sql": """SELECT ticker, company_name, market_cap_crore, pe_ratio,
       dividend_yield_pct, roe_pct
FROM stock_fundamentals
WHERE market_cap_crore > 20000
AND dividend_yield_pct > 1
AND roe_pct > 10
AND pe_ratio > 0
ORDER BY market_cap_crore DESC
LIMIT 50""",
    },
]
