"""Company detail endpoints."""

import logging
import sqlite3
import time

from fastapi import APIRouter, HTTPException, Query, Request

from common.database import get_connection
from common.types import (
    AnalystData,
    ChartDataPoint,
    ChartResponse,
    CompanyResponse,
    FinancialHealthData,
    GrowthData,
    OwnershipData,
    PeerEntry,
    PeerResponse,
    PriceData,
    ProfitabilityData,
    TechnicalsData,
    ValuationData,
)

router = APIRouter(prefix="/api", tags=["company"])
logger = logging.getLogger("strattest.backend.company")

CHART_SQL = "SELECT date, open, high, low, close, volume FROM eod_prices WHERE ticker = ? AND date >= ? ORDER BY date ASC"
CHART_SQL_ALL = "SELECT date, open, high, low, close, volume FROM eod_prices WHERE ticker = ? ORDER BY date ASC"


def _latest_eod(conn, ticker: str) -> dict:
    row = conn.execute(
        "SELECT date, open, high, low, close, volume FROM eod_prices WHERE ticker = ? ORDER BY date DESC LIMIT 1",
        [ticker],
    ).fetchone()
    if row is None:
        return {}
    return {
        "date": row["date"],
        "open": row["open"],
        "high": row["high"],
        "low": row["low"],
        "close": row["close"],
        "volume": row["volume"],
    }


def _prev_close(conn, ticker: str, latest_date: str | None) -> float | None:
    if latest_date is None:
        return None
    row = conn.execute(
        "SELECT close FROM eod_prices WHERE ticker = ? AND date < ? ORDER BY date DESC LIMIT 1",
        [ticker, latest_date],
    ).fetchone()
    return row["close"] if row else None


# ---------------------------------------------------------------------------
# GET /api/company/{ticker}
# ---------------------------------------------------------------------------

@router.get("/company/{ticker}", response_model=CompanyResponse)
def get_company(request: Request, ticker: str) -> CompanyResponse:
    start = time.perf_counter()
    db_path: str = request.app.state.db_path
    conn = get_connection(db_path, readonly=True)

    try:
        row = conn.execute(
            "SELECT * FROM stock_fundamentals WHERE ticker = ?", [ticker.upper()]
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")

        # Latest EOD price for today's action
        eod = _latest_eod(conn, ticker.upper())
        current_price = eod.get("close") or row["current_price"]
        prev_close_val = _prev_close(conn, ticker.upper(), eod.get("date"))

        # Compute day change
        change = None
        change_pct = None
        if current_price is not None and prev_close_val is not None and prev_close_val != 0:
            change = round(current_price - prev_close_val, 2)
            change_pct = round((change / prev_close_val) * 100, 2)

        # Technical computed fields
        price_52w_high = row["high_52w"]
        price_52w_low = row["low_52w"]
        pct_from_high = None
        pct_from_low = None
        if current_price is not None:
            if price_52w_high and price_52w_high != 0:
                pct_from_high = round(((price_52w_high - current_price) / price_52w_high) * 100, 1)
            if price_52w_low and price_52w_low != 0:
                pct_from_low = round(((current_price - price_52w_low) / price_52w_low) * 100, 1)

        # Promoter holdings from insiders, public = 100 - insider - institutional
        promoter = row["held_pct_insiders"]
        institutional = row["held_pct_institutions"]
        public = None
        if promoter is not None and institutional is not None:
            promoter = round(promoter * 100, 1)
            institutional = round(institutional * 100, 1)
            public = round(100 - promoter - institutional, 1)

        company = CompanyResponse(
            ticker=ticker.upper(),
            company_name=row["company_name"],
            sector=row["sector"],
            industry=row["industry"],
            exchange=row["exchange"],
            as_of_date=row["as_of_date"],
            price=PriceData(
                current=current_price,
                change=change,
                change_pct=change_pct,
                prev_close=prev_close_val,
                open=eod.get("open"),
                high=eod.get("high"),
                low=eod.get("low"),
                high_52w=price_52w_high,
                low_52w=price_52w_low,
                volume_today=eod.get("volume"),
            ),
            valuation=ValuationData(
                market_cap_crore=row["market_cap_crore"],
                pe_ratio=row["pe_ratio"],
                forward_pe=row["forward_pe"],
                pb_ratio=row["pb_ratio"],
                peg_ratio=row["peg_ratio"],
                price_to_sales=row["price_to_sales"],
                eps_ttm=row["eps_ttm"],
                eps_forward=row["eps_forward"],
                book_value_per_share=row["book_value_per_share"],
            ),
            profitability=ProfitabilityData(
                roe_pct=row["roe_pct"],
                roa_pct=row["roa_pct"],
                profit_margins_pct=row["profit_margins_pct"],
                operating_margins_pct=row["operating_margins_pct"],
                gross_margins_pct=row["gross_margins_pct"],
                ebitda_margins_pct=row["ebitda_margins_pct"],
            ),
            growth=GrowthData(
                revenue_growth_pct=row["revenue_growth_pct"],
                earnings_growth_pct=row["earnings_growth_pct"],
                earnings_quarterly_growth_pct=row["earnings_quarterly_growth_pct"],
            ),
            financial_health=FinancialHealthData(
                debt_to_equity=row["debt_to_equity"],
                current_ratio=row["current_ratio"],
                quick_ratio=row["quick_ratio"],
                payout_ratio=row["payout_ratio"],
                dividend_yield_pct=row["dividend_yield_pct"],
                five_year_avg_dividend_yield_pct=row["five_year_avg_dividend_yield_pct"],
                free_cashflow=row["free_cashflow"],
                operating_cashflow=row["operating_cashflow"],
                total_debt=row["total_debt"],
                total_revenue=row["total_revenue"],
                ebitda=row["ebitda"],
                total_cash_per_share=row["total_cash_per_share"],
            ),
            ownership=OwnershipData(
                promoter_pct=promoter,
                institutional_pct=institutional,
                public_pct=public,
            ),
            technicals=TechnicalsData(
                beta=row["beta"],
                price_pct_from_52w_high=pct_from_high,
                price_pct_from_52w_low=pct_from_low,
            ),
            analyst_coverage=AnalystData(
                recommendation=row["recommendation"],
                number_of_analysts=row["number_of_analysts"],
                target_mean=row["target_mean_price"],
                target_high=row["target_high_price"],
                target_low=row["target_low_price"],
            ),
        )
    finally:
        conn.close()

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "",
        extra={
            "method": "GET",
            "path": f"/api/company/{ticker}",
            "duration_ms": round(elapsed_ms, 1),
            "status": 200,
        },
    )

    return company


