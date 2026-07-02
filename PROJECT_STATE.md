# Strattest — Project State (July 2, 2026)

## What this is
A stock market analytics SaaS (screener.in + AI). Users paste YouTube links of trading strategies → AI extracts strategy → backtests against 5 years of Indian stock data.

## What's built (backend)

### Database
- SQLite at `db/strattest.db` (373 MB)
- `eod_prices`: 2,380 NSE stocks × 5 years daily OHLCV = 2.95M rows (2021-07-02 → 2026-07-02)
- `stock_fundamentals`: 2,367 stocks (99.5% coverage), 48 columns each (PE, ROE, sector, market cap, debt, growth, dividends, analyst targets, ownership, cash flows, etc.)
- All data sourced from yfinance (free, no API key needed)

### Data pipeline (`data_pipeline/`)
- `schema.sql` — DDL for both tables
- `backfill.py` — one-time backfill via yfinance (OHLCV in batches of 50, fundamentals with 1.5s delays and cooldowns)
- `daily_sync.py` — cron job: daily OHLCV appends, weekly fundamentals refresh
- `nse_tickers.csv` — full NSE equity list from nselib (2,380 symbols)

### Git
- 6 commits on `main`, no AI attribution
- `.gitignore` blocks `*.csv`, `db/*.db`, `__pycache__`, `.venv`

## What's NOT built yet

### Screener module (`screener/`)
Text-to-SQL for stock screening. Planned approach (no external libraries like Vanna):
1. Build prompt with: DDL + column glossary (what each column means) + few-shot examples + user question
2. LLM generates SQL
3. `sqlglot` validates syntax
4. Execute on READ-ONLY SQLite connection
5. Return results to user

Column glossary already exists in `schema.sql` comments.

### Strategy extractor (`strategy_extractor/`)
1. `youtube-transcript-api` → raw transcript from YouTube URL
2. LLM + `instructor` + Pydantic schema → structured `TradingStrategy` JSON (indicators, entry/exit conditions, timeframes)
3. JSON → `backtrader` Python class (deterministic codegen, not LLM)

### Backtest engine (`backtest_engine/`)
1. `backtrader` or `vectorbt` → run strategy against `eod_prices` data
2. Output: Sharpe ratio, max drawdown, win rate, profit factor, equity curve

## Key technical decisions
- **Python all the way** for MVP (Go would be premature)
- **yfinance** as single data source (consistent column names, adjusted prices for backtesting)
- **SQLite** for MVP (440 MB, zero ops); migrate to PostgreSQL+TimescaleDB when needed
- **No Vanna.ai** — simple prompt-based text-to-SQL instead (more control, fewer dependencies)
- **Rate limiting solved**: 1.5–2.3s jittered delays, 45s cooldowns every 300 calls

## Requirements
```
yfinance>=1.5.0
nselib>=2.5.0
pandas>=2.0.0
sqlglot>=25.0.0
```

## Next steps (priority order)
1. Build `screener/` module (text-to-SQL + DDL prompt + sqlglot validation)
2. Build `strategy_extractor/` module (YouTube transcript → TradingStrategy JSON)
3. Build `backtest_engine/` module (JSON → backtrader → metrics)
