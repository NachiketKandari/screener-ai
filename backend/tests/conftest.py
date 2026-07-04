"""Shared fixtures for backend tests."""

import os
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SCHEMA_PATH = (
    Path(__file__).parent.parent.parent / "data_pipeline" / "schema.sql"
)

_TEST_INSERT_SQL = """
INSERT INTO stock_fundamentals (ticker, as_of_date, company_name, sector,
    industry, current_price, market_cap_crore, pe_ratio, pb_ratio,
    roe_pct, roa_pct, profit_margins_pct, operating_margins_pct,
    revenue_growth_pct, earnings_growth_pct, debt_to_equity,
    current_ratio, dividend_yield_pct, eps_ttm,
    high_52w, low_52w, held_pct_insiders)
VALUES
    ('TCS', '2026-07-03', 'Tata Consultancy', 'Technology', 'Software',
     3800.0, 1200000, 28.5, 12.0, 45.0, 22.0, 25.0, 30.0,
     12.0, 8.0, 0.1, 2.5, 1.5, 130.0,
     4200.0, 3200.0, 72.0),
    ('HDFCBANK', '2026-07-03', 'HDFC Bank', 'Financial Services', 'Banking',
     1650.0, 850000, 18.3, 3.5, 16.0, 1.8, 22.0, 35.0,
     15.0, 14.0, 0.8, 1.2, 1.0, 88.0,
     1700.0, 1400.0, NULL),
    ('RELIANCE', '2026-07-03', 'Reliance Industries', 'Energy', 'Oil & Gas',
     2450.0, 1650000, 22.1, 2.8, 9.0, 5.0, 10.0, 15.0,
     8.0, 12.0, 0.6, 1.5, 0.5, 110.0,
     2800.0, 2200.0, 48.0),
    ('INFY', '2026-07-03', 'Infosys', 'Technology', 'Software',
     1500.0, 620000, 25.0, 8.0, 32.0, 18.0, 22.0, 25.0,
     10.0, 6.0, 0.05, 3.0, 2.0, 60.0,
     1900.0, 1200.0, 0.0),
    ('VBL', '2026-07-03', 'Varun Beverages', 'Consumer Defensive', 'Beverages',
     600.0, 180000, 85.0, 15.0, 28.0, 12.0, 8.0, 12.0,
     18.0, 25.0, 0.3, 1.8, 0.2, 7.0,
     650.0, 500.0, NULL);

INSERT INTO eod_prices (ticker, date, open, high, low, close, volume)
VALUES
    ('TCS',   '2026-07-03', 3790.0, 3820.0, 3780.0, 3800.0, 2500000),
    ('TCS',   '2026-07-02', 3780.0, 3810.0, 3770.0, 3790.0, 2400000),
    ('HDFCBANK', '2026-07-03', 1640.0, 1660.0, 1630.0, 1650.0, 5200000),
    ('RELIANCE', '2026-07-03', 2440.0, 2460.0, 2430.0, 2450.0, 3800000);
"""


@pytest.fixture(scope="session")
def _schema_sql() -> str:
    return SCHEMA_PATH.read_text()


@pytest.fixture
def test_db_path(tmp_path: Path) -> str:
    """Return a temporary database path for tests that manage their own schema."""
    db_path = tmp_path / "test.db"
    return str(db_path)


@pytest.fixture
def test_db(tmp_path: Path, _schema_sql: str) -> str:
    """Create a temporary SQLite database with the full schema and test data."""
    db_path = tmp_path / "test.db"
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(_schema_sql)
        conn.executescript(_TEST_INSERT_SQL)
    return str(db_path)


@pytest.fixture
def client(test_db: str) -> TestClient:
    """FastAPI TestClient wired to the test database."""
    from backend.main import create_app

    app = create_app()
    app.state.db_path = test_db
    return TestClient(app)
