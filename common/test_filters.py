"""Tests for common.filters -- the SQL builder."""

from __future__ import annotations

import pytest

from common.types import FilterSpec
from common.filters import (
    SORT_COLUMNS,
    build_count_query,
    build_screen_query,
    resolve_sort,
)


# ── resolve_sort ────────────────────────────────────────────────────────

class TestResolveSort:
    def test_all_valid_columns(self):
        """Every entry in SORT_COLUMNS must resolve to itself."""
        for key in SORT_COLUMNS:
            assert resolve_sort(key) == SORT_COLUMNS[key]

    def test_invalid_column_raises(self):
        with pytest.raises(ValueError, match="Unknown sort column"):
            resolve_sort("nonexistent_column")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Unknown sort column"):
            resolve_sort("")


# ── build_screen_query ──────────────────────────────────────────────────

class TestBuildScreenQuery:
    def test_no_filters_produces_minimal_sql(self):
        """A FilterSpec with only defaults should produce a simple query with
        no WHERE clause."""
        spec = FilterSpec()
        sql, params = build_screen_query(spec)

        assert "SELECT sf.*" in sql
        assert "FROM stock_fundamentals sf" in sql
        assert "WHERE" not in sql
        assert "ORDER BY sf.market_cap_crore DESC" in sql
        assert "LIMIT :limit OFFSET :offset" in sql
        assert params["limit"] == 50
        assert params["offset"] == 0

    def test_ticker_filter(self):
        spec = FilterSpec(ticker="RELIANCE")
        sql, params = build_screen_query(spec)

        assert "sf.ticker = :ticker" in sql
        assert params["ticker"] == "RELIANCE"

    def test_search_filter(self):
        spec = FilterSpec(search="Reliance")
        sql, params = build_screen_query(spec)

        assert "sf.company_name LIKE '%' || :search || '%'" in sql
        assert params["search"] == "Reliance"

    def test_sectors_filter(self):
        spec = FilterSpec(sectors=["Technology", "Finance"])
        sql, params = build_screen_query(spec)

        assert "sf.sector IN (" in sql
        assert ":sector_0" in sql
        assert ":sector_1" in sql
        assert params["sector_0"] == "Technology"
        assert params["sector_1"] == "Finance"

    def test_industries_filter(self):
        spec = FilterSpec(industries=["Software", "Banking"])
        sql, params = build_screen_query(spec)

        assert "sf.industry IN (" in sql
        assert ":industry_0" in sql
        assert ":industry_1" in sql
        assert params["industry_0"] == "Software"
        assert params["industry_1"] == "Banking"

    def test_pe_filter_with_null_guard(self):
        spec = FilterSpec(pe_min=10.0, pe_max=30.0)
        sql, params = build_screen_query(spec)

        assert "sf.pe_ratio >= :pe_min" in sql
        assert "sf.pe_ratio <= :pe_max" in sql
        assert "sf.pe_ratio > 0" in sql  # null guard
        assert params["pe_min"] == 10.0
        assert params["pe_max"] == 30.0

    def test_valuation_filters(self):
        spec = FilterSpec(
            pb_min=1.0,
            pb_max=3.0,
            peg_max=1.5,
            price_to_sales_max=5.0,
        )
        sql, params = build_screen_query(spec)

        assert "sf.pb_ratio >= :pb_min" in sql
        assert "sf.pb_ratio <= :pb_max" in sql
        assert "sf.pb_ratio > 0" in sql
        assert "sf.peg_ratio <= :peg_max" in sql
        assert "sf.price_to_sales <= :ps_max" in sql
        assert params["pb_min"] == 1.0
        assert params["pb_max"] == 3.0

    def test_profitability_filters_with_null_guards(self):
        spec = FilterSpec(
            roe_min=15.0,
            roa_min=5.0,
            profit_margin_min=10.0,
            operating_margin_min=12.0,
        )
        sql, params = build_screen_query(spec)

        assert "sf.roe_pct >= :roe_min" in sql
        assert "sf.roe_pct IS NOT NULL" in sql
        assert "sf.roa_pct >= :roa_min" in sql
        assert "sf.roa_pct IS NOT NULL" in sql
        assert "sf.profit_margins_pct IS NOT NULL" in sql
        assert "sf.operating_margins_pct IS NOT NULL" in sql

    def test_growth_filters_with_null_guards(self):
        spec = FilterSpec(
            revenue_growth_min=10.0,
            earnings_growth_min=15.0,
        )
        sql, _params = build_screen_query(spec)

        assert "sf.revenue_growth_pct >= :rg_min" in sql
        assert "sf.revenue_growth_pct IS NOT NULL" in sql
        assert "sf.earnings_growth_pct >= :eg_min" in sql
        assert "sf.earnings_growth_pct IS NOT NULL" in sql

    def test_financial_health_filters(self):
        spec = FilterSpec(
            debt_to_equity_max=2.0,
            current_ratio_min=1.5,
            dividend_yield_min=1.0,
        )
        sql, params = build_screen_query(spec)

        assert "sf.debt_to_equity <= :de_max" in sql
        assert "sf.debt_to_equity IS NOT NULL" in sql
        assert "sf.current_ratio >= :cr_min" in sql
        assert "sf.current_ratio > 0" in sql
        assert "sf.dividend_yield_pct >= :dy_min" in sql
        assert "sf.dividend_yield_pct > 0" in sql

    def test_promoter_holding_filter(self):
        spec = FilterSpec(promoter_holding_min=40.0)
        sql, params = build_screen_query(spec)

        assert "sf.held_pct_insiders >= :ph_min" in sql
        assert "sf.held_pct_insiders > 0" in sql
        assert params["ph_min"] == 40.0

    def test_52w_filters_no_join(self):
        """52-week high/low filters use stock_fundamentals columns directly."""
        spec = FilterSpec(
            price_pct_from_52w_high_max=20.0,
            price_pct_from_52w_low_min=10.0,
        )
        sql, params = build_screen_query(spec)

        assert "high_52w" in sql
        assert "low_52w" in sql
        assert "current_price" in sql
        # No eod_prices references
        assert "eod_prices" not in sql
        assert "dma_50" not in sql
        assert "dma_200" not in sql
        assert params["pct_52w_high_max"] == 20.0
        assert params["pct_52w_low_min"] == 10.0

    def test_dma_50_triggers_correlated_subquery(self):
        """price_above_50dma should use a correlated subquery on eod_prices."""
        spec = FilterSpec(price_above_50dma=True)
        sql, _params = build_screen_query(spec)

        assert "eod_prices" in sql
        assert "ticker = sf.ticker" in sql
        assert "sf.current_price >" in sql
        assert "date('now', '-70 days')" in sql
        assert "LEFT JOIN" not in sql  # no CTE/JOIN

    def test_dma_200_triggers_correlated_subquery(self):
        """price_above_200dma should use a correlated subquery on eod_prices."""
        spec = FilterSpec(price_above_200dma=True)
        sql, _params = build_screen_query(spec)

        assert "eod_prices" in sql
        assert "ticker = sf.ticker" in sql
        assert "date('now', '-280 days')" in sql
        assert "LEFT JOIN" not in sql

    def test_volume_above_20d_avg_triggers_correlated_subquery(self):
        spec = FilterSpec(volume_above_20d_avg=True)
        sql, _params = build_screen_query(spec)

        assert "eod_prices" in sql
        assert "volume" in sql
        assert "ticker = sf.ticker" in sql
        assert "LEFT JOIN" not in sql

    def test_multiple_price_conditions(self):
        """All three price conditions should coexist in one query."""
        spec = FilterSpec(
            price_above_50dma=True,
            price_above_200dma=True,
            volume_above_20d_avg=True,
        )
        sql, _params = build_screen_query(spec)

        assert "date('now', '-70 days')" in sql
        assert "date('now', '-280 days')" in sql
        assert "volume" in sql
        assert sql.count("ticker = sf.ticker") >= 4  # each condition has at least 1 correlated ref

    def test_no_price_data_no_eod_prices(self):
        """Without price-based conditions, eod_prices should not appear at all."""
        spec = FilterSpec(pe_max=20.0, sectors=["Health"])
        sql, _params = build_screen_query(spec)

        assert "eod_prices" not in sql
        assert "dma_50" not in sql
        assert "dma_200" not in sql
        assert "vol_stats" not in sql
        assert "LEFT JOIN" not in sql

    def test_custom_sort_and_pagination(self):
        spec = FilterSpec(
            sort_by="pe_ratio",
            sort_dir="asc",
            limit=25,
            offset=10,
        )
        sql, params = build_screen_query(spec)

        assert "ORDER BY sf.pe_ratio ASC" in sql
        assert "LIMIT :limit OFFSET :offset" in sql
        assert params["limit"] == 25
        assert params["offset"] == 10

    def test_market_cap_filters(self):
        spec = FilterSpec(market_cap_min=100.0, market_cap_max=10000.0)
        sql, params = build_screen_query(spec)

        assert "sf.market_cap_crore >= :mcap_min" in sql
        assert "sf.market_cap_crore <= :mcap_max" in sql
        assert "sf.market_cap_crore > 0" in sql
        assert params["mcap_min"] == 100.0
        assert params["mcap_max"] == 10000.0

    def test_combined_filters(self):
        """A rich FilterSpec with many fields should produce a well-formed query."""
        spec = FilterSpec(
            sectors=["Technology"],
            pe_min=10.0,
            pe_max=30.0,
            roe_min=15.0,
            debt_to_equity_max=2.0,
            dividend_yield_min=2.0,
            price_above_50dma=True,
            sort_by="dividend_yield_pct",
            sort_dir="desc",
            limit=20,
            offset=0,
        )
        sql, params = build_screen_query(spec)

        assert "sf.sector IN (" in sql
        assert "sf.pe_ratio >= :pe_min" in sql
        assert "sf.pe_ratio <= :pe_max" in sql
        assert "sf.pe_ratio > 0" in sql
        assert "sf.roe_pct >= :roe_min" in sql
        assert "sf.roe_pct IS NOT NULL" in sql
        assert "sf.debt_to_equity <= :de_max" in sql
        assert "sf.debt_to_equity IS NOT NULL" in sql
        assert "sf.dividend_yield_pct >= :dy_min" in sql
        assert "sf.current_price > (SELECT AVG(close) FROM eod_prices WHERE ticker = sf.ticker" in sql
        assert "ORDER BY sf.dividend_yield_pct DESC" in sql
        assert params["limit"] == 20
        assert params["offset"] == 0

    def test_parameterized_not_string_interpolated(self):
        """Values must appear as :params, never inlined into SQL text."""
        spec = FilterSpec(pe_max=20.0, ticker="ABC")
        sql, _params = build_screen_query(spec)

        # Literal values should NOT appear in SQL
        assert "20.0" not in sql
        assert "'ABC'" not in sql
        # But parameter names should
        assert ":pe_max" in sql
        assert ":ticker" in sql


