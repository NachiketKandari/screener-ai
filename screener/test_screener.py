import sqlite3
import pytest
from screener.screener import Screener, QueryError
from screener.config import Config
from screener.prompt_builder import PromptBuilder


@pytest.fixture
def test_db(tmp_path):
    """Create a minimal test database."""
    db_path = tmp_path / "test.db"
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript("""
            CREATE TABLE eod_prices (
                ticker TEXT NOT NULL,
                date TEXT NOT NULL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (ticker, date)
            );
            CREATE TABLE stock_fundamentals (
                ticker TEXT PRIMARY KEY,
                company_name TEXT,
                sector TEXT,
                pe_ratio REAL,
                roe_pct REAL,
                market_cap_crore REAL,
                debt_to_equity REAL
            );
            INSERT INTO stock_fundamentals VALUES
                ('TCS', 'Tata Consultancy', 'Technology', 28.5, 45.2, 1200000, 0.0),
                ('HDFCBANK', 'HDFC Bank', 'Financial Services', 18.3, 16.8, 850000, 0.8),
                ('RELIANCE', 'Reliance Industries', 'Energy', 22.1, 9.5, 1650000, 0.6),
                ('INFY', 'Infosys', 'Technology', 25.0, 32.1, 620000, 0.0),
                ('VBL', 'Varun Beverages', 'Consumer Defensive', 85.0, 28.0, 180000, 0.3);
            INSERT INTO eod_prices VALUES
                ('TCS', '2026-07-03', 3800.0, 2500000),
                ('HDFCBANK', '2026-07-03', 1650.0, 5200000),
                ('RELIANCE', '2026-07-03', 2450.0, 3800000);
        """)
    return str(db_path)


class FakeConfig:
    api_key = "sk-fake"
    base_url = "https://api.deepseek.com"
    model = "deepseek-v4-flash"
    db_path_absolute = None
    query_timeout = 5
    max_rows = 100

    def __init__(self, db_path):
        self.db_path_absolute = db_path


class FakeLLM:
    """Returns a fixed SQL string instead of calling DeepSeek."""
    def __init__(self, sql_to_return):
        self.sql_to_return = sql_to_return
        self.call_count = 0
        self.prompts = []

    def __call__(self, prompt):
        self.call_count += 1
        self.prompts.append(prompt)
        return self.sql_to_return


def test_screener_executes_valid_sql(test_db):
    cfg = FakeConfig(test_db)
    llm = FakeLLM("SELECT ticker, company_name, pe_ratio FROM stock_fundamentals WHERE pe_ratio < 30")
    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=llm)

    columns, rows = screener.query("cheap stocks")

    assert columns == ("ticker", "company_name", "pe_ratio")
    assert len(rows) == 4  # TCS(28.5), HDFCBANK(18.3), RELIANCE(22.1), INFY(25.0)


def test_screener_extracts_sql_from_markdown(test_db):
    cfg = FakeConfig(test_db)
    llm = FakeLLM("```sql\nSELECT ticker FROM stock_fundamentals WHERE ticker = 'TCS'\n```")
    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=llm)

    columns, rows = screener.query("find TCS")

    assert rows[0][0] == "TCS"


def test_screener_retries_on_sqlglot_failure(test_db):
    cfg = FakeConfig(test_db)
    responses = ["SELECT * FRUM stock_fundamentals", "SELECT * FROM stock_fundamentals"]
    call_count = [0]

    def bad_then_good(prompt):
        idx = call_count[0]
        call_count[0] += 1
        return responses[idx]

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=bad_then_good)

    columns, rows = screener.query("test")

    assert call_count[0] == 2
    assert len(rows) == 5


def test_screener_raises_on_double_failure(test_db):
    cfg = FakeConfig(test_db)
    llm = FakeLLM("NOT A VALID SQL STATEMENT AT ALL !!!")

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=llm)

    with pytest.raises(QueryError) as exc:
        screener.query("test")
    assert exc.value.exit_code == 2
    assert llm.call_count == 2


def test_screener_rejects_non_select(test_db):
    cfg = FakeConfig(test_db)
    llm = FakeLLM("DROP TABLE stock_fundamentals")

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=llm)

    with pytest.raises(QueryError) as exc:
        screener.query("test")
    assert exc.value.exit_code == 3


def test_screener_applies_row_limit(test_db):
    cfg = FakeConfig(test_db)
    cfg.max_rows = 2
    llm = FakeLLM("SELECT * FROM stock_fundamentals")

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=llm)

    columns, rows = screener.query("test")
    assert len(rows) == 2


def test_screener_empty_results(test_db):
    cfg = FakeConfig(test_db)
    llm = FakeLLM("SELECT * FROM stock_fundamentals WHERE pe_ratio < 0")

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=llm)

    columns, rows = screener.query("test")
    assert rows == []


def test_screener_readonly_prevents_writes(test_db):
    """Verify we open the DB in read-only mode."""
    cfg = FakeConfig(test_db)
    llm = FakeLLM("INSERT INTO stock_fundamentals (ticker) VALUES ('EVIL')")

    screener = Screener(cfg, prompt_builder=PromptBuilder(), llm_callable=llm)

    with pytest.raises(QueryError) as exc:
        screener.query("test")
    assert exc.value.exit_code == 3
