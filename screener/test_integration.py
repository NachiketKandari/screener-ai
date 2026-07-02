"""End-to-end integration tests with a fake LLM and real SQLite."""

import sqlite3
import pytest
from screener.screener import Screener
from screener.prompt_builder import PromptBuilder


@pytest.fixture
def integration_db(tmp_path):
    """Full schema test database with sample data."""
    from pathlib import Path
    schema_path = Path(__file__).parent.parent / "data_pipeline" / "schema.sql"
    db_path = tmp_path / "integration.db"
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(schema_path.read_text())
        conn.executescript("""
            INSERT INTO stock_fundamentals VALUES
                ('TCS', '2026-07-01', 'Tata Consultancy', 'Technology', 'Software',
                 'NSI', 3800, 1230000, 28.5, 25.0, 12.3, 2.1, 7.5,
                 45.2, 22.0, 19.5, 25.0, 55.0, 35.0,
                 133.3, 152.0, 310.0, 350.0,
                 12.5, 10.2, 8.5,
                 0.0, 2.5, 2.0, 35.0,
                 1.2, 1.1,
                 4200, 3400, 0.85,
                 4200, 4500, 3800,
                 'buy', 42,
                 8.5, 45.0,
                 35000, 42000, 120.0,
                 0, 650000, 28000);
            INSERT INTO stock_fundamentals VALUES
                ('VBL', '2026-07-01', 'Varun Beverages', 'Consumer Defensive', 'Beverages',
                 'NSI', 1500, 180000, 85.0, 60.0, 18.5, 3.5, 12.0,
                 28.0, 12.0, 10.0, 18.0, 48.0, 22.0,
                 17.6, 25.0, 83.0, 125.0,
                 35.0, 40.0, 25.0,
                 0.3, 1.2, 1.0, 15.0,
                 0.3, 0.2,
                 1600, 800, 0.95,
                 1800, 2000, 1300,
                 'buy', 28,
                 65.0, 22.0,
                 12000, 15000, 45.0,
                 5000, 85000, 12000);
            INSERT INTO eod_prices VALUES
                ('TCS', '2026-07-01', 3800, 3850, 3780, 3800, 2500000, 0, 0),
                ('TCS', '2026-07-02', 3820, 3880, 3800, 3820, 2100000, 0, 0);
        """)
    return str(db_path)


class FakeConfig:
    api_key = "sk-test"
    base_url = "https://api.deepseek.com"
    model = "deepseek-v4-flash"
    query_timeout = 5
    max_rows = 100

    def __init__(self, db_path):
        self.db_path_absolute = db_path


def test_end_to_end_valuation_screen(integration_db):
    cfg = FakeConfig(integration_db)

    def fake_llm(prompt):
        return """SELECT ticker, company_name, pe_ratio, roe_pct, market_cap_crore
FROM stock_fundamentals WHERE pe_ratio < 30 AND pe_ratio > 0
AND roe_pct > 20 ORDER BY pe_ratio ASC"""

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=fake_llm)
    columns, rows = screener.query("stocks with PE under 30 and ROE above 20")

    # TCS matches (PE 28.5, ROE 45.2), VBL does not (PE 85)
    assert len(rows) == 1
    assert rows[0][0] == "TCS"


def test_end_to_end_joins_price_and_fundamentals(integration_db):
    cfg = FakeConfig(integration_db)

    def fake_llm(prompt):
        return """SELECT f.ticker, f.company_name, f.current_price, p.close
FROM stock_fundamentals f INNER JOIN eod_prices p ON f.ticker = p.ticker
WHERE p.date = '2026-07-02'"""

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=fake_llm)
    columns, rows = screener.query("stocks with recent price data")

    assert len(rows) >= 1


def test_end_to_end_sector_filter(integration_db):
    cfg = FakeConfig(integration_db)

    def fake_llm(prompt):
        return """SELECT ticker, company_name, sector FROM stock_fundamentals
WHERE sector = 'Consumer Defensive'"""

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=fake_llm)
    columns, rows = screener.query("consumer stocks")

    assert len(rows) == 1
    assert rows[0][0] == "VBL"


def test_sql_injection_prevented(integration_db):
    cfg = FakeConfig(integration_db)

    def fake_llm(prompt):
        return "SELECT ticker FROM stock_fundamentals WHERE ticker = 'TCS'; DROP TABLE stock_fundamentals; --'"

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=fake_llm)
    # Multiple statements fail in sqlite3 + read-only mode
    with pytest.raises(Exception):
        screener.query("malicious query")