# ── build_count_query ───────────────────────────────────────────────────

class TestBuildCountQuery:
    def test_selects_count_star(self):
        spec = FilterSpec(pe_max=20.0)
        sql, _params = build_count_query(spec)

        assert "SELECT COUNT(*)" in sql

    def test_no_order_by(self):
        spec = FilterSpec(pe_max=20.0, sort_by="roe_pct", sort_dir="asc")
        sql, _params = build_count_query(spec)

        assert "ORDER BY" not in sql

    def test_no_limit_offset(self):
        spec = FilterSpec(pe_max=20.0)
        sql, params = build_count_query(spec)

        assert "LIMIT" not in sql
        assert "OFFSET" not in sql
        assert "limit" not in params
        assert "offset" not in params

    def test_same_where_as_screen(self):
        """Count and screen queries should share the same WHERE conditions."""
        spec = FilterSpec(
            sectors=["Tech"],
            pe_min=10.0,
            roe_min=15.0,
            price_above_50dma=True,
        )
        screen_sql, _ = build_screen_query(spec)
        count_sql, _ = build_count_query(spec)

        # Both should have the same conditions
        for fragment in [
            "sf.sector IN (",
            "sf.pe_ratio >= :pe_min",
            "sf.roe_pct >= :roe_min",
            "sf.current_price > (SELECT AVG(close) FROM eod_prices WHERE ticker = sf.ticker",
        ]:
            assert fragment in screen_sql
            assert fragment in count_sql

    def test_count_params_dont_include_pagination(self):
        spec = FilterSpec(pe_max=20.0)
        _sql, params = build_count_query(spec)

        assert "limit" not in params
        assert "offset" not in params


