# Screener Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a text-to-SQL CLI (`python -m screener`) that accepts natural language stock screening queries, generates SQL via DeepSeek V4 Flash, validates with sqlglot, executes against read-only SQLite, and returns formatted results.

**Architecture:** Seven modules in `screener/`. Config loads env vars from `.env`. Glossary and examples feed into PromptBuilder, which assembles the full LLM prompt. Screener orchestrates: build prompt → call LLM → validate → execute → return. CLI handles argparse and output formatting.

**Tech Stack:** Python 3.13, openai SDK, sqlglot, sqlite3 (stdlib), rich, python-dotenv

---

### Task 1: Project setup — dependencies and directory

**Files:**
- Modify: `requirements.txt`
- Create: `screener/__init__.py`

- [ ] **Step 1: Add dependencies to requirements.txt**

```bash
cat >> requirements.txt << 'EOF'
openai>=1.0.0
rich>=13.0.0
python-dotenv>=1.0.0
EOF
```

- [ ] **Step 2: Create screener package directory**

```bash
mkdir -p screener
```

- [ ] **Step 3: Create empty __init__.py (placeholder, will be populated in Task 7)**

Write `screener/__init__.py`:
```python
"""Screener — text-to-SQL stock screening for strattest."""
```

- [ ] **Step 4: Install dependencies**

```bash
pip install openai rich python-dotenv
```

- [ ] **Step 5: Commit**

```bash
git add requirements.txt screener/__init__.py
git commit -m "Set up screener package skeleton and dependencies"
```

---

### Task 2: Config module

**Files:**
- Create: `screener/config.py`
- Create: `screener/test_config.py`

- [ ] **Step 1: Write the failing test**

Write `screener/test_config.py`:
```python
import os
from screener.config import Config

def test_config_loads_from_env(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("STRATTEST_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("STRATTEST_DB_PATH", "db/test.db")
    monkeypatch.setenv("STRATTEST_QUERY_TIMEOUT", "30")
    monkeypatch.setenv("STRATTEST_MAX_ROWS", "500")

    cfg = Config()

    assert cfg.api_key == "sk-test"
    assert cfg.base_url == "https://api.deepseek.com"
    assert cfg.model == "deepseek-v4-flash"
    assert cfg.db_path == "db/test.db"
    assert cfg.query_timeout == 30
    assert cfg.max_rows == 500


def test_config_defaults(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.delenv("STRATTEST_DB_PATH", raising=False)
    monkeypatch.delenv("STRATTEST_QUERY_TIMEOUT", raising=False)
    monkeypatch.delenv("STRATTEST_MAX_ROWS", raising=False)
    monkeypatch.delenv("STRATTEST_MODEL", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)

    cfg = Config()

    assert cfg.db_path == "db/strattest.db"
    assert cfg.query_timeout == 30
    assert cfg.max_rows == 1000
    assert cfg.model == "deepseek-v4-flash"
    assert cfg.base_url == "https://api.deepseek.com"


def test_config_missing_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    try:
        Config()
        assert False, "Expected SystemExit"
    except SystemExit as e:
        assert e.code == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest screener/test_config.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'screener.config'`

- [ ] **Step 3: Write config.py**

Write `screener/config.py`:
```python
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            print("Error: DEEPSEEK_API_KEY environment variable is required")
            sys.exit(1)

        self.base_url = os.environ.get(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        )
        self.model = os.environ.get("STRATTEST_MODEL", "deepseek-v4-flash")
        self.db_path = os.environ.get("STRATTEST_DB_PATH", "db/strattest.db")
        self.query_timeout = int(
            os.environ.get("STRATTEST_QUERY_TIMEOUT", "30")
        )
        self.max_rows = int(os.environ.get("STRATTEST_MAX_ROWS", "1000"))

    @property
    def db_path_absolute(self):
        repo_root = Path(__file__).parent.parent
        return str(repo_root / self.db_path)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest screener/test_config.py -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add screener/config.py screener/test_config.py
git commit -m "Add Config module with env-var loading and tests"
```

---

### Task 3: Glossary module

**Files:**
- Create: `screener/glossary.py`
- Create: `screener/test_glossary.py`

- [ ] **Step 1: Write the failing test**

