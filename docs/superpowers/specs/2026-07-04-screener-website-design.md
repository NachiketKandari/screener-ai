# Screener Website — Design Spec

## Overview

Web-based stock screener for Indian markets (NSE). User applies structured filters or natural language queries, backend executes SQL against a SQLite database, frontend renders results in a fast, paginated, sortable table. Hybrid approach: filter-based for speed (no LLM cost), NL box for flexibility.

## Architecture

```
                    Vercel                          Hostinger VPS
               ┌──────────────┐              ┌──────────────────┐
               │  Next.js FE  │──HTTPS──────▶│  FastAPI BE      │
               │  (static +   │              │  (port 8000)     │
               │   CSR)       │              │       │          │
               └──────────────┘              │  ┌────┴─────┐    │
                                             │  │ SQLite   │    │
                 Nginx reverse proxy ◀───────│  │(read-only│    │
                 + Let's Encrypt            │  │ queries) │    │
                                             │  └──────────┘    │
                                             │                  │
                                             │  cron (6:30 PM): │
                                             │  daily_sync.py   │
                                             └──────────────────┘
```

- **Frontend**: Next.js App Router, deployed to Vercel. Client-side rendering for the screener page (no SSR needed — data is live-filtered). Calls FastAPI directly from the browser.
- **Backend**: FastAPI on Hostinger VPS behind Nginx. Read-only SQLite connection per request. LLM calls go through the backend (API key stays server-side).
- **No Next.js API routes**: The frontend is a pure client that talks to FastAPI. Simpler, one less layer.

## Directory Structure

```
strattest/
├── common/
│   ├── __init__.py
│   ├── types.py           # Pydantic models: FilterSpec, ScreenResponse
│   ├── filters.py         # FilterSpec → SQL builder (pure functions)
│   └── database.py        # Connection factory (swap point for Postgres)
├── backend/
│   ├── __init__.py
│   ├── main.py            # App factory, CORS, lifespan, logging setup
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── screen.py      # GET /api/screen, POST /api/screen/nl
│   │   └── filters.py     # GET /api/filters/options
│   ├── logging.conf        # Logging configuration
│   └── tests/
│       ├── __init__.py
│       ├── test_screen.py
│       └── test_filters.py
├── frontend/
│   ├── app/
│   │   ├── layout.tsx     # Root layout (minimal, no heavy deps)
│   │   ├── page.tsx       # Screener page
│   │   └── globals.css
│   ├── components/
│   │   ├── filter-bar.tsx         # All filter controls
│   │   ├── natural-language.tsx   # NL input box
│   │   ├── results-table.tsx      # Virtualized/paginated table
│   │   ├── skeleton-table.tsx     # Loading skeleton
│   │   ├── summary-bar.tsx        # "N stocks match" + sort selector
│   │   └── ui/                    # shadcn/ui primitives (generated)
│   ├── lib/
│   │   ├── api.ts                 # FastAPI client (fetch wrappers)
│   │   ├── types.ts               # Mirror of common/types.py
│   │   └── logger.ts              # Structured frontend logger
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
├── data_pipeline/          # Existing — unchanged
├── screener/               # Existing — reused by backend routes
└── db/                     # SQLite DB (gitignored)
```

## API Contract

### `GET /api/screen`

Query parameters map 1:1 with `FilterSpec` fields. Examples:

```
GET /api/screen?sectors=Technology&sectors=Financial+Services&pe_min=0&pe_max=15&roe_min=20&sort_by=market_cap_crore&sort_dir=desc&limit=50&offset=0
```

All filters optional. If none provided, returns all stocks sorted by market cap.

**Response** (200):
```json
{
  "columns": ["ticker", "company_name", "sector", "current_price", "pe_ratio", "roe_pct", "market_cap_crore"],
  "rows": [
    ["HDFCBANK", "HDFC Bank Ltd.", "Financial Services", 1721.35, 19.2, 15.8, 1300000.0],
    ...
  ],
  "total_count": 238,
  "query_time_ms": 12.4,
  "warnings": []
}
```

