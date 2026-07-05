"""Filter options and health-check endpoints."""

import logging
import os
from datetime import date, datetime

from fastapi import APIRouter, Request

from backend.cache import route_cache
from backend.limiter import limiter
from common.database import get_connection
from common.filters import sort_columns_ui
from common.types import FilterOptions, HealthResponse

router = APIRouter(prefix="/api", tags=["filters"])
logger = logging.getLogger("screener_ai.backend.filters")


@router.get("/filters/options", response_model=FilterOptions)
@limiter.limit("100/minute")
def filter_options(request: Request) -> FilterOptions:
    cached = route_cache.get("filter_options")
    if cached is not None:
        return cached

    db_path = request.app.state.db_path
    with get_connection(db_path, readonly=True) as conn:
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

    result = FilterOptions(
        sectors=sectors,
        industries=industries,
        sort_columns=sort_columns_ui(),
    )
    route_cache.set("filter_options", result, ttl=300)
    return result


@router.get("/health", response_model=HealthResponse)
def health_check(request: Request) -> HealthResponse:
    cached = route_cache.get("health")
    if cached is not None:
        return cached

    db_path = request.app.state.db_path
    try:
        with get_connection(db_path, readonly=True) as conn:
            latest_row = conn.execute(
                "SELECT MAX(date) FROM eod_prices"
            ).fetchone()
            latest = latest_row[0] if latest_row else None

            count_row = conn.execute(
                "SELECT COUNT(*) FROM stock_fundamentals"
            ).fetchone()
            count = count_row[0] if count_row else 0

        db_size_mb = (
            os.path.getsize(db_path) / (1024 * 1024)
            if os.path.exists(db_path)
            else 0
        )

        stale = False
        if latest:
            latest_date = datetime.strptime(latest, "%Y-%m-%d").date()
            stale = (date.today() - latest_date).days > 2

        result = HealthResponse(
            status="ok",
            latest_data_date=latest,
            stock_count=count,
            db_size_mb=round(db_size_mb, 1),
            stale=stale,
        )
        route_cache.set("health", result, ttl=60)
        return result
    except Exception:
        logger.exception("Health check failed")
        return HealthResponse(status="error")
