"""Column glossary with human descriptions, units, thresholds, and gotchas."""

GLOSSARY = {
    # === eod_prices ===
    "ticker": (
        "NSE stock symbol. Join key with stock_fundamentals. "
        "Example values: 'RELIANCE', 'TCS', 'INFY'."
    ),
    "date": (
        "Trading date in ISO format: '2021-07-02'. "
        "Use strftime('%Y-%m-%d', date_col) for formatting, "
        "date('now') for today, julianday() for day differences."
    ),
    "open": "Opening price for the day, adjusted for splits and dividends.",
    "high": "Highest traded price during the day, adjusted.",
    "low": "Lowest traded price during the day, adjusted.",
    "close": (
        "Adjusted closing price. Use this for all returns calculations, "
        "moving averages, and price-based filters. Already adjusted for "
        "splits and dividends."
    ),
    "volume": (
        "Number of shares traded. Higher = more liquid. Use for liquidity "
        "filters and volume-based indicators. NULL means no trades."
    ),
    "dividends": "Dividend amount per share paid on that date. 0 or NULL if none.",
    "stock_splits": "Stock split ratio for that date. 0 or NULL if no split.",

    # === stock_fundamentals: Identity ===
    "company_name": "Full company name as reported by yfinance.",
    "sector": (
        "Industry sector. Use exact values from data — common ones: "
        "'Technology', 'Financial Services', 'Healthcare', "
        "'Consumer Cyclical', 'Basic Materials', 'Industrials', "
        "'Consumer Defensive', 'Energy', 'Real Estate', 'Utilities', "
        "'Communication Services'. Use = or IN() for exact match."
    ),
    "industry": "Sub-industry classification. More granular than sector.",
    "exchange": "Exchange code. Almost always 'NSI' for NSE stocks.",
    "as_of_date": "Date when fundamentals were last refreshed.",

    # === stock_fundamentals: Valuation ===
    "current_price": "Latest trading price in rupees.",
    "market_cap_crore": (
        "Market capitalization in ₹ crore (NOT raw rupees). "
        "Divide by 100 for ₹100 crore. "
        "Large cap > 20000, mid cap 5000-20000, small cap < 5000."
    ),
    "pe_ratio": (
        "Trailing P/E ratio. Lower = cheaper. "
        "Common screens: < 15 (value), 15-25 (fair), > 50 (growth premium). "
        "NULL means the company is unprofitable (negative earnings). "
        "Always filter with IS NOT NULL or > 0 when using in calculations."
    ),
    "forward_pe": (
        "Forward P/E based on analyst earnings estimates. "
        "Compare to pe_ratio — lower forward PE suggests expected earnings growth. "
        "NULL if no analyst estimates."
    ),
    "pb_ratio": (
        "Price to Book ratio. < 1 may indicate undervaluation or distress. "
        "Best used for banking/financial stocks. NULL if book value unavailable."
    ),
    "peg_ratio": (
        "P/E divided by earnings growth rate. < 1 suggests undervalued growth. "
        "NULL if either P/E or growth rate unavailable."
    ),
    "price_to_sales": (
        "Price to Sales ratio. Useful when earnings are negative. "
        "Lower = cheaper relative to revenue. NULL if revenue unavailable."
    ),

    # === stock_fundamentals: Profitability ===
    "roe_pct": (
        "Return on Equity %. Already multiplied by 100 (15 means 15%, not 0.15). "
        "Above 15 is good, above 20 is excellent. "
        "Negative means the company is losing shareholder value."
    ),
    "roa_pct": (
        "Return on Assets %. Already in percentage. "
        "Higher = more efficient use of assets. "
        "Compare within same sector — asset-heavy industries have lower ROA."
    ),
    "profit_margins_pct": (
        "Net profit margin %. Already in percentage. "
        "Higher = more of each rupee of revenue becomes profit."
    ),
    "operating_margins_pct": (
        "Operating profit margin %. Already in percentage. "
        "Excludes interest and taxes — better for comparing operational efficiency."
    ),
    "gross_margins_pct": (
        "Gross profit margin %. Already in percentage. "
        "Higher = stronger pricing power. Compare within same industry."
    ),
    "ebitda_margins_pct": (
        "EBITDA margin %. Already in percentage. "
        "Use for capital-intensive industry comparisons."
    ),

    # === stock_fundamentals: Per-Share ===
    "eps_ttm": (
        "Trailing twelve-month earnings per share in rupees. "
        "price / eps_ttm should approximately equal pe_ratio. "
        "NULL for unprofitable companies."
    ),
    "eps_forward": (
        "Forward EPS estimate from analysts. NULL if no estimates."
    ),
    "book_value_per_share": (
        "Book value per share in rupees. "
        "current_price / book_value_per_share = pb_ratio."
    ),
    "revenue_per_share": (
        "Revenue per share in rupees. "
        "current_price / revenue_per_share = price_to_sales."
    ),

    # === stock_fundamentals: Growth ===
    "revenue_growth_pct": (
        "Year-over-year revenue growth %. Already in percentage. "
        "> 20 is high growth, > 50 is exceptional. "
        "Negative means declining revenue — investigate further."
    ),
    "earnings_growth_pct": (
        "Year-over-year earnings growth %. Already in percentage. "
        "Compare with revenue_growth to see if profitability is keeping pace. "
        "Earnings growing slower than revenue = margin compression."
    ),
    "earnings_quarterly_growth_pct": (
        "Quarter-over-quarter earnings growth %. Already in percentage. "
        "More volatile than annual — use for recent momentum checks."
    ),

    # === stock_fundamentals: Financial Health ===
    "debt_to_equity": (
        "Debt-to-equity ratio. < 1 is conservative, 1-2 is moderate, "
        "> 2 is highly levered. Important for manufacturing and capital-heavy "
        "industries. Less relevant for IT/services companies."
    ),
    "current_ratio": (
        "Current assets / current liabilities. > 1.5 is healthy short-term "
        "liquidity. < 1 is a red flag for working capital management. "
        "Too high (> 3) may indicate inefficient use of assets."
    ),
    "quick_ratio": (
        "Like current_ratio but excludes inventory. More conservative. "
        "> 1 is comfortable. Important for manufacturing companies."
    ),
    "payout_ratio": (
        "Dividend payout ratio. What % of earnings is paid as dividends. "
        "> 100 means paying dividends from reserves — unsustainable."
    ),

    # === stock_fundamentals: Returns & Yield ===
    "dividend_yield_pct": (
        "Dividend yield %. Already in percentage. "
        "> 3 is high yield, > 5 is very high (verify sustainability). "
        "0 means no dividend. NULL if unavailable."
    ),
    "five_year_avg_dividend_yield_pct": (
        "5-year average dividend yield %. Use to check if current yield "
        "is unusually high or low relative to history."
    ),

    # === stock_fundamentals: Price History ===
    "high_52w": "52-week high price in rupees. current_price / high_52w shows how far from peak.",
    "low_52w": "52-week low price in rupees. current_price / low_52w shows how far from trough.",
    "beta": (
        "Volatility vs market. 1 = moves with market. "
        "< 1 = less volatile (defensive stocks). > 1 = more volatile (aggressive). "
        "NULL if insufficient data to calculate."
    ),

    # === stock_fundamentals: Targets & Ratings ===
    "target_mean_price": "Average analyst price target in rupees. NULL if no coverage.",
    "target_high_price": "Highest analyst price target in rupees.",
    "target_low_price": "Lowest analyst price target in rupees.",
    "recommendation": (
        "Analyst consensus as TEXT: 'buy', 'hold', or 'sell'. "
        "Use exact match: WHERE recommendation = 'buy'. "
        "NULL if no analyst coverage."
    ),
    "number_of_analysts": (
        "Number of analysts covering the stock. Higher = more consensus confidence."
    ),

    # === stock_fundamentals: Ownership ===
    "held_pct_insiders": "Percentage held by insiders/promoters. Already in percentage (0-100).",
    "held_pct_institutions": (
        "Percentage held by institutions (FII + DII). Already in percentage. "
        "Higher institutional holding = more professional scrutiny."
    ),

    # === stock_fundamentals: Cash Flows ===
    "free_cashflow": "Free cash flow in rupees. Positive = company generates cash after capex.",
    "operating_cashflow": "Operating cash flow in rupees. Should exceed net income for quality.",
    "total_cash_per_share": "Cash and equivalents per share in rupees. High cash = acquisition potential or buyback capacity.",
    "total_debt": "Total debt in rupees. Compare to market cap to gauge leverage scale.",
    "total_revenue": "Total revenue in rupees. Use with market cap for PS ratio calculation.",
    "ebitda": "EBITDA in rupees. Use with total_debt for debt/EBITDA (leverage) ratio.",
}