Write `screener/test_glossary.py`:
```python
from screener.glossary import GLOSSARY


def test_glossary_covers_all_schema_columns():
    """Every column in schema.sql must have a glossary entry."""
    from pathlib import Path

    schema_path = (
        Path(__file__).parent.parent / "data_pipeline" / "schema.sql"
    )
    schema = schema_path.read_text()

    # Extract column names from CREATE TABLE statements
    missing = []
    in_create = False
    for line in schema.split("\n"):
        stripped = line.strip()
        if stripped.startswith("CREATE TABLE"):
            in_create = True
            continue
        if in_create and stripped.startswith(");"):
            in_create = False
            continue
        if in_create and stripped and not stripped.startswith("--") and not stripped.startswith("PRIMARY") and not stripped.startswith(")"):
            # Extract column name (first word before whitespace or comma)
            col = stripped.strip().split()[0].strip(",")
            if col and col not in GLOSSARY:
                missing.append(col)

    # Index columns are excluded — they don't appear in queries
    missing = [m for m in missing if not m.startswith("idx_")]

    assert missing == [], f"Missing glossary entries for: {missing}"


def test_glossary_has_key_columns():
    assert "pe_ratio" in GLOSSARY
    assert "roe_pct" in GLOSSARY
    assert "market_cap_crore" in GLOSSARY
    assert "sector" in GLOSSARY
    assert "ticker" in GLOSSARY
    assert "debt_to_equity" in GLOSSARY
    assert "revenue_growth_pct" in GLOSSARY
    assert "close" in GLOSSARY
    assert "beta" in GLOSSARY


def test_glossary_values_are_strings():
    for k, v in GLOSSARY.items():
        assert isinstance(v, str), f"Glossary entry '{k}' is not a string"
        assert len(v) > 20, f"Glossary entry '{k}' too short: {len(v)} chars"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest screener/test_glossary.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'screener.glossary'`

- [ ] **Step 3: Write glossary.py**

Write `screener/glossary.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest screener/test_glossary.py -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add screener/glossary.py screener/test_glossary.py
git commit -m "Add column glossary with descriptions, units, and thresholds"
```

---

### Task 4: Examples module

**Files:**
- Create: `screener/examples.py`

- [ ] **Step 1: Write examples.py**

Write `screener/examples.py`:
```python
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
```

- [ ] **Step 2: Commit**

```bash
git add screener/examples.py
git commit -m "Add 16 few-shot SQL examples with keyword tags"
```

---

### Task 5: Prompt Builder module

**Files:**
- Create: `screener/prompt_builder.py`
- Create: `screener/test_prompt_builder.py`

- [ ] **Step 1: Write the failing test**

Write `screener/test_prompt_builder.py`:
```python
from screener.prompt_builder import PromptBuilder


def test_build_includes_system_message():
    pb = PromptBuilder()
    prompt = pb.build("test query")
    assert "SQL generator" in prompt
    assert "Indian stock market" in prompt


def test_build_includes_sqlite_rules():
    pb = PromptBuilder()
    prompt = pb.build("test query")
    assert "No RIGHT JOIN" in prompt
    assert "No CONCAT()" in prompt
    assert "IFNULL() or COALESCE()" in prompt
    assert "Always LIMIT" in prompt


def test_build_includes_ddl():
    pb = PromptBuilder()
    prompt = pb.build("test query")
    assert "CREATE TABLE" in prompt
    assert "eod_prices" in prompt
    assert "stock_fundamentals" in prompt


def test_build_includes_glossary():
    pb = PromptBuilder()
    prompt = pb.build("test query")
    assert "pe_ratio" in prompt
    assert "roe_pct" in prompt


def test_build_includes_user_question():
    pb = PromptBuilder()
    prompt = pb.build("find cheap banks with low debt")
    assert "find cheap banks with low debt" in prompt


def test_build_includes_examples():
    pb = PromptBuilder()
    prompt = pb.build("stocks with PE under 15 and growth above 20%")
    assert "[EXAMPLES]" in prompt
    # Should match valuation/growth examples
    assert "pe_ratio" in prompt.lower()


def test_example_selection_falls_back_for_unmatched_query():
    pb = PromptBuilder()
    prompt = pb.build("xyzzy flurbo glarp")  # nonsense, won't match any tags
    # Should still include some examples (fallback to first few)
    assert "[EXAMPLES]" in prompt
    assert "SELECT" in prompt


def test_promptbuilder_uses_schema_from_data_pipeline():
    pb = PromptBuilder()
    prompt = pb.build("test")
    # Schema columns should be present
    assert "PRIMARY KEY (ticker, date)" in prompt


def test_build_includes_limit_instruction():
    pb = PromptBuilder()
    prompt = pb.build("test query")
    assert "LIMIT" in prompt  # at least one example should have LIMIT
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest screener/test_prompt_builder.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'screener.prompt_builder'`