# ── Null-guard correctness ──────────────────────────────────────────────

class TestNullGuards:
    """Ensure every filtered nullable column includes an appropriate guard."""

    def test_pe_ratio_has_gt_zero_guard(self):
        spec = FilterSpec(pe_min=10.0)
        sql, _params = build_screen_query(spec)
        assert "sf.pe_ratio > 0" in sql

    def test_pb_ratio_has_gt_zero_guard(self):
        spec = FilterSpec(pb_max=3.0)
        sql, _params = build_screen_query(spec)
        assert "sf.pb_ratio > 0" in sql

    def test_roe_has_is_not_null_guard(self):
        spec = FilterSpec(roe_min=15.0)
        sql, _params = build_screen_query(spec)
        assert "sf.roe_pct IS NOT NULL" in sql

    def test_growth_has_is_not_null_guard(self):
        spec = FilterSpec(revenue_growth_min=10.0)
        sql, _params = build_screen_query(spec)
        assert "sf.revenue_growth_pct IS NOT NULL" in sql

    def test_debt_has_is_not_null_guard(self):
        spec = FilterSpec(debt_to_equity_max=2.0)
        sql, _params = build_screen_query(spec)
        assert "sf.debt_to_equity IS NOT NULL" in sql

    def test_dividend_has_gt_zero_guard(self):
        spec = FilterSpec(dividend_yield_min=2.0)
        sql, _params = build_screen_query(spec)
        assert "sf.dividend_yield_pct > 0" in sql

    def test_promoter_holding_has_gt_zero_guard(self):
        spec = FilterSpec(promoter_holding_min=30.0)
        sql, _params = build_screen_query(spec)
        assert "sf.held_pct_insiders > 0" in sql

    def test_market_cap_has_gt_zero_guard(self):
        spec = FilterSpec(market_cap_min=500.0)
        sql, _params = build_screen_query(spec)
        assert "sf.market_cap_crore > 0" in sql
