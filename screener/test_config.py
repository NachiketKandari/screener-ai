import os
from screener.config import Config


def test_config_loads_from_env(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("STRATTEST_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("STRATTEST_DB_PATH", "db/test.db")
    monkeypatch.setenv("STRATTEST_QUERY_TIMEOUT", "30")
    monkeypatch.setenv("STRATTEST_MAX_ROWS", "500")

    cfg = Config()

    assert cfg.api_key == "sk-test"
    assert cfg.base_url == "https://api.deepseek.com"
    assert cfg.model == "deepseek-v4-flash"
    assert cfg.db_path == "db/test.db"
    assert cfg.query_timeout == 30
    assert cfg.max_rows == 500


def test_config_defaults(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.delenv("STRATTEST_DB_PATH", raising=False)
    monkeypatch.delenv("STRATTEST_QUERY_TIMEOUT", raising=False)
    monkeypatch.delenv("STRATTEST_MAX_ROWS", raising=False)
    monkeypatch.delenv("STRATTEST_MODEL", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)

    cfg = Config()

    assert cfg.db_path == "db/strattest.db"
    assert cfg.query_timeout == 30
    assert cfg.max_rows == 1000
    assert cfg.model == "deepseek-v4-flash"
    assert cfg.base_url == "https://api.deepseek.com"


def test_config_missing_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    try:
        Config()
        assert False, "Expected SystemExit"
    except SystemExit as e:
        assert e.code == 1
