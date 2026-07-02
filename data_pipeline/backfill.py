"""One-time backfill: pull 5-year OHLCV + fundamentals for all NSE stocks via yfinance."""

import sqlite3
import time
import sys
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import yfinance as yf
from nselib import capital_market


DB_PATH = Path(__file__).parent.parent / "db" / "strattest.db"
BATCH_SIZE = 50
BATCH_DELAY = 2  # seconds between batches to avoid rate limiting
STOCK_DELAY = 0.3  # seconds between individual stock info calls


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    schema = Path(__file__).parent / "schema.sql"
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.executescript(schema.read_text())
        conn.commit()
    print(f"Database initialized at {DB_PATH}")


def get_ticker_list():
    """Get all NSE equity symbols from nselib."""
    try:
        df = capital_market.equity_list()
        tickers = df["SYMBOL"].str.strip().tolist()
        print(f"Got {len(tickers)} tickers from NSE equity list")
        return tickers
    except Exception as e:
        print(f"nselib failed: {e}, loading from cached CSV")
        csv = Path(__file__).parent / "nse_tickers.csv"
        if csv.exists():
            df = pd.read_csv(csv)
            tickers = df["SYMBOL"].str.strip().tolist()
            print(f"Got {len(tickers)} tickers from cached CSV")
            return tickers
        raise RuntimeError("No ticker list available")


def already_done():
    """Return set of tickers already backfilled (to support resume)."""
    if not DB_PATH.exists():
        return set()
    with sqlite3.connect(str(DB_PATH)) as conn:
        try:
            cursor = conn.execute("SELECT DISTINCT ticker FROM eod_prices")
            return {row[0] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            return set()


def backfill_ohlcv(tickers: list[str]):
    """Pull 5-year OHLCV for all tickers, store in eod_prices."""
    done = already_done()
    remaining = [t for t in tickers if t not in done]
    print(f"OHLCV backfill: {len(done)} already done, {len(remaining)} remaining")

    if not remaining:
        print("OHLCV backfill complete — nothing to do.")
        return

    total_batches = (len(remaining) + BATCH_SIZE - 1) // BATCH_SIZE
    yf_symbols = [f"{t}.NS" for t in remaining]

    with sqlite3.connect(str(DB_PATH)) as conn:
        for batch_idx in range(0, len(yf_symbols), BATCH_SIZE):
            batch = yf_symbols[batch_idx : batch_idx + BATCH_SIZE]
            batch_num = batch_idx // BATCH_SIZE + 1

            try:
                df = yf.download(
                    batch,
                    period="5y",
                    progress=False,
                    auto_adjust=True,
                    group_by="ticker",
                    threads=True,
                )
            except Exception as e:
                print(f"  Batch {batch_num}/{total_batches}: download error {e}, retrying after 5s...")
                time.sleep(5)
                try:
                    df = yf.download(batch, period="5y", progress=False, auto_adjust=True, group_by="ticker", threads=True)
                except Exception as e2:
                    print(f"  Batch {batch_num}/{total_batches}: failed again, skipping. {e2}")
                    continue

            if df.empty:
                print(f"  Batch {batch_num}/{total_batches}: empty response, skipping")
                continue

            rows_inserted = 0
            for sym in batch:
                ticker_name = sym.replace(".NS", "")
                try:
                    if len(batch) == 1:
                        stock_df = df
                    else:
                        stock_df = df[sym]

                    if stock_df.empty or stock_df.dropna(how="all").empty:
                        continue

                    for idx, row in stock_df.iterrows():
                        def scalar(val, default=None):
                            """Extract scalar from Series or return as-is."""
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
                                ticker_name,
                                idx.strftime("%Y-%m-%d"),
                                scalar(row["Open"]),
                                scalar(row["High"]),
                                scalar(row["Low"]),
                                scalar(row["Close"]),
                                scalar(row["Volume"]),
                                scalar(row.get("Dividends"), 0),
                                scalar(row.get("Stock Splits"), 0),
                            ),
                        )
                        rows_inserted += 1
                except Exception as e:
                    print(f"    {ticker_name}: error: {e}")
                    continue

            conn.commit()
            pct = min(100, (batch_idx + BATCH_SIZE) / len(yf_symbols) * 100)
            print(f"  Batch {batch_num}/{total_batches}: {len(batch)} stocks, {rows_inserted} rows "
                  f"({pct:.0f}%)")
            time.sleep(BATCH_DELAY)

    print("OHLCV backfill complete.")