- [ ] **Step 3: Write prompt_builder.py**

Write `screener/prompt_builder.py`:
```python
"""Assembles the full LLM prompt from schema, glossary, examples, and user query."""

from pathlib import Path

from screener.glossary import GLOSSARY
from screener.examples import EXAMPLES

SCHEMA_PATH = Path(__file__).parent.parent / "data_pipeline" / "schema.sql"

SYSTEM_PROMPT = (
    "You are a SQL generator for a SQLite database of Indian stock market data. "
    "Generate ONLY a SELECT query — no explanations, no markdown, no code fences."
)

SQLITE_RULES = """[SQLITE RULES]
- This is SQLite 3. No RIGHT JOIN, FULL OUTER JOIN, or window functions with RANGE.
- Dates are TEXT in ISO format ('2021-07-02'). Use date('now') for today,
  strftime('%Y-%m-%d', date_col, '+30 days') for arithmetic, julianday() for
  day differences.
- String matching: LIKE is case-insensitive for ASCII. No ILIKE, no REGEXP.
  Use UPPER() or LOWER() only when needed.
- No CONCAT() — use the || operator.
- No IF() — use CASE WHEN ... THEN ... ELSE ... END.
- Aggregation: GROUP_CONCAT() instead of STRING_AGG() or ARRAY_AGG().
- Booleans are 1/0, not TRUE/FALSE.
- Always use LIMIT, never FETCH FIRST or TOP.
- IFNULL() or COALESCE() for null handling, not NVL() or ISNULL().
- No SERIAL, no AUTO_INCREMENT — this is a read-only query, no DDL."""


class PromptBuilder:
    def __init__(self, max_examples: int = 3):
        self._schema = SCHEMA_PATH.read_text()
        self._max_examples = max_examples

    def build(self, user_question: str) -> str:
        parts = [
            SYSTEM_PROMPT,
            "",
            SQLITE_RULES,
            "",
            "[DDL]",
            self._schema,
            "",
            "[GLOSSARY]",
            self._build_glossary_section(),
            "",
            "[EXAMPLES]",
            self._build_examples_section(user_question),
            "",
            "[QUESTION]",
            user_question,
        ]
        return "\n".join(parts)

    def _build_glossary_section(self) -> str:
        lines = []
        for col, desc in GLOSSARY.items():
            lines.append(f"{col}: {desc}")
        return "\n".join(lines)

    def _build_examples_section(self, user_question: str) -> str:
        query_lower = user_question.lower()
        scored = []
        for ex in EXAMPLES:
            score = sum(
                1 for tag in ex["tags"] if tag.lower() in query_lower
            )
            scored.append((score, ex))

        scored.sort(key=lambda x: x[0], reverse=True)

        selected = [ex for score, ex in scored[: self._max_examples]]

        # If no tags matched, fall back to first few examples
        if not selected or scored[0][0] == 0:
            selected = EXAMPLES[: self._max_examples]

        lines = []
        for ex in selected:
            lines.append(f"Q: \"{ex['question']}\"")
            lines.append(f"SQL: {ex['sql']}")
            lines.append("")
        return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest screener/test_prompt_builder.py -v
```
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add screener/prompt_builder.py screener/test_prompt_builder.py
git commit -m "Add PromptBuilder with schema, glossary, examples, and SQLite rules"
```

---

### Task 6: Screener core orchestrator

**Files:**
- Create: `screener/screener.py`
- Create: `screener/test_screener.py`

- [ ] **Step 1: Write test_screener.py (mocked LLM, real SQLite)**

Write `screener/test_screener.py`:
```python
import sqlite3
import pytest
from screener.screener import Screener, QueryError
from screener.config import Config
from screener.prompt_builder import PromptBuilder