**Response** (422): validation error — malformed ranges, unknown sort column, etc.

**Response** (500): server error with `detail` string.

### `POST /api/screen/nl`

```json
// Request
{ "query": "banks with PE under 15 and ROE above 20" }

// Response: same shape as GET /api/screen
{ "columns": [...], "rows": [...], ... }
```

The backend may additionally return `"interpreted_as": "..."` — a human-readable summary of what the LLM understood.

If the LLM fails to parse the query, returns 422 with `detail` explaining the ambiguity.

### `GET /api/filters/options`

```json
{
  "sectors": ["Technology", "Financial Services", "Healthcare", ...],
  "industries": ["Software - Infrastructure", "Banks - Regional", ...],
  "sort_columns": [
    {"value": "market_cap_crore", "label": "Market Cap"},
    {"value": "pe_ratio", "label": "P/E Ratio"},
    {"value": "roe_pct", "label": "ROE"},
    {"value": "current_price", "label": "Current Price"},
    {"value": "revenue_growth_pct", "label": "Revenue Growth"}
  ]
}
```

Hit once on page load, cached for session.

### `GET /api/health`

```json
{
  "status": "ok",
  "latest_data_date": "2026-07-04",
  "stock_count": 2380,
  "db_size_mb": 373
}
```

Shown in footer: "Data as of July 4, 2026 · 2,380 stocks".

## FilterSpec Schema

```python
class FilterSpec(BaseModel):
    # Identity
    sectors: list[str] | None = None
    industries: list[str] | None = None
    ticker: str | None = None          # single symbol search
    search: str | None = None          # LIKE '%text%' on company_name

    # Valuation
    pe_min: float | None = None
    pe_max: float | None = None
    market_cap_min: float | None = None
    market_cap_max: float | None = None
    pb_min: float | None = None
    pb_max: float | None = None
    peg_max: float | None = None
    price_to_sales_max: float | None = None

    # Profitability
    roe_min: float | None = None
    roa_min: float | None = None
    profit_margin_min: float | None = None
    operating_margin_min: float | None = None

    # Growth
    revenue_growth_min: float | None = None
    earnings_growth_min: float | None = None

    # Financial health
    debt_to_equity_max: float | None = None
    current_ratio_min: float | None = None
    dividend_yield_min: float | None = None

    # Ownership
    promoter_holding_min: float | None = None   # held_pct_insiders

    # Price-based (require JOIN with eod_prices)
    price_pct_from_52w_high_max: float | None = None
    price_pct_from_52w_low_min: float | None = None
    price_above_50dma: bool = False
    price_above_200dma: bool = False
    volume_above_20d_avg: bool = False

    # Sorting & pagination
    sort_by: str = "market_cap_crore"
    sort_dir: Literal["asc", "desc"] = "desc"
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
```

## Filter → SQL Builder

`common/filters.py` — pure functions, no I/O. The core of the screener.

```python
def build_screen_query(spec: FilterSpec) -> tuple[str, dict]:
    """
    Returns (sql, params) for parameterized execution.
    Always starts from stock_fundamentals.
    JOINs eod_prices only when price-based conditions are present.
    All nullable columns get IS NOT NULL guards when used in WHERE.
    Defaults to LIMIT 50, OFFSET 0 sorted by market cap desc.
    """

def build_count_query(spec: FilterSpec) -> tuple[str, dict]:
    """Same WHERE but SELECT COUNT(*) for pagination total."""

def resolve_sort(sort_by: str) -> str:
    """Validate sort column against whitelist, return safe column expression."""
```

### Performance

- All frequently filtered columns are indexed on `stock_fundamentals`. A migration in `data_pipeline/` adds them:

