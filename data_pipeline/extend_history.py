"""Extend OHLCV history to 10 years + catch up recent days.

Uses yfinance's period="max" (like backfill.py) rather than start/end dates,
which is more robust — yfinance returns whatever data exists per ticker.
INSERT OR REPLACE handles deduplication.
"""

import sys
import time
from datetime import datetime, date
from pathlib import Path

import yfinance as yf

_repo_root = Path(__file__).parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from common.database import get_connection

DB_PATH = Path(__file__).parent.parent / "db" / "strattest.db"
BATCH_SIZE = 50
BATCH_DELAY = 2


def get_tracked_tickers():
    with get_connection(str(DB_PATH), readonly=True) as conn:
        return sorted([row[0] for row in conn.execute("SELECT DISTINCT ticker FROM eod_prices")])


def store_batch(conn, df, batch_symbols):
    """Store a downloaded DataFrame into eod_prices."""
    rows = 0
    for sym in batch_symbols:
        ticker_name = sym.replace(".NS", "")
        try:
            stock_df = df[sym] if len(batch_symbols) > 1 else df
            if stock_df.empty or stock_df.dropna(how="all").empty:
                continue
            for idx, row in stock_df.iterrows():
                def s(val, default=None):
                    if val is None:
                        return default
                    if hasattr(val, 'iloc'):
                        return val.iloc[0] if len(val) > 0 else default
                    return val

                conn.execute(
                    """INSERT OR REPLACE INTO eod_prices
                       (ticker, date, open, high, low, close, volume, dividends, stock_splits)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        ticker_name, idx.strftime("%Y-%m-%d"),
                        s(row["Open"]), s(row["High"]), s(row["Low"]),
                        s(row["Close"]), s(row["Volume"]),
                        s(row.get("Dividends"), 0), s(row.get("Stock Splits"), 0),
                    ),
                )
                rows += 1
        except Exception:
            continue
    return rows


def extend_all(tickers: list[str]):
    """Download full history (period=max) for all tickers in batches."""
    yf_symbols = [f"{t}.NS" for t in tickers]
    total_batches = (len(yf_symbols) + BATCH_SIZE - 1) // BATCH_SIZE
    total_rows = 0

    with get_connection(str(DB_PATH), readonly=False) as conn:
        for batch_idx in range(0, len(yf_symbols), BATCH_SIZE):
            batch = yf_symbols[batch_idx : batch_idx + BATCH_SIZE]
            batch_num = batch_idx // BATCH_SIZE + 1

            try:
                df = yf.download(
                    batch,
                    period="10y",
                    progress=False,
                    auto_adjust=True,
                    group_by="ticker",
                    threads=True,
                )
            except Exception as e:
                print(f"  Batch {batch_num}/{total_batches}: error {e}, retrying after 5s...")
                time.sleep(5)
                try:
                    df = yf.download(batch, period="10y", progress=False, auto_adjust=True, group_by="ticker", threads=True)
                except Exception as e2:
                    print(f"  Batch {batch_num}/{total_batches}: failed again, skipping")
                    continue

            if df.empty:
                print(f"  Batch {batch_num}/{total_batches}: empty, skipping")
                continue

            rows = store_batch(conn, df, batch)
            conn.commit()
            conn.sync()
            total_rows += rows
            pct = min(100, (batch_idx + BATCH_SIZE) / len(yf_symbols) * 100)
            print(f"  Batch {batch_num}/{total_batches}: {len(batch)} stocks, {rows} rows ({pct:.0f}%)")
            time.sleep(BATCH_DELAY)

    return total_rows


def main():
    print(f"Strattest History Extension — {datetime.now().isoformat()}\n")

    tickers = get_tracked_tickers()
    print(f"Extending history for {len(tickers)} tickers (period=max, ~10yr where available)\n")
    print(f"~{len(tickers) // BATCH_SIZE} batches, ~{len(tickers) // BATCH_SIZE * BATCH_DELAY // 60}min estimated\n")

    n = extend_all(tickers)

    with get_connection(str(DB_PATH), readonly=True) as conn:
        total_rows = conn.execute("SELECT COUNT(*) FROM eod_prices").fetchone()[0]
        dr = conn.execute("SELECT MIN(date), MAX(date) FROM eod_prices").fetchone()
    print(f"\nDone. {n:,} new rows stored. Total: {total_rows:,} rows, range: {dr[0]} → {dr[1]}")


if __name__ == "__main__":
    main()