@pytest.fixture
def test_db(tmp_path):
    """Create a minimal test database."""
    db_path = tmp_path / "test.db"
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript("""
            CREATE TABLE eod_prices (
                ticker TEXT NOT NULL,
                date TEXT NOT NULL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (ticker, date)
            );
            CREATE TABLE stock_fundamentals (
                ticker TEXT PRIMARY KEY,
                company_name TEXT,
                sector TEXT,
                pe_ratio REAL,
                roe_pct REAL,
                market_cap_crore REAL,
                debt_to_equity REAL
            );
            INSERT INTO stock_fundamentals VALUES
                ('TCS', 'Tata Consultancy', 'Technology', 28.5, 45.2, 1200000, 0.0),
                ('HDFCBANK', 'HDFC Bank', 'Financial Services', 18.3, 16.8, 850000, 0.8),
                ('RELIANCE', 'Reliance Industries', 'Energy', 22.1, 9.5, 1650000, 0.6),
                ('INFY', 'Infosys', 'Technology', 25.0, 32.1, 620000, 0.0),
                ('VBL', 'Varun Beverages', 'Consumer Defensive', 85.0, 28.0, 180000, 0.3);
            INSERT INTO eod_prices VALUES
                ('TCS', '2026-07-03', 3800.0, 2500000),
                ('HDFCBANK', '2026-07-03', 1650.0, 5200000),
                ('RELIANCE', '2026-07-03', 2450.0, 3800000);
        """)
    return str(db_path)


class FakeConfig:
    api_key = "sk-fake"
    base_url = "https://api.deepseek.com"
    model = "deepseek-v4-flash"
    db_path_absolute = None
    query_timeout = 5
    max_rows = 100

    def __init__(self, db_path):
        self.db_path_absolute = db_path


class FakeLLM:
    """Returns a fixed SQL string instead of calling DeepSeek."""
    def __init__(self, sql_to_return):
        self.sql_to_return = sql_to_return
        self.call_count = 0
        self.prompts = []

    def __call__(self, prompt):
        self.call_count += 1
        self.prompts.append(prompt)
        return self.sql_to_return


def test_screener_executes_valid_sql(test_db):
    cfg = FakeConfig(test_db)
    llm = FakeLLM("SELECT ticker, company_name, pe_ratio FROM stock_fundamentals WHERE pe_ratio < 30")
    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=llm)

    columns, rows = screener.query("cheap stocks")

    assert columns == ("ticker", "company_name", "pe_ratio")
    assert len(rows) == 3  # TCS, HDFCBANK, RELIANCE (not VBL with PE 85)
    assert rows[0][0] == "HDFCBANK"  # lowest PE first (order by PE ASC not in query, but data order)


def test_screener_extracts_sql_from_markdown(test_db):
    cfg = FakeConfig(test_db)
    llm = FakeLLM("```sql\nSELECT ticker FROM stock_fundamentals WHERE ticker = 'TCS'\n```")
    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=llm)

    columns, rows = screener.query("find TCS")

    assert rows[0][0] == "TCS"


def test_screener_retries_on_sqlglot_failure(test_db):
    cfg = FakeConfig(test_db)
    # First call returns invalid SQL, second returns valid
    responses = ["SELECT * FRUM stock_fundamentals", "SELECT * FROM stock_fundamentals"]
    call_count = [0]

    def bad_then_good(prompt):
        idx = call_count[0]
        call_count[0] += 1
        return responses[idx]

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=bad_then_good)

    columns, rows = screener.query("test")

    assert call_count[0] == 2
    assert len(rows) == 5


def test_screener_raises_on_double_failure(test_db):
    cfg = FakeConfig(test_db)
    llm = FakeLLM("NOT A VALID SQL STATEMENT AT ALL !!!")

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=llm)

    with pytest.raises(QueryError) as exc:
        screener.query("test")
    assert exc.value.exit_code == 2
    assert llm.call_count == 2


def test_screener_rejects_non_select(test_db):
    cfg = FakeConfig(test_db)
    llm = FakeLLM("DROP TABLE stock_fundamentals")

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=llm)

    with pytest.raises(QueryError) as exc:
        screener.query("test")
    assert exc.value.exit_code == 3