```sql
CREATE INDEX IF NOT EXISTS idx_fund_sector ON stock_fundamentals(sector);
CREATE INDEX IF NOT EXISTS idx_fund_industry ON stock_fundamentals(industry);
CREATE INDEX IF NOT EXISTS idx_fund_pe ON stock_fundamentals(pe_ratio);
CREATE INDEX IF NOT EXISTS idx_fund_roe ON stock_fundamentals(roe_pct);
CREATE INDEX IF NOT EXISTS idx_fund_mcap ON stock_fundamentals(market_cap_crore);
CREATE INDEX IF NOT EXISTS idx_fund_rev_growth ON stock_fundamentals(revenue_growth_pct);
CREATE INDEX IF NOT EXISTS idx_fund_debt_eq ON stock_fundamentals(debt_to_equity);
```

- Price-based conditions (DMA, volume avg) use CTEs that scan the last 200 days of `eod_prices` per ticker (enough for 200 DMA). The existing `idx_eod_ticker` and `idx_eod_date` indexes make this a fast range scan.
- `price_pct_from_52w_high/low` filters use `stock_fundamentals.high_52w` / `low_52w` — no JOIN needed.
- Pagination via `LIMIT/OFFSET` on filtered + sorted results. For any screener, the filter set is small enough (< 500 rows typically) that this is fast even without keyset pagination.

### Sort whitelist

```python
SORT_COLUMNS: dict[str, str] = {
    "market_cap_crore": "market_cap_crore",
    "pe_ratio": "pe_ratio",
    "roe_pct": "roe_pct",
    "current_price": "current_price",
    "revenue_growth_pct": "revenue_growth_pct",
    "earnings_growth_pct": "earnings_growth_pct",
    "debt_to_equity": "debt_to_equity",
    "dividend_yield_pct": "dividend_yield_pct",
    "pb_ratio": "pb_ratio",
    "eps_ttm": "eps_ttm",
}
```
`resolve_sort()` looks up the input in this dict. Unknown keys raise `ValueError` → 422 response. No raw column names in SQL ORDER BY.

## Backend

### Logging

Every request logs: method, path, query params (no API keys), duration, status code, row count. Structured JSON logs to stdout (systemd journal).

```python
# Log format
{"time": "2026-07-04T18:30:01.123Z", "level": "INFO", "method": "GET",
 "path": "/api/screen", "params": {"sectors": ["Technology"], "pe_max": "15"},
 "duration_ms": 14.2, "status": 200, "row_count": 42}
```

ERROR level for: database errors, LLM failures, unexpected exceptions (with traceback).

### Error responses

All errors follow the same shape:
```json
{"detail": "Human-readable error message"}
```

No stack traces in responses. No internal state leaked.

### Input validation

- `sort_by` checked against a whitelist of known columns — not passed raw to SQL
- `sort_dir` must be "asc" or "desc"
- Numeric ranges: min <= max (when both provided)
- `limit` capped at 500
- Sector/industry values validated against known list from `GET /api/filters/options`

## Frontend

### Performance & UX

**Non-negotiable: no laggy tables.** Every loading state has a visual indicator:

| State | What user sees |
|---|---|
| Initial page load | Skeleton table (4 rows of pulsing gray bars) + skeleton filter bar |
| Filter change | Skeleton table overlays existing results (preserves layout, no jump) |
| Natural language submit | Spinner inside the NL box + "translating..." text |
| Column sort (in-memory) | Instant (no API call for already-loaded page) |
| Pagination | Skeleton table over results |
| API error | Toast notification at bottom-right, existing results preserved |

Column sorting for the currently loaded page is done client-side (no network request). Only changing filters or paginating triggers an API call.

### Component tree

```
<ScreenerPage>
  <NaturalLanguageInput />          ← text area + submit button
  <FilterBar>
    <SectorSelect />                ← multi-select combobox (searchable)
    <RangeFilter label="P/E" />     ← two inputs: min, max
    <RangeFilter label="ROE %" />
    <RangeFilter label="Market Cap" />
    ...                              ← collapsible advanced section
  </FilterBar>
  <SummaryBar />                    ← "N matches · sorted by X"
  <ResultsTable />                  ← paginated, sortable
  <DataFreshnessFooter />           ← "Data as of ..."
</ScreenerPage>
```

### Filter behavior

