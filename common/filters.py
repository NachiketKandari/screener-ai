"""SQL builder for the stock screener.

Pure functions -- no I/O, no side-effects.
Every function returns (sql: str, params: dict) for parameterised execution.
"""

from __future__ import annotations

from typing import Any

from common.types import FilterSpec

# -- Whitelist of sortable columns ----------------------------------------
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


def resolve_sort(sort_by: str) -> str:
    """Validate *sort_by* against the whitelist and return the safe column name.

    Raises:
        ValueError: if *sort_by* is not in ``SORT_COLUMNS``.
    """
    if sort_by not in SORT_COLUMNS:
        raise ValueError(
            f"Unknown sort column: {sort_by}.  "
            f"Valid columns: {', '.join(sorted(SORT_COLUMNS))}"
        )
    return SORT_COLUMNS[sort_by]


# -- Helpers ---------------------------------------------------------------

def _add_in_clause(
    conditions: list[str],
    params: dict[str, Any],
    column: str,
    values: list[str],
    param_prefix: str,
) -> None:
    """Append ``column IN (:p0, :p1, ...)`` using parameterised placeholders."""
    placeholders: list[str] = []
    for i, val in enumerate(values):
        key = f"{param_prefix}_{i}"
        placeholders.append(f":{key}")
        params[key] = val
    conditions.append(f"sf.{column} IN ({', '.join(placeholders)})")


def _add_min_guard(
    qp: _QueryParts,
    column: str,
    value: float,
    param_name: str,
    null_guard: str,
) -> None:
    """Add a ``col >= :val`` condition plus its NULL guard (deduplicated)."""
    qp.params[param_name] = value
    qp.conditions.append(f"sf.{column} >= :{param_name}")
    if column not in qp._guarded:
        qp.conditions.append(null_guard)
        qp._guarded.add(column)


def _add_max_guard(
    qp: _QueryParts,
    column: str,
    value: float,
    param_name: str,
    null_guard: str,
) -> None:
    """Add a ``col <= :val`` condition plus its NULL guard (deduplicated)."""
    qp.params[param_name] = value
    qp.conditions.append(f"sf.{column} <= :{param_name}")
    if column not in qp._guarded:
        qp.conditions.append(null_guard)
        qp._guarded.add(column)


# -- DMA / volume condition helpers (correlated subquery approach) --------
# Using correlated subqueries instead of CTEs because SQLite always chooses
# the ticker index over the date index for GROUP BY operations, resulting in
# full 2.95M-row scans (~20s). Correlated subqueries use the PK (ticker, date)
# for efficient index seeks, running in ~2s for the full universe and much
# faster when combined with other filters.

def _dma_50_condition() -> str:
    return (
        "sf.current_price > ("
        "SELECT AVG(close) FROM eod_prices "
        "WHERE ticker = sf.ticker AND date >= date('now', '-70 days')"
        ")"
    )


def _dma_200_condition() -> str:
    return (
        "sf.current_price > ("
        "SELECT AVG(close) FROM eod_prices "
        "WHERE ticker = sf.ticker AND date >= date('now', '-280 days')"
        ")"
    )


def _vol_20d_condition() -> str:
    return (
        "(SELECT volume FROM eod_prices "
        "WHERE ticker = sf.ticker "
        "ORDER BY date DESC LIMIT 1) > ("
        "SELECT AVG(volume) FROM eod_prices "
        "WHERE ticker = sf.ticker AND date >= date('now', '-28 days')"
        ")"
    )


# -- Shared condition builder (used by both screen and count) --------------

class _QueryParts:
    """Container for the pieces assembled during WHERE-clause construction."""

    def __init__(self) -> None:
        self.conditions: list[str] = []
        self.params: dict[str, Any] = {}
        self.cte_parts: list[str] = []
        self.extra_joins: list[str] = []
        self._guarded: set[str] = set()