def test_screener_applies_row_limit(test_db):
    cfg = FakeConfig(test_db)
    cfg.max_rows = 2
    llm = FakeLLM("SELECT * FROM stock_fundamentals")

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=llm)

    columns, rows = screener.query("test")
    assert len(rows) == 2


def test_screener_empty_results(test_db):
    cfg = FakeConfig(test_db)
    llm = FakeLLM("SELECT * FROM stock_fundamentals WHERE pe_ratio < 0")

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=llm)

    columns, rows = screener.query("test")
    assert rows == []


def test_screener_readonly_prevents_writes(test_db):
    """Verify we open the DB in read-only mode."""
    cfg = FakeConfig(test_db)
    llm = FakeLLM("INSERT INTO stock_fundamentals (ticker) VALUES ('EVIL')")

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=llm)

    with pytest.raises(QueryError) as exc:
        screener.query("test")
    # SQLite will reject the write on a read-only connection
    assert exc.value.exit_code == 3
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest screener/test_screener.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'screener.screener'`

- [ ] **Step 3: Write screener.py**

Write `screener/screener.py`:
```python
"""Core orchestrator: build prompt → LLM → validate → execute."""

import re
import sqlite3
from typing import Any

import sqlglot

from screener.config import Config
from screener.prompt_builder import PromptBuilder