- Changing any filter **debounces 400ms** before firing the API call
- Filter state lives in a `useReducer` — a single `FilterSpec` object. URL is the source of truth (filters serialized as search params, shareable/bookmarkable).
- Sectors: fetched from `/api/filters/options` on mount, rendered as a searchable multi-select
- Ranges: two number inputs (min/max) laid out horizontally
- "Add filter" button opens a dropdown of available filters not yet shown
- "Clear all" resets to default (all stocks, sorted by market cap)

### Table behavior

- Uses shadcn/ui `Table` component
- Columns shown by default: Ticker, Company, Sector, CMP (₹), P/E, ROE %, Market Cap (Cr), Revenue Growth %
- Click a column header to sort (client-side for current page; shows "Sorting..." and re-fetches from API for full dataset)
- Each row has a subtle hover state
- Ticker and Company name are sticky-left on narrow screens
- Empty state: "No stocks match your filters. Try broadening your criteria."

### Frontend logging

```typescript
// lib/logger.ts
const logger = {
  info(msg: string, data?: Record<string, unknown>): void,
  warn(msg: string, data?: Record<string, unknown>): void,
  error(msg: string, err?: Error, data?: Record<string, unknown>): void,
}
```

Key events logged:
- Filter changes (which filters, not values)
- API call start + duration + status
- NL query submitted (the text)
- Errors (API errors, unexpected exceptions)

In production, logs go to `console.info/warn/error` — Vercel captures these. In development, they're pretty-printed with timestamps.

## Ingestion Pipeline

### Cron schedule

```
# /etc/cron.d/strattest on Hostinger VPS
# Run 6:30 PM IST Mon-Fri (market closes 3:30 PM, yfinance data ready by ~6 PM)
30 18 * * 1-5 root cd /opt/strattest && /opt/strattest/.venv/bin/python data_pipeline/daily_sync.py >> /var/log/strattest/sync.log 2>&1
```

### Logging

Replace `print()` calls in `daily_sync.py` with `logging` module:
```python
import logging
logger = logging.getLogger("strattest.daily_sync")
```

Log format: `{"time": "...", "level": "INFO", "component": "daily_sync", "msg": "OHLCV sync: 2026-07-03 → 2026-07-04", "rows": 2380}`

INFO level: sync start/end, row counts, fundamentals refresh status.
WARNING level: batch failures with retry, individual stock fetch errors.
ERROR level: database errors, unrecoverable failures.

### Idempotency

- OHLCV: `INSERT OR REPLACE` handles re-runs safely (PRIMARY KEY on ticker+date)
- Fundamentals: `INSERT OR REPLACE` by ticker
- `get_last_date()` check prevents redundant OHLCV pulls

### Health check integration

Backend's `/api/health` reads `MAX(date)` from eod_prices. If that date is more than 2 trading days old, include `"stale": true` in the response so the frontend can warn users.

## shadcn/ui Components Used

```bash
npx shadcn@latest add table input select button badge command popover drawer
```

- `Table` — results table
- `Input` — number inputs for ranges
- `Select` — sort dropdown, single-select filters
- `Button` — submit, clear, pagination
- `Badge` — active filter pills
- `Command` — searchable sector/industry multi-select
- `Popover` — "Add filter" dropdown
- `Drawer` — mobile filter panel

## Development & Deployment

### Local dev

```bash
# Backend
cd backend && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

### Production

**Frontend (Vercel):**
- `NEXT_PUBLIC_API_URL=https://api.strattest.com`
- `vercel --prod` from `frontend/`

**Backend (Hostinger VPS):**
- Nginx reverse proxy: `api.strattest.com` → `localhost:8000`
- Systemd service: `strattest-api.service` (auto-restart, env file)
- Cron: `/etc/cron.d/strattest` for daily sync

## What's Explicitly Deferred

- Click-to-view stock detail page (v2)
- Stock chart with OHLCV history (v2)
- User accounts / saved screens (v2)
- PostgreSQL migration (when traffic demands it)
- Minute-level data (not available via free sources, not needed for fundamental screening)