# ---------------------------------------------------------------------------
# GET /api/company/{ticker}/chart
# ---------------------------------------------------------------------------

@router.get("/company/{ticker}/chart", response_model=ChartResponse)
def get_company_chart(
    request: Request,
    ticker: str,
    range: str = Query("1y", pattern="^(1mo|6mo|1y|3y|5y|max)$"),
) -> ChartResponse:
    start = time.perf_counter()
    db_path: str = request.app.state.db_path
    conn = get_connection(db_path, readonly=True)

    try:
        exists = conn.execute(
            "SELECT 1 FROM stock_fundamentals WHERE ticker = ? LIMIT 1",
            [ticker.upper()],
        ).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")

        if range == "max":
            sql, params = CHART_SQL_ALL, [ticker.upper()]
        else:
            date_mod = {"1mo": "-1 months", "6mo": "-6 months", "1y": "-1 years", "3y": "-3 years", "5y": "-5 years"}[range]
            cutoff = conn.execute(
                "SELECT date(?, ?)", [sqlite3.datetime.date.today().isoformat(), date_mod]
            ).fetchone()[0]
            sql, params = CHART_SQL, [ticker.upper(), cutoff]

        rows = conn.execute(sql, params).fetchall()

        data = [
            ChartDataPoint(
                date=row["date"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
            )
            for row in rows
        ]
    finally:
        conn.close()

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "",
        extra={
            "method": "GET",
            "path": f"/api/company/{ticker}/chart",
            "duration_ms": round(elapsed_ms, 1),
            "status": 200,
            "range": range,
            "points": len(data),
        },
    )

    return ChartResponse(ticker=ticker.upper(), range=range, data=data)


# ---------------------------------------------------------------------------
# GET /api/company/{ticker}/peers
# ---------------------------------------------------------------------------

@router.get("/company/{ticker}/peers", response_model=PeerResponse)
def get_company_peers(
    request: Request,
    ticker: str,
    limit: int = Query(10, ge=1, le=20),
) -> PeerResponse:
    start = time.perf_counter()
    db_path: str = request.app.state.db_path
    conn = get_connection(db_path, readonly=True)

    try:
        row = conn.execute(
            "SELECT sector FROM stock_fundamentals WHERE ticker = ?",
            [ticker.upper()],
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")

        sector = row["sector"]
        if sector is None:
            return PeerResponse(ticker=ticker.upper(), peers=[])

        peers_rows = conn.execute(
            """SELECT ticker, company_name, current_price, market_cap_crore,
                      pe_ratio, roe_pct, revenue_growth_pct, debt_to_equity
               FROM stock_fundamentals
               WHERE sector = ? AND ticker != ?
               ORDER BY market_cap_crore DESC
               LIMIT ?""",
            [sector, ticker.upper(), limit],
        ).fetchall()

        peers = [
            PeerEntry(
                ticker=pr["ticker"],
                company_name=pr["company_name"],
                current_price=pr["current_price"],
                market_cap_crore=pr["market_cap_crore"],
                pe_ratio=pr["pe_ratio"],
                roe_pct=pr["roe_pct"],
                revenue_growth_pct=pr["revenue_growth_pct"],
                debt_to_equity=pr["debt_to_equity"],
            )
            for pr in peers_rows
        ]
    finally:
        conn.close()

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "",
        extra={
            "method": "GET",
            "path": f"/api/company/{ticker}/peers",
            "duration_ms": round(elapsed_ms, 1),
            "status": 200,
            "peer_count": len(peers),
        },
    )

    return PeerResponse(ticker=ticker.upper(), peers=peers)
