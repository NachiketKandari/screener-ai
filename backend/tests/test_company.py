"""Tests for company detail endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_company_data(test_db_path, monkeypatch):
    """Test client with a DB that has company + price data."""
    import sqlite3, os
    monkeypatch.setenv("STRATTEST_DB_PATH", test_db_path)

    conn = sqlite3.connect(test_db_path)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS stock_fundamentals (
            ticker TEXT PRIMARY KEY, as_of_date TEXT, company_name TEXT,
            sector TEXT, industry TEXT, exchange TEXT,
            current_price REAL, market_cap_crore REAL, pe_ratio REAL,
            forward_pe REAL, pb_ratio REAL, peg_ratio REAL,
            price_to_sales REAL, eps_ttm REAL, eps_forward REAL,
            book_value_per_share REAL, roe_pct REAL, roa_pct REAL,
            profit_margins_pct REAL, operating_margins_pct REAL,
            gross_margins_pct REAL, ebitda_margins_pct REAL,
            revenue_growth_pct REAL, earnings_growth_pct REAL,
            earnings_quarterly_growth_pct REAL, debt_to_equity REAL,
            current_ratio REAL, quick_ratio REAL, payout_ratio REAL,
            dividend_yield_pct REAL, five_year_avg_dividend_yield_pct REAL,
            high_52w REAL, low_52w REAL, beta REAL,
            target_mean_price REAL, target_high_price REAL,
            target_low_price REAL, recommendation TEXT,
            number_of_analysts INTEGER, held_pct_insiders REAL,
            held_pct_institutions REAL, free_cashflow REAL,
            operating_cashflow REAL, total_cash_per_share REAL,
            total_debt REAL, total_revenue REAL, ebitda REAL
        );
        CREATE TABLE IF NOT EXISTS eod_prices (
            ticker TEXT NOT NULL, date TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL, volume INTEGER,
            PRIMARY KEY (ticker, date)
        );
        INSERT INTO stock_fundamentals (
            ticker, as_of_date, company_name, sector, industry, exchange,
            current_price, market_cap_crore, pe_ratio, forward_pe, pb_ratio,
            peg_ratio, price_to_sales, eps_ttm, eps_forward,
            book_value_per_share, roe_pct, roa_pct, profit_margins_pct,
            operating_margins_pct, gross_margins_pct, ebitda_margins_pct,
            revenue_growth_pct, earnings_growth_pct,
            earnings_quarterly_growth_pct, debt_to_equity, current_ratio,
            quick_ratio, payout_ratio, dividend_yield_pct,
            five_year_avg_dividend_yield_pct, high_52w, low_52w, beta,
            target_mean_price, target_high_price, target_low_price,
            recommendation, number_of_analysts, held_pct_insiders,
            held_pct_institutions, free_cashflow, operating_cashflow,
            total_cash_per_share, total_debt, total_revenue, ebitda
        ) VALUES (
            'TEST', '2026-07-04', 'Test Co', 'Tech', 'Software', 'NSE',
            100.0, 5000.0, 15.0, 14.0, 2.0,
            3.0, 50.0, 48.0, 25.0,
            18.0, 18.0, 5.0, 20.0,
            30.0, 60.0, 40.0,
            10.0, 8.0,
            2.0, 0.5, 1.5,
            1.2, 15.0, 1.5,
            0.8, 120.0, 80.0, 1.1,
            130.0, 140.0, 110.0,
            'Buy', 10, 0.25,
            0.45, 1000.0, 1500.0,
            30.0, 200.0, 5000.0, 800.0
        );
        INSERT INTO eod_prices VALUES ('TEST', '2026-07-03', 98.0, 102.0, 97.0, 99.0, 10000);
        INSERT INTO eod_prices VALUES ('TEST', '2026-07-04', 99.0, 101.0, 98.5, 100.0, 12000);
        -- Second company in same sector for peers test
        INSERT INTO stock_fundamentals (
            ticker, as_of_date, company_name, sector, industry, exchange,
            current_price, market_cap_crore, pe_ratio, forward_pe, pb_ratio,
            peg_ratio, price_to_sales, eps_ttm, eps_forward,
            book_value_per_share, roe_pct, roa_pct, profit_margins_pct,
            operating_margins_pct, gross_margins_pct, ebitda_margins_pct,
            revenue_growth_pct, earnings_growth_pct,
            earnings_quarterly_growth_pct, debt_to_equity, current_ratio,
            quick_ratio, payout_ratio, dividend_yield_pct,
            five_year_avg_dividend_yield_pct, high_52w, low_52w, beta,
            target_mean_price, target_high_price, target_low_price,
            recommendation, number_of_analysts, held_pct_insiders,
            held_pct_institutions, free_cashflow, operating_cashflow,
            total_cash_per_share, total_debt, total_revenue, ebitda
        ) VALUES (
            'PEER1', '2026-07-04', 'Peer One', 'Tech', 'Software', 'NSE',
            200.0, 8000.0, 20.0, 18.0, 3.0,
            4.0, 60.0, 55.0, 30.0,
            15.0, 4.0, 18.0, 28.0,
            55.0, 38.0, 12.0,
            10.0, 3.0,
            0.6, 1.4, 1.1,
            10.0, 2.0, 1.0,
            150.0, 90.0, 0.9, NULL,
            NULL, NULL, NULL,
            NULL, NULL, NULL,
            NULL, NULL, NULL,
            NULL, NULL, NULL, NULL
        );
    """)
    conn.commit()
    conn.close()

    # Force re-import so the app picks up the new DB path
    import backend.main
    import importlib
    importlib.reload(backend.main)
    from backend.main import app
    return TestClient(app)


def test_get_company_returns_full_data(client_with_company_data):
    resp = client_with_company_data.get("/api/company/TEST")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "TEST"
    assert data["company_name"] == "Test Co"
    assert data["sector"] == "Tech"
    assert data["price"]["current"] == 100.0
    assert data["price"]["change"] == 1.0  # 100 - 99
    assert data["price"]["open"] == 99.0
    assert data["price"]["high"] == 101.0
    assert data["valuation"]["pe_ratio"] == 15.0
    assert data["profitability"]["roe_pct"] == 18.0
    assert data["growth"]["revenue_growth_pct"] == 10.0
    assert data["financial_health"]["debt_to_equity"] == 0.5
    assert data["analyst_coverage"]["recommendation"] == "Buy"
    assert data["analyst_coverage"]["number_of_analysts"] == 10


def test_get_company_404(client_with_company_data):
    resp = client_with_company_data.get("/api/company/ZZZZZ")
    assert resp.status_code == 404


def test_get_company_chart_returns_data(client_with_company_data):
    resp = client_with_company_data.get("/api/company/TEST/chart?range=1mo")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "TEST"
    assert data["range"] == "1mo"
    assert len(data["data"]) >= 1
    point = data["data"][0]
    assert "date" in point
    assert "close" in point


def test_get_company_chart_invalid_range(client_with_company_data):
    resp = client_with_company_data.get("/api/company/TEST/chart?range=invalid")
    assert resp.status_code == 422


def test_get_company_peers(client_with_company_data):
    resp = client_with_company_data.get("/api/company/TEST/peers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "TEST"
    assert len(data["peers"]) >= 1
    assert data["peers"][0]["ticker"] == "PEER1"


def test_get_company_peers_404(client_with_company_data):
    resp = client_with_company_data.get("/api/company/ZZZZZ/peers")
    assert resp.status_code == 404
