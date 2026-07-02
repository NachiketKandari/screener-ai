import os
from pathlib import Path


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default))
    try:
        return int(raw)
    except (ValueError, TypeError):
        raise ConfigError(
            f"{name}={raw!r} is not a valid integer"
        ) from None


class ConfigError(Exception):
    """Configuration error — missing or invalid env vars."""
    pass


class Config:
    def __init__(self):
        self.api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ConfigError(
                "DEEPSEEK_API_KEY environment variable is required"
            )

        self.base_url = os.environ.get(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        )
        self.model = os.environ.get("STRATTEST_MODEL", "deepseek-v4-flash")
        self.db_path = os.environ.get("STRATTEST_DB_PATH", "db/strattest.db")
        self.query_timeout = _int_env(
            "STRATTEST_QUERY_TIMEOUT", 30
        )
        self.max_rows = _int_env("STRATTEST_MAX_ROWS", 1000)

    @property
    def db_path_absolute(self):
        repo_root = Path(__file__).parent.parent
        return str(repo_root / self.db_path)
