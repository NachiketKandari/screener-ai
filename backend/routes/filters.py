"""Filter options and health-check endpoints."""

import logging
import os
from datetime import date, datetime

from fastapi import APIRouter, Request

from backend.limiter import limiter
from common.database import get_connection
from common.types import FilterOptions, HealthResponse

router = APIRouter(prefix="/api", tags=["filters"])
logger = logging.getLogger("strattest.backend.filters")


SORT_COLUMNS_UI: list[dict] = [
    {"value": "market_cap_crore", "label": "Market Cap"},
    {"value": "pe_ratio", "label": "P/E Ratio"},
    {"value": "roe_pct", "label": "ROE"},
    {"value": "current_price", "label": "Current Price"},
    {"value": "revenue_growth_pct", "label": "Revenue Growth"},
    {"value": "earnings_growth_pct", "label": "Earnings Growth"},
    {"value": "debt_to_equity", "label": "Debt to Equity"},
    {"value": "dividend_yield_pct", "label": "Dividend Yield"},
    {"value": "pb_ratio", "label": "P/B Ratio"},
    {"value": "eps_ttm", "label": "EPS (TTM)"},
]


@router.get("/filters/options", response_model=FilterOptions)
@limiter.limit("100/minute")
def filter_options(request: Request) -> FilterOptions:
    db_path = request.app.state.db_path
    conn = get_connection(db_path, readonly=True)
    try:
        sectors = [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT sector FROM stock_fundamentals "
                "WHERE sector IS NOT NULL AND sector != '' AND sector != 'None' "
                "ORDER BY sector"
            ).fetchall()
        ]
        industries = [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT industry FROM stock_fundamentals "
                "WHERE industry IS NOT NULL AND industry != '' AND industry != 'None' "
                "ORDER BY industry"
            ).fetchall()
        ]
    finally:
        conn.close()

    return FilterOptions(
        sectors=sectors,
        industries=industries,
        sort_columns=SORT_COLUMNS_UI,
    )


@router.get("/health", response_model=HealthResponse)
def health_check(request: Request) -> HealthResponse:
    db_path = request.app.state.db_path
    try:
        conn = get_connection(db_path, readonly=True)
        try:
            latest_row = conn.execute(
                "SELECT MAX(date) FROM eod_prices"
            ).fetchone()
            latest = latest_row[0] if latest_row else None

            count_row = conn.execute(
                "SELECT COUNT(*) FROM stock_fundamentals"
            ).fetchone()
            count = count_row[0] if count_row else 0
        finally:
            conn.close()

        db_size_mb = (
            os.path.getsize(db_path) / (1024 * 1024)
            if os.path.exists(db_path)
            else 0
        )

        stale = False
        if latest:
            latest_date = datetime.strptime(latest, "%Y-%m-%d").date()
            stale = (date.today() - latest_date).days > 2

        return HealthResponse(
            status="ok",
            latest_data_date=latest,
            stock_count=count,
            db_size_mb=round(db_size_mb, 1),
            stale=stale,
        )
    except Exception:
        logger.exception("Health check failed")
        return HealthResponse(status="error")