def _build_conditions(spec: FilterSpec) -> _QueryParts:
    """Populate a _QueryParts from every enabled field on *spec*.

    This is the single source of truth for the WHERE clause.  Both
    ``build_screen_query`` and ``build_count_query`` delegate to it.
    """
    qp = _QueryParts()

    # -- Identity --------------------------------------------------------
    if spec.sectors:
        _add_in_clause(qp.conditions, qp.params, "sector", spec.sectors, "sector")
    if spec.industries:
        _add_in_clause(qp.conditions, qp.params, "industry", spec.industries, "industry")
    if spec.ticker is not None:
        qp.params["ticker"] = spec.ticker
        qp.conditions.append("sf.ticker = :ticker")
    if spec.search is not None:
        qp.params["search"] = spec.search
        qp.conditions.append("sf.company_name LIKE '%' || :search || '%'")

    # -- Valuation -------------------------------------------------------
    if spec.pe_min is not None:
        _add_min_guard(qp, "pe_ratio", spec.pe_min, "pe_min", "sf.pe_ratio > 0")
    if spec.pe_max is not None:
        _add_max_guard(qp, "pe_ratio", spec.pe_max, "pe_max", "sf.pe_ratio > 0")
    if spec.market_cap_min is not None:
        _add_min_guard(qp, "market_cap_crore", spec.market_cap_min, "mcap_min", "sf.market_cap_crore > 0")
    if spec.market_cap_max is not None:
        _add_max_guard(qp, "market_cap_crore", spec.market_cap_max, "mcap_max", "sf.market_cap_crore > 0")
    if spec.pb_min is not None:
        _add_min_guard(qp, "pb_ratio", spec.pb_min, "pb_min", "sf.pb_ratio > 0")
    if spec.pb_max is not None:
        _add_max_guard(qp, "pb_ratio", spec.pb_max, "pb_max", "sf.pb_ratio > 0")
    if spec.peg_max is not None:
        _add_max_guard(qp, "peg_ratio", spec.peg_max, "peg_max", "sf.peg_ratio > 0")
    if spec.price_to_sales_max is not None:
        _add_max_guard(qp, "price_to_sales", spec.price_to_sales_max, "ps_max", "sf.price_to_sales > 0")

    # -- Profitability ---------------------------------------------------
    if spec.roe_min is not None:
        _add_min_guard(qp, "roe_pct", spec.roe_min, "roe_min", "sf.roe_pct IS NOT NULL")
    if spec.roa_min is not None:
        _add_min_guard(qp, "roa_pct", spec.roa_min, "roa_min", "sf.roa_pct IS NOT NULL")
    if spec.profit_margin_min is not None:
        _add_min_guard(qp, "profit_margins_pct", spec.profit_margin_min, "pm_min", "sf.profit_margins_pct IS NOT NULL")
    if spec.operating_margin_min is not None:
        _add_min_guard(qp, "operating_margins_pct", spec.operating_margin_min, "om_min", "sf.operating_margins_pct IS NOT NULL")

    # -- Growth ----------------------------------------------------------
    if spec.revenue_growth_min is not None:
        _add_min_guard(qp, "revenue_growth_pct", spec.revenue_growth_min, "rg_min", "sf.revenue_growth_pct IS NOT NULL")
    if spec.earnings_growth_min is not None:
        _add_min_guard(qp, "earnings_growth_pct", spec.earnings_growth_min, "eg_min", "sf.earnings_growth_pct IS NOT NULL")

    # -- Financial health ------------------------------------------------
    if spec.debt_to_equity_max is not None:
        _add_max_guard(qp, "debt_to_equity", spec.debt_to_equity_max, "de_max", "sf.debt_to_equity IS NOT NULL")
    if spec.current_ratio_min is not None:
        _add_min_guard(qp, "current_ratio", spec.current_ratio_min, "cr_min", "sf.current_ratio > 0")
    if spec.dividend_yield_min is not None:
        _add_min_guard(qp, "dividend_yield_pct", spec.dividend_yield_min, "dy_min", "sf.dividend_yield_pct > 0")

    # -- Ownership -------------------------------------------------------
    if spec.promoter_holding_min is not None:
        _add_min_guard(qp, "held_pct_insiders", spec.promoter_holding_min, "ph_min", "sf.held_pct_insiders > 0")

    # -- Price (52w) -- use stock_fundamentals columns directly ----------
    if spec.price_pct_from_52w_high_max is not None:
        qp.params["pct_52w_high_max"] = spec.price_pct_from_52w_high_max
        qp.conditions.append(
            "((sf.high_52w - sf.current_price) / sf.high_52w) * 100 <= :pct_52w_high_max"
        )
        qp.conditions.append("sf.high_52w > 0")
        qp.conditions.append("sf.current_price > 0")
    if spec.price_pct_from_52w_low_min is not None:
        qp.params["pct_52w_low_min"] = spec.price_pct_from_52w_low_min
        qp.conditions.append(
            "((sf.current_price - sf.low_52w) / sf.low_52w) * 100 >= :pct_52w_low_min"
        )
        qp.conditions.append("sf.low_52w > 0")
        qp.conditions.append("sf.current_price > 0")

    # -- Price-based (DMA / volume) -- correlated subqueries on eod_prices
    if spec.price_above_50dma:
        qp.conditions.append(_dma_50_condition())
    if spec.price_above_200dma:
        qp.conditions.append(_dma_200_condition())
    if spec.volume_above_20d_avg:
        qp.conditions.append(_vol_20d_condition())

    return qp


def _assemble_clauses(qp: _QueryParts) -> tuple[str, str]:
    """Return (from_clause, where_clause) from *qp*."""
    from_clause = "stock_fundamentals sf"

    if qp.conditions:
        where_clause = " WHERE " + "\n  AND ".join(qp.conditions)
    else:
        where_clause = ""

    return from_clause, where_clause


# -- Public API ------------------------------------------------------------

def build_screen_query(spec: FilterSpec) -> tuple[str, dict[str, Any]]:
    """Build a parameterised SELECT query from a FilterSpec.

    Returns:
        ``(sql, params)`` tuple suitable for ``conn.execute(sql, params)``.
        *sql* uses ``:param`` named-placeholder style.
    """
    qp = _build_conditions(spec)
    from_clause, where_clause = _assemble_clauses(qp)

    sort_col = resolve_sort(spec.sort_by)
    sort_dir = spec.sort_dir.upper()

    qp.params["limit"] = spec.limit
    qp.params["offset"] = spec.offset

    sql = (
        f"SELECT sf.*\n"
        f"FROM {from_clause}"
        f"{where_clause}\n"
        f"ORDER BY sf.{sort_col} {sort_dir}\n"
        f"LIMIT :limit OFFSET :offset"
    )

    return sql, qp.params


def build_count_query(spec: FilterSpec) -> tuple[str, dict[str, Any]]:
    """Same WHERE as ``build_screen_query`` but returns ``SELECT COUNT(*)``.

    No ORDER BY, LIMIT, or OFFSET.
    """
    qp = _build_conditions(spec)
    from_clause, where_clause = _assemble_clauses(qp)

    sql = (
        f"SELECT COUNT(*)\n"
        f"FROM {from_clause}"
        f"{where_clause}"
    )

    return sql, qp.params
