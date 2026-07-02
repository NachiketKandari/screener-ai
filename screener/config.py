import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            print("Error: DEEPSEEK_API_KEY environment variable is required")
            sys.exit(1)

        self.base_url = os.environ.get(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        )
        self.model = os.environ.get("STRATTEST_MODEL", "deepseek-v4-flash")
        self.db_path = os.environ.get("STRATTEST_DB_PATH", "db/strattest.db")
        self.query_timeout = int(
            os.environ.get("STRATTEST_QUERY_TIMEOUT", "30")
        )
        self.max_rows = int(os.environ.get("STRATTEST_MAX_ROWS", "1000"))

    @property
    def db_path_absolute(self):
        repo_root = Path(__file__).parent.parent
        return str(repo_root / self.db_path)
