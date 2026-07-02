# Strattest

Stock market analytics toolkit for Indian markets (NSE). Natural language screening, strategy backtesting, and AI-powered strategy extraction — all from a local SQLite database.

## What's built

### Data pipeline (`data_pipeline/`)
- **2,380 NSE stocks** × 5 years daily OHLCV (2.95M rows, 2021–2026)
- **2,367 stock fundamentals** (99.5% coverage) — 48 columns: PE, ROE, sector, market cap, debt, growth, dividends, analyst targets, etc.
- Sourced from [yfinance](https://pypi.org/project/yfinance/) (free, no API key)
- Scripts: `backfill.py` (one-time), `daily_sync.py` (cron — daily OHLCV, weekly fundamentals)

### Screener (`screener/`)
- Text-to-SQL CLI: `python -m screener "banks with PE under 15 and ROE above 20%"`
- DeepSeek V4 Flash generates SQL from natural language
- Validates with sqlglot, executes on read-only SQLite, retries on failure
- Output as rich-formatted table or CSV

## Setup

```bash
git clone <repo-url>
cd strattest
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Environment

Create `.env`:

```
DEEPSEEK_API_KEY=your-deepseek-api-key
```

Optional overrides:

| Variable | Default |
|---|---|
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` |
| `STRATTEST_MODEL` | `deepseek-v4-flash` |
| `STRATTEST_DB_PATH` | `db/strattest.db` |
| `STRATTEST_QUERY_TIMEOUT` | `30` |
| `STRATTEST_MAX_ROWS` | `1000` |

### Database

The database is gitignored (373 MB). Build it:

```bash
python data_pipeline/backfill.py
```

This takes ~2 hours for OHLCV + fundamentals. Yahoo rate limits are handled with jittered delays.

## Usage

### Screener

```bash
python -m screener "stocks with PE < 15, ROE > 20%, and market cap above 1000 crore"

# CSV output
python -m screener --format csv "large cap IT stocks" > results.csv

# Override row limit
python -m screener --limit 50 "most active stocks today"
```

### Data sync

```bash
# Daily OHLCV append + weekly fundamentals refresh
python data_pipeline/daily_sync.py
```

## What's next

| Module | Description |
|---|---|
| `strategy_extractor/` | YouTube transcript → LLM → structured trading strategy JSON |
| `backtest_engine/` | Strategy JSON → backtrader → Sharpe, drawdown, equity curve |

## Stack

Python · yfinance · SQLite · sqlglot · DeepSeek V4 Flash · rich · OpenRouter-compatible

No ORM, no web framework, no external services beyond the LLM API.

## Running tests

```bash
python -m pytest screener/ -v
```