class QueryError(Exception):
    def __init__(self, message: str, exit_code: int, sql: str | None = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.sql = sql


class Screener:
    def __init__(
        self,
        config: Config,
        prompt_builder: PromptBuilder | None = None,
        llm_callable=None,
    ):
        self._cfg = config
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._llm = llm_callable or _llm_call

    def query(self, user_question: str) -> tuple[tuple[str, ...], list[tuple[Any, ...]]]:
        prompt = self._prompt_builder.build(user_question)

        # Attempt 1
        raw = self._llm(
            prompt,
            api_key=self._cfg.api_key,
            base_url=self._cfg.base_url,
            model=self._cfg.model,
        )
        sql = _extract_sql(raw)

        # Validate and possibly retry
        try:
            sqlglot.parse(sql)
        except Exception as parse_err:
            retry_prompt = (
                prompt
                + f"\n\nYour previous SQL had a syntax error: {parse_err}\n"
                + "Generate corrected SQL. Output ONLY the SQL, no explanations."
            )
            raw = self._llm(
                retry_prompt,
                api_key=self._cfg.api_key,
                base_url=self._cfg.base_url,
                model=self._cfg.model,
            )
            sql = _extract_sql(raw)
            try:
                sqlglot.parse(sql)
            except Exception as parse_err2:
                raise QueryError(
                    f"Syntax error after retry: {parse_err2}\n\n"
                    f"SQL attempted:\n{sql}",
                    exit_code=2,
                    sql=sql,
                )

        # Safety: only SELECT
        if not sql.strip().upper().startswith("SELECT"):
            raise QueryError(
                f"Non-SELECT statement rejected.\n\nSQL:\n{sql}",
                exit_code=3,
                sql=sql,
            )

        # Execute
        try:
            conn = sqlite3.connect(
                f"file:{self._cfg.db_path_absolute}?mode=ro", uri=True
            )
            conn.execute(f"PRAGMA query_only = ON")
        except sqlite3.OperationalError as e:
            raise QueryError(
                f"Cannot open database: {e}", exit_code=3, sql=sql
            )

        try:
            conn.execute(f"PRAGMA busy_timeout = {self._cfg.query_timeout * 1000}")
            # Add LIMIT if not present
            if "LIMIT" not in sql.upper():
                sql = sql.rstrip(";") + f" LIMIT {self._cfg.max_rows}"
            cursor = conn.execute(sql)
            columns = tuple(d[0] for d in cursor.description) if cursor.description else ()
            rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            raise QueryError(
                f"Query execution failed: {e}\n\nSQL:\n{sql}",
                exit_code=3,
                sql=sql,
            )
        finally:
            conn.close()

        return columns, rows


def _extract_sql(raw: str) -> str:
    """Extract SQL from LLM response, stripping markdown fences if present."""
    s = raw.strip()
    # Remove ```sql ... ``` or ``` ... ``` fences
    m = re.search(r"```(?:sql)?\s*\n?(.*?)```", s, re.DOTALL)
    if m:
        s = m.group(1).strip()
    # If the response starts with SELECT, take the first paragraph
    if s.upper().startswith("SELECT"):
        lines = s.split("\n")
        # Grab until first blank line or non-SQL line
        sql_lines = []
        for line in lines:
            if line.strip() == "":
                break
            sql_lines.append(line)
        s = " ".join(sql_lines)
    return s.strip()


def _llm_call(
    prompt: str,
    api_key: str,
    base_url: str,
    model: str,
) -> str:
    """Call DeepSeek via OpenAI-compatible SDK."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )
    return response.choices[0].message.content
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest screener/test_screener.py -v
```
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add screener/screener.py screener/test_screener.py
git commit -m "Add Screener orchestrator with SQL extraction, validation, retry, and read-only execution"
```

---

### Task 7: CLI module and __main__.py

**Files:**
- Create: `screener/cli.py`
- Create: `screener/__main__.py`
- Modify: `screener/__init__.py`

- [ ] **Step 1: Write cli.py**

Write `screener/cli.py`:
```python
"""CLI: argument parsing and output formatting."""

import argparse
import csv
import io
import sys

from rich.console import Console
from rich.table import Table

from screener.config import Config
from screener.screener import Screener, QueryError


def main():
    parser = argparse.ArgumentParser(
        prog="screener",
        description="Text-to-SQL stock screening for Indian markets.",
    )
    parser.add_argument(
        "query",
        nargs="+",
        help="Natural language screening query (e.g. 'stocks with PE < 15 and ROE > 20%%')",
    )
    parser.add_argument(
        "--format",
        choices=["table", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max rows to return (overrides STRATTEST_MAX_ROWS)",
    )
    args = parser.parse_args()

    user_question = " ".join(args.query)

    cfg = Config()
    if args.limit is not None:
        cfg.max_rows = args.limit

    screener = Screener(cfg)

    try:
        columns, rows = screener.query(user_question)
    except QueryError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(e.exit_code)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("No stocks matched.", file=sys.stderr)
        sys.exit(0)

    if args.format == "csv":
        _format_csv(columns, rows)
    else:
        _format_table(columns, rows)

    print(f"{len(rows)} rows", file=sys.stderr)
    sys.exit(0)


def _format_csv(columns, rows):
    writer = csv.writer(sys.stdout)
    writer.writerow(columns)
    writer.writerows(rows)


def _format_table(columns, rows):
    console = Console()
    table = Table(title="Screener Results")

    for col in columns:
        table.add_column(col, no_wrap=False)

    for row in rows:
        table.add_row(*[_fmt_cell(v) for v in row])

    console.print(table)


def _fmt_cell(value):
    if value is None:
        return "—"
    if isinstance(value, float):
        # Show up to 2 decimal places, strip trailing zeros
        s = f"{value:.2f}".rstrip("0").rstrip(".")
        return s
    return str(value)
```

- [ ] **Step 2: Write __main__.py**

Write `screener/__main__.py`:
```python
from screener.cli import main

main()
```

- [ ] **Step 3: Update __init__.py**

Write `screener/__init__.py`:
```python
"""Screener — text-to-SQL stock screening for strattest."""

from screener.screener import Screener, QueryError

__all__ = ["Screener", "QueryError"]
```

- [ ] **Step 4: Manual smoke test (with real DeepSeek API)**

```bash
python -m screener "banks with PE under 20 and ROE above 10"
```
Expected: formatted table of results or descriptive error

- [ ] **Step 5: Commit**

```bash
git add screener/cli.py screener/__main__.py screener/__init__.py
git commit -m "Add CLI interface with rich table and CSV output"
```

---

### Task 8: Final integration test and cleanup

**Files:**
- Create: `screener/test_integration.py`

- [ ] **Step 1: Write integration test (with fake LLM)**

Write `screener/test_integration.py`:
```python
"""End-to-end integration tests with a fake LLM and real SQLite."""

import sqlite3
import pytest
from screener.screener import Screener
from screener.prompt_builder import PromptBuilder


@pytest.fixture
def integration_db(tmp_path):
    """Full schema test database."""
    from pathlib import Path
    schema_path = Path(__file__).parent.parent / "data_pipeline" / "schema.sql"
    db_path = tmp_path / "integration.db"
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(schema_path.read_text())
        # Insert sample data
        conn.executescript("""
            INSERT INTO stock_fundamentals VALUES
                ('TCS', '2026-07-01', 'Tata Consultancy', 'Technology', 'Software',
                 'NSI', 3800, 1230000, 28.5, 25.0, 12.3, 2.1, 7.5,
                 45.2, 22.0, 19.5, 25.0, 55.0, 35.0,
                 133.3, 152.0, 310.0, 350.0,
                 12.5, 10.2, 8.5,
                 0.0, 2.5, 2.0, 35.0,
                 1.2, 1.1,
                 4200, 3400, 0.85,
                 4200, 4500, 3800,
                 'buy', 42,
                 8.5, 45.0,
                 35000, 42000, 120.0,
                 0, 650000, 28000);
            INSERT INTO stock_fundamentals VALUES
                ('VBL', '2026-07-01', 'Varun Beverages', 'Consumer Defensive', 'Beverages',
                 'NSI', 1500, 180000, 85.0, 60.0, 18.5, 3.5, 12.0,
                 28.0, 12.0, 10.0, 18.0, 48.0, 22.0,
                 17.6, 25.0, 83.0, 125.0,
                 35.0, 40.0, 25.0,
                 0.3, 1.2, 1.0, 15.0,
                 0.3, 0.2,
                 1600, 800, 0.95,
                 1800, 2000, 1300,
                 'buy', 28,
                 65.0, 22.0,
                 12000, 15000, 45.0,
                 5000, 85000, 12000);
            INSERT INTO eod_prices VALUES
                ('TCS', '2026-07-01', 3800, 3850, 3780, 3800, 2500000, 0, 0),
                ('TCS', '2026-07-02', 3820, 3880, 3800, 3820, 2100000, 0, 0);
        """)
    return str(db_path)


class FakeConfig:
    api_key = "sk-test"
    base_url = "https://api.deepseek.com"
    model = "deepseek-v4-flash"
    query_timeout = 5
    max_rows = 100

    def __init__(self, db_path):
        self.db_path_absolute = db_path


def test_end_to_end_valuation_screen(integration_db):
    cfg = FakeConfig(integration_db)

    def fake_llm(prompt):
        return """SELECT ticker, company_name, pe_ratio, roe_pct, market_cap_crore
FROM stock_fundamentals WHERE pe_ratio < 30 AND pe_ratio > 0
AND roe_pct > 20 ORDER BY pe_ratio ASC"""

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=fake_llm)
    columns, rows = screener.query("stocks with PE under 30 and ROE above 20")

    # TCS matches (PE 28.5, ROE 45.2), VBL does not (PE 85)
    assert len(rows) == 1
    assert rows[0][0] == "TCS"


def test_end_to_end_joins_price_and_fundamentals(integration_db):
    cfg = FakeConfig(integration_db)

    def fake_llm(prompt):
        return """SELECT f.ticker, f.company_name, f.current_price, p.close
FROM stock_fundamentals f INNER JOIN eod_prices p ON f.ticker = p.ticker
WHERE p.date = '2026-07-02'"""

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=fake_llm)
    columns, rows = screener.query("stocks with recent price data")

    assert len(rows) >= 1


def test_end_to_end_sector_filter(integration_db):
    cfg = FakeConfig(integration_db)

    def fake_llm(prompt):
        return """SELECT ticker, company_name, sector FROM stock_fundamentals
WHERE sector = 'Consumer Defensive'"""

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=fake_llm)
    columns, rows = screener.query("consumer stocks")

    assert len(rows) == 1
    assert rows[0][0] == "VBL"


def test_sql_injection_prevented(integration_db):
    cfg = FakeConfig(integration_db)

    def fake_llm(prompt):
        return "SELECT ticker FROM stock_fundamentals WHERE ticker = 'TCS'; DROP TABLE stock_fundamentals; --'"

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=fake_llm)
    # Multiple statements will fail in sqlite3
    with pytest.raises(Exception):
        screener.query("malicious query")
```

- [ ] **Step 2: Run integration tests**

```bash
python -m pytest screener/test_integration.py -v
```
Expected: PASS (4 tests)

- [ ] **Step 3: Run entire test suite**

```bash
python -m pytest screener/ -v
```
Expected: all tests PASS

- [ ] **Step 4: Commit**

```bash
git add screener/test_integration.py
git commit -m "Add end-to-end integration tests with fake LLM"
```