def backfill_fundamentals(tickers: list[str]):
    """Pull fundamentals (.info) for all tickers, store in stock_fundamentals."""
    total = len(tickers)
    print(f"Fundamentals backfill: {total} stocks")

    # Check which tickers already have fundamentals
    existing = set()
    if DB_PATH.exists():
        with sqlite3.connect(str(DB_PATH)) as conn:
            try:
                cursor = conn.execute("SELECT ticker FROM stock_fundamentals")
                existing = {row[0] for row in cursor.fetchall()}
            except sqlite3.OperationalError:
                pass

    yf_symbols = [f"{t}.NS" for t in tickers if t not in existing]
    skipped = total - len(yf_symbols)
    if skipped:
        print(f"  {skipped} already processed, {len(yf_symbols)} remaining")

    if not yf_symbols:
        print("Fundamentals backfill complete — nothing to do.")
        return

    FUNDA_DELAY = 1.5  # seconds between calls to avoid rate limiting
    BATCH_BREAK_EVERY = 200  # take a longer break every N stocks
    BATCH_BREAK_SECS = 30

    with sqlite3.connect(str(DB_PATH)) as conn:
        for i, sym in enumerate(yf_symbols):
            ticker_name = sym.replace(".NS", "")

            # Retry up to 3 times with backoff
            info = None
            for attempt in range(3):
                try:
                    t = yf.Ticker(sym)
                    info = t.info
                    if info and info.get("marketCap"):
                        break
                except Exception as e:
                    if attempt < 2:
                        wait = 5 * (attempt + 1)
                        time.sleep(wait)
                    continue

            if not info or info.get("marketCap") is None:
                continue

                def get(key, default=None, scale=1.0):
                    val = info.get(key)
                    if val is None:
                        return default
                    try:
                        return float(val) * scale
                    except (ValueError, TypeError):
                        return val

                conn.execute(
                    """INSERT OR REPLACE INTO stock_fundamentals
                       (ticker, as_of_date, company_name, sector, industry, exchange,
                        current_price, market_cap_crore, pe_ratio, forward_pe, pb_ratio,
                        peg_ratio, price_to_sales,
                        roe_pct, roa_pct, profit_margins_pct, operating_margins_pct,
                        gross_margins_pct, ebitda_margins_pct,
                        eps_ttm, eps_forward, book_value_per_share, revenue_per_share,
                        revenue_growth_pct, earnings_growth_pct, earnings_quarterly_growth_pct,
                        debt_to_equity, current_ratio, quick_ratio, payout_ratio,
                        dividend_yield_pct, five_year_avg_dividend_yield_pct,
                        high_52w, low_52w, beta,
                        target_mean_price, target_high_price, target_low_price,
                        recommendation, number_of_analysts,
                        held_pct_insiders, held_pct_institutions,
                        free_cashflow, operating_cashflow, total_cash_per_share,
                        total_debt, total_revenue, ebitda)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                               ?, ?, ?, ?, ?, ?,
                               ?, ?, ?, ?,
                               ?, ?, ?,
                               ?, ?, ?, ?,
                               ?, ?,
                               ?, ?, ?,
                               ?, ?, ?,
                               ?, ?,
                               ?, ?,
                               ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        ticker_name,
                        date.today().isoformat(),
                        info.get("longName") or info.get("shortName"),
                        info.get("sector"),
                        info.get("industry"),
                        info.get("exchange"),
                        get("currentPrice"),
                        get("marketCap", scale=1e-7),
                        get("trailingPE"),
                        get("forwardPE"),
                        get("priceToBook"),
                        get("pegRatio"),
                        get("priceToSalesTrailing12Months"),
                        get("returnOnEquity", scale=100),
                        get("returnOnAssets", scale=100),
                        get("profitMargins", scale=100),
                        get("operatingMargins", scale=100),
                        get("grossMargins", scale=100),
                        get("ebitdaMargins", scale=100),
                        get("trailingEps"),
                        get("forwardEps"),
                        get("bookValue"),
                        get("revenuePerShare"),
                        get("revenueGrowth", scale=100),
                        get("earningsGrowth", scale=100),
                        get("earningsQuarterlyGrowth", scale=100),
                        get("debtToEquity"),
                        get("currentRatio"),
                        get("quickRatio"),
                        get("payoutRatio"),
                        get("dividendYield", scale=100),
                        get("fiveYearAvgDividendYield", scale=100),
                        get("fiftyTwoWeekHigh"),
                        get("fiftyTwoWeekLow"),
                        get("beta"),
                        get("targetMeanPrice"),
                        get("targetHighPrice"),
                        get("targetLowPrice"),
                        info.get("recommendationKey"),
                        info.get("numberOfAnalystOpinions"),
                        get("heldPercentInsiders", scale=100),
                        get("heldPercentInstitutions", scale=100),
                        get("freeCashflow"),
                        get("operatingCashflow"),
                        get("totalCashPerShare"),
                        get("totalDebt"),
                        get("totalRevenue"),
                        get("ebitda"),
                    ),
                )

                if (i + 1) % 50 == 0 or i == len(yf_symbols) - 1:
                    conn.commit()
                    print(f"  {i + 1}/{len(yf_symbols)} fundamentals done ({(i + 1) / len(yf_symbols) * 100:.0f}%)")

            time.sleep(FUNDA_DELAY)

            # Longer break every BATCH_BREAK_EVERY to let Yahoo cool down
            if (i + 1) % BATCH_BREAK_EVERY == 0:
                print(f"  Cooling down for {BATCH_BREAK_SECS}s...")
                time.sleep(BATCH_BREAK_SECS)

    print("Fundamentals backfill complete.")


def print_summary():
    with sqlite3.connect(str(DB_PATH)) as conn:
        stocks = conn.execute("SELECT COUNT(DISTINCT ticker) FROM eod_prices").fetchone()[0]
        rows = conn.execute("SELECT COUNT(*) FROM eod_prices").fetchone()[0]
        daterange = conn.execute(
            "SELECT MIN(date), MAX(date) FROM eod_prices"
        ).fetchone()
        funda = conn.execute("SELECT COUNT(*) FROM stock_fundamentals").fetchone()[0]

    db_size_mb = DB_PATH.stat().st_size / 1024**2 if DB_PATH.exists() else 0

    print(f"\n{'='*60}")
    print(f"BACKFILL SUMMARY")
    print(f"{'='*60}")
    print(f"Stocks with OHLCV:  {stocks}")
    print(f"Total OHLCV rows:   {rows:,}")
    print(f"Date range:          {daterange[0]} → {daterange[1]}")
    print(f"Fundamentals rows:   {funda}")
    print(f"Database size:       {db_size_mb:.1f} MB")


def main():
    print("Strattest Data Backfill")
    print(f"Started: {datetime.now().isoformat()}")
    print()

    init_db()
    tickers = get_ticker_list()

    # Filter out problematic symbols (special characters, too short, etc.)
    tickers = [t for t in tickers if t and len(t) >= 2 and t.isascii()]
    print(f"Valid tickers: {len(tickers)}")
    print()

    print("=== PHASE 1: OHLCV History ===")
    backfill_ohlcv(tickers)

    print("\n=== PHASE 2: Fundamentals ===")
    backfill_fundamentals(tickers)

    print_summary()


if __name__ == "__main__":
    main()
