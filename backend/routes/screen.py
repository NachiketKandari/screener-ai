"""Structured and natural-language screening endpoints."""

import logging
import os
import time
from types import SimpleNamespace
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from common.database import get_connection
from common.filters import build_count_query, build_screen_query
from common.types import (
    FilterSpec,
    NLScreenRequest,
    NLScreenResponse,
    ScreenResponse,
)

router = APIRouter(prefix="/api", tags=["screen"])
logger = logging.getLogger("strattest.backend.screen")


# ---------------------------------------------------------------------------
# GET /api/screen  –  structured screening
# ---------------------------------------------------------------------------

@router.get("/screen", response_model=ScreenResponse)
def screen_stocks(
    request: Request,
    sectors: list[str] | None = Query(None),
    industries: list[str] | None = Query(None),
    ticker: str | None = None,
    search: str | None = None,
    pe_min: float | None = None,
    pe_max: float | None = None,
    market_cap_min: float | None = None,
    market_cap_max: float | None = None,
    pb_min: float | None = None,
    pb_max: float | None = None,
    peg_max: float | None = None,
    price_to_sales_max: float | None = None,
    roe_min: float | None = None,
    roa_min: float | None = None,
    profit_margin_min: float | None = None,
    operating_margin_min: float | None = None,
    revenue_growth_min: float | None = None,
    earnings_growth_min: float | None = None,
    debt_to_equity_max: float | None = None,
    current_ratio_min: float | None = None,
    dividend_yield_min: float | None = None,
    promoter_holding_min: float | None = None,
    price_pct_from_52w_high_max: float | None = None,
    price_pct_from_52w_low_min: float | None = None,
    price_above_50dma: bool = False,
    price_above_200dma: bool = False,
    volume_above_20d_avg: bool = False,
    sort_by: str = "market_cap_crore",
    sort_dir: str = "desc",
    limit: int = 50,
    offset: int = 0,
) -> ScreenResponse:
    start = time.perf_counter()

    # Build FilterSpec – validates types and range constraints
    try:
        spec = FilterSpec(
            sectors=sectors,
            industries=industries,
            ticker=ticker,
            search=search,
            pe_min=pe_min,
            pe_max=pe_max,
            market_cap_min=market_cap_min,
            market_cap_max=market_cap_max,
            pb_min=pb_min,
            pb_max=pb_max,
            peg_max=peg_max,
            price_to_sales_max=price_to_sales_max,
            roe_min=roe_min,
            roa_min=roa_min,
            profit_margin_min=profit_margin_min,
            operating_margin_min=operating_margin_min,
            revenue_growth_min=revenue_growth_min,
            earnings_growth_min=earnings_growth_min,
            debt_to_equity_max=debt_to_equity_max,
            current_ratio_min=current_ratio_min,
            dividend_yield_min=dividend_yield_min,
            promoter_holding_min=promoter_holding_min,
            price_pct_from_52w_high_max=price_pct_from_52w_high_max,
            price_pct_from_52w_low_min=price_pct_from_52w_low_min,
            price_above_50dma=price_above_50dma,
            price_above_200dma=price_above_200dma,
            volume_above_20d_avg=volume_above_20d_avg,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Build SQL
    try:
        sql, sql_params = build_screen_query(spec)
        count_sql, count_params = build_count_query(spec)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    db_path: str = request.app.state.db_path
    conn = get_connection(db_path, readonly=True)
    try:
        cursor = conn.execute(sql, sql_params)
        columns = (
            [d[0] for d in cursor.description] if cursor.description else []
        )
        rows = [list(row) for row in cursor.fetchall()]

        count_cursor = conn.execute(count_sql, count_params)
        count_row = count_cursor.fetchone()
        total_count: int = count_row[0] if count_row else 0
    finally:
        conn.close()

    elapsed_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "",
        extra={
            "method": "GET",
            "path": "/api/screen",
            "duration_ms": round(elapsed_ms, 1),
            "status": 200,
            "row_count": len(rows),
        },
    )

    return ScreenResponse(
        columns=columns,
        rows=rows,
        total_count=total_count,
        query_time_ms=round(elapsed_ms, 1),
        warnings=[],
    )


# ---------------------------------------------------------------------------
# POST /api/screen/nl  –  natural-language screening
# ---------------------------------------------------------------------------

@router.post("/screen/nl", response_model=NLScreenResponse)
def screen_natural_language(
    request: Request, body: NLScreenRequest
) -> NLScreenResponse:
    start = time.perf_counter()
    db_path: str = request.app.state.db_path

    # Check for API key before attempting to use the screener
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Natural language screening unavailable: DEEPSEEK_API_KEY not set",
        )

    from screener.screener import QueryError, Screener  # noqa: E402

    # Build a config-like object the Screener can consume directly.
    # (We cannot use screener.config.Config because it forces a relative
    # db_path computation; we already have an absolute path from app.state.)
    cfg = SimpleNamespace(
        api_key=api_key,
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        model=os.environ.get("STRATTEST_MODEL", "deepseek-v4-flash"),
        db_path_absolute=db_path,
        query_timeout=30,
        max_rows=500,
    )

    screener = Screener(cfg)
    try:
        columns, rows = screener.query(body.query)
    except QueryError as exc:
        logger.warning(
            "",
            extra={"query": body.query, "error": str(exc)},
        )
        raise HTTPException(status_code=422, detail=str(exc))

    elapsed_ms = (time.perf_counter() - start) * 1000

    return NLScreenResponse(
        columns=list(columns),
        rows=[list(row) for row in rows],
        total_count=len(rows),
        query_time_ms=round(elapsed_ms, 1),
        warnings=screener.warnings,
        interpreted_as=None,
    )
