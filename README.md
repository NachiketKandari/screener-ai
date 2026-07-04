# Strattest

A stock screening and analysis platform for Indian stocks on the NSE (National Stock Exchange). Screen stocks using structured filters or natural language, explore company fundamentals with interactive charts, and compare peers — all backed by a local SQLite database with 5 years of daily OHLCV data and ~40 fundamental metrics.

## Features

### Stock Screener
- **30+ filter fields** across 7 categories: Identity, Valuation, Profitability, Growth, Financial Health, Ownership, and Price & Technical
- **Filter chips UI** — add, configure, and remove individual filter conditions with support for numeric ranges, min/max thresholds, multi-select enums, booleans, and text search
- **Natural language screening** — type a query like _"banks with PE under 15 and ROE above 20%"_ and an LLM translates it to SQL
- Results table with column sorting and pagination
- Data freshness footer showing the latest data date

### Company Detail Pages (`/company/{ticker}`)
- **Overview tab** — interactive OHLCV chart with line/candlestick toggle and 1M to MAX range selector, plus a metrics dashboard
- **Chart tab** — expanded full-width chart view
- **Metrics tab** — full metrics dashboard across Valuation, Profitability, Growth & Cash Flow
- **Peers tab** — side-by-side comparison with same-sector companies (market cap, P/E, ROE, revenue growth, debt/equity)
- **Analysts tab** — analyst recommendations, consensus target price, and coverage count
- **Info popovers** on every metric with plain-English descriptions
- Color-coded signal indicators (green/red) for key metrics like ROE and revenue growth
- Stock price with day change, 52-week range, and volume data

### Data Pipeline
- **~2,300 NSE stocks** imported from yfinance
- **5 years of daily OHLCV data** (open, high, low, close, volume)
- **~40 fundamental metrics** per stock: valuation, profitability, growth, financial health, ownership, technicals, and analyst targets
- `backfill.py` — one-time bulk download (handle rate limits with jittered delays)
- `daily_sync.py` — cron-friendly incremental updates (daily OHLCV append, weekly fundamentals refresh)
- `extend_history.py` — extend historical data further back

### CLI Screener
```bash
python -m screener "stocks with PE < 15, ROE > 20%, and market cap above 1000 crore"
```
A standalone text-to-SQL tool using DeepSeek V4 Flash with sqlglot validation and retry-on-failure.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python), uvicorn |
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Charts | lightweight-charts v5 (line + candlestick) |
| UI Components | Radix UI (Popover, Dialog, Select), Lucide icons |
| Database | SQLite (single-file, ~370 MB for full dataset) |
| Data source | yfinance (free, no API key required) |
| NLP / LLM | DeepSeek V4 Flash (via OpenRouter-compatible API) |
| SQL tooling | sqlglot (query validation for LLM-generated SQL) |

## Project Structure

```
strattest/
├── backend/                  FastAPI backend
│   ├── main.py              App factory, CORS, logging
│   ├── routes/
│   │   ├── screen.py         GET /api/screen (structured) + POST /api/screen/nl (NL)
│   │   ├── company.py        GET /api/company/{ticker}, /chart, /peers
│   │   └── filters.py        GET /api/filters/options + GET /api/health
│   └── tests/                Backend test suite (conftest.py + per-route tests)
├── frontend/                 Next.js 14 frontend
│   ├── app/
│   │   ├── page.tsx          Home page — screener with filters + NL input
│   │   ├── layout.tsx         Root layout
│   │   └── company/[ticker]/page.tsx  Company detail page with tabs
│   ├── components/
│   │   ├── company/           CompanyHeader, CompanyChart, MetricsDashboard,
│   │   │                      MetricCard, PeerComparison, AnalystCoverage,
│   │   │                      CompanyNavTabs, Skeleton, ErrorState
│   │   ├── filter-bar.tsx     Filter bar with chip add/remove
│   │   ├── filter-chip.tsx    Individual filter chip UI
│   │   ├── add-filter-dropdown.tsx  Category-grouped filter picker
│   │   ├── natural-language.tsx     Natural language query input
│   │   ├── results-table.tsx  Sortable, paginated results table
│   │   ├── summary-bar.tsx    Result count, sort dropdown
│   │   └── data-freshness-footer.tsx  DB freshness indicator
│   └── lib/
│       ├── api.ts             Frontend API client (typed fetch wrappers)
│       ├── types.ts           TypeScript types for all API responses
│       ├── filter-registry.ts  30+ filter metric definitions + serialization
│       ├── glossary.ts        Plain-English metric descriptions for popovers
│       └── format.ts          Number/percent/price formatting utilities
├── common/                   Shared Python modules
│   ├── database.py           SQLite connection helper
│   ├── filters.py            Screen query builder (FilterSpec → SQL)
│   ├── types.py              Pydantic models shared by backend and screener
│   └── test_filters.py       Tests for query builder
├── screener/                 Standalone text-to-SQL CLI module
│   ├── screener.py           Core engine (LLM → SQL → execute)
│   ├── prompt_builder.py     System prompt with schema + glossary
│   ├── config.py             Configuration loading
│   ├── cli.py                CLI entry point
│   └── glossary.py           Column descriptions for the LLM prompt
├── data_pipeline/            Data ingestion
│   ├── backfill.py           Bulk OHLCV + fundamentals download
│   ├── daily_sync.py         Incremental daily updates
│   ├── extend_history.py     Extend historical price data
│   ├── schema.sql            Database schema (eod_prices + stock_fundamentals)
│   └── nse_tickers.csv       NSE ticker list (2,300+ stocks)
├── db/                       SQLite database (gitignored)
└── requirements.txt          Python dependencies
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- DeepSeek API key (for natural language screener; structured screener works without it)

### 1. Clone and set up Python

```bash
git clone <repo-url>
cd strattest
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment

Create `.env` at the project root:

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

### 3. Build the database

The database is gitignored (approximately 370 MB). Build it with:

```bash
python data_pipeline/backfill.py
```

This takes roughly 2 hours for the full OHLCV + fundamentals download. Yahoo rate limits are handled with jittered delays.

### 4. Set up and run the frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Application

Start the backend (serves on port 8000):

```bash
uvicorn backend.main:app --reload --port 8000
```

Start the frontend dev server (serves on port 3000):

```bash
cd frontend && npm run dev
```

Open `http://localhost:3000` in your browser.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/screen` | Structured screener with 30+ query params |
| `POST` | `/api/screen/nl` | Natural language screening (`{"query": "..."}`) |
| `GET` | `/api/filters/options` | Available sectors, industries, sort columns |
| `GET` | `/api/health` | Database health (latest date, stock count, size) |
| `GET` | `/api/company/{ticker}` | Full company profile and fundamentals |
| `GET` | `/api/company/{ticker}/chart?range=1y` | OHLCV price data (range: 1mo, 6mo, 1y, 3y, 5y, max) |
| `GET` | `/api/company/{ticker}/peers?limit=10` | Same-sector peer comparison |

## Data Sync (ongoing updates)

```bash
# Daily OHLCV append + weekly fundamentals refresh
python data_pipeline/daily_sync.py
```

## Running Tests

### Python tests

```bash
python -m pytest screener/ -v
python -m pytest common/ -v
python -m pytest backend/tests/ -v
```

### Frontend build check

```bash
cd frontend && npm run build
```

## License

Proprietary. All rights reserved.
