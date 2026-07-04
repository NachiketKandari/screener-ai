"""FastAPI application factory for the Strattest stock screener backend."""

import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# Ensure repo root is on sys.path so that common/ and screener/ are importable.
_repo_root = Path(__file__).parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


# ---------------------------------------------------------------------------
# JSON logging
# ---------------------------------------------------------------------------

class JsonFormatter(logging.Formatter):
    """Structured JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        now = datetime.now(timezone.utc)
        log_entry: dict = {
            "time": now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z",
            "level": record.levelname,
            "logger": record.name,
        }
        # Custom extra fields set via logger.info("", extra={...})
        if hasattr(record, "extra"):
            log_entry.update(record.extra)
        if record.exc_info and record.exc_info[0]:
            import traceback
            log_entry["traceback"] = "".join(traceback.format_exception(*record.exc_info))
        log_entry["msg"] = record.getMessage()
        return json.dumps(log_entry)


def _setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger("strattest")
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)
    # Capture uvicorn logs in the same format
    logging.getLogger("uvicorn").handlers.clear()
    logging.getLogger("uvicorn").addHandler(handler)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = logging.getLogger("strattest.backend")
    logger.info("Backend starting", extra={"db_path": app.state.db_path})
    yield
    logger.info("Backend shutting down")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    _setup_logging()

    app = FastAPI(title="Strattest API", version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Frontend on Vercel, dev on localhost
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.state.db_path = os.environ.get("STRATTEST_DB_PATH", "db/strattest.db")
    if not os.path.isabs(app.state.db_path):
        app.state.db_path = str(_repo_root / app.state.db_path)

    from backend.routes import screen, filters  # noqa: E402

    app.include_router(screen.router)
    app.include_router(filters.router)

    return app


app = create_app()
