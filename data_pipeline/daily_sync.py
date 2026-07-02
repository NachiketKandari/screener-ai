"""Daily EOD sync: update today's OHLCV + refresh fundamentals weekly."""

import sqlite3
import time
from datetime import datetime, date, timedelta
from pathlib import Path

import yfinance as yf


DB_PATH = Path(__file__).parent.parent / "db" / "strattest.db"
BATCH_SIZE = 50
FUNDAMENTALS_REFRESH_DAYS = 7  # Refresh fundamentals weekly


def get_tracked_tickers():
    """Get all tickers already in the database."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.execute("SELECT DISTINCT ticker FROM eod_prices")
        return sorted([row[0] for row in cursor.fetchall()])


def get_last_date():
    """Get the most recent date in eod_prices."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.execute("SELECT MAX(date) FROM eod_prices")
        return cursor.fetchone()[0]


def sync_ohlcv(tickers: list[str]):
    """Sync OHLCV for all tracked tickers from last known date to today."""
    last_date = get_last_date()
    today = date.today().isoformat()

    if last_date == today:
        print(f"Already up to date ({today}).")
        return

    # Only pull days we're missing (yfinance handles this with start=)
    start = (date.fromisoformat(last_date) + timedelta(days=1)).isoformat()
    print(f"OHLCV sync: {start} → {today}")

    yf_symbols = [f"{t}.NS" for t in tickers]

    with sqlite3.connect(str(DB_PATH)) as conn:
        for batch_idx in range(0, len(yf_symbols), BATCH_SIZE):
            batch = yf_symbols[batch_idx : batch_idx + BATCH_SIZE]

            try:
                df = yf.download(
                    batch,
                    start=start,
                    progress=False,
                    auto_adjust=True,
                    group_by="ticker",
                    threads=True,
                )
            except Exception as e:
                print(f"  Batch error: {e}, skipping")
                continue

            if df.empty:
                continue

            rows = 0
            for sym in batch:
                ticker_name = sym.replace(".NS", "")
                try:
                    stock_df = df[sym] if len(batch) > 1 else df
                    if stock_df.empty:
                        continue
                    for idx, row in stock_df.iterrows():
                        def scalar(val, default=None):
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
                        rows += 1
                except Exception as e:
                    continue

            conn.commit()
            print(f"  Batch {batch_idx // BATCH_SIZE + 1}: {rows} rows")

    print("OHLCV sync complete.")


def should_refresh_fundamentals():
    """Check if fundamentals need a refresh (weekly)."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.execute("SELECT MAX(as_of_date) FROM stock_fundamentals")
        last = cursor.fetchone()[0]
        if not last:
            return True
        last_date = date.fromisoformat(last)
        return (date.today() - last_date).days >= FUNDAMENTALS_REFRESH_DAYS


def sync_fundamentals(tickers: list[str]):
    """Refresh fundamentals for all tracked tickers."""
    if not should_refresh_fundamentals():
        print("Fundamentals refresh not due yet (weekly cadence).")
        return

    print(f"Refreshing fundamentals for {len(tickers)} stocks...")
    today = date.today().isoformat()

    with sqlite3.connect(str(DB_PATH)) as conn:
        for i, t in enumerate(tickers):
            sym = f"{t}.NS"
            try:
                info = yf.Ticker(sym).info
                if not info or not info.get("marketCap"):
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
                    """UPDATE stock_fundamentals SET
                       as_of_date=?, company_name=?, sector=?, industry=?, exchange=?,
                       current_price=?, market_cap_crore=?, pe_ratio=?, forward_pe=?, pb_ratio=?,
                       peg_ratio=?, price_to_sales=?,
                       roe_pct=?, roa_pct=?, profit_margins_pct=?, operating_margins_pct=?,
                       gross_margins_pct=?, ebitda_margins_pct=?,
                       eps_ttm=?, eps_forward=?, book_value_per_share=?, revenue_per_share=?,
                       revenue_growth_pct=?, earnings_growth_pct=?, earnings_quarterly_growth_pct=?,
                       debt_to_equity=?, current_ratio=?, quick_ratio=?, payout_ratio=?,
                       dividend_yield_pct=?, five_year_avg_dividend_yield_pct=?,
                       high_52w=?, low_52w=?, beta=?,
                       target_mean_price=?, target_high_price=?, target_low_price=?,
                       recommendation=?, number_of_analysts=?,
                       held_pct_insiders=?, held_pct_institutions=?,
                       free_cashflow=?, operating_cashflow=?, total_cash_per_share=?,
                       total_debt=?, total_revenue=?, ebitda=?
                       WHERE ticker=?""",
                    (
                        today, info.get("longName") or info.get("shortName"),
                        info.get("sector"), info.get("industry"), info.get("exchange"),
                        get("currentPrice"), get("marketCap", scale=1e-7),
                        get("trailingPE"), get("forwardPE"), get("priceToBook"),
                        get("pegRatio"), get("priceToSalesTrailing12Months"),
                        get("returnOnEquity", scale=100), get("returnOnAssets", scale=100),
                        get("profitMargins", scale=100), get("operatingMargins", scale=100),
                        get("grossMargins", scale=100), get("ebitdaMargins", scale=100),
                        get("trailingEps"), get("forwardEps"), get("bookValue"),
                        get("revenuePerShare"),
                        get("revenueGrowth", scale=100), get("earningsGrowth", scale=100),
                        get("earningsQuarterlyGrowth", scale=100),
                        get("debtToEquity"), get("currentRatio"), get("quickRatio"),
                        get("payoutRatio"),
                        get("dividendYield", scale=100), get("fiveYearAvgDividendYield", scale=100),
                        get("fiftyTwoWeekHigh"), get("fiftyTwoWeekLow"), get("beta"),
                        get("targetMeanPrice"), get("targetHighPrice"), get("targetLowPrice"),
                        info.get("recommendationKey"), info.get("numberOfAnalystOpinions"),
                        get("heldPercentInsiders", scale=100), get("heldPercentInstitutions", scale=100),
                        get("freeCashflow"), get("operatingCashflow"), get("totalCashPerShare"),
                        get("totalDebt"), get("totalRevenue"), get("ebitda"),
                        t,
                    ),
                )

                if (i + 1) % 100 == 0:
                    conn.commit()
                    print(f"  {i + 1}/{len(tickers)} refreshed")

            except Exception as e:
                continue

            time.sleep(0.3)

        conn.commit()
    print("Fundamentals sync complete.")


def main():
    print(f"Strattest Daily Sync — {datetime.now().isoformat()}")
    print()

    tickers = get_tracked_tickers()
    if not tickers:
        print("No tickers in database. Run backfill.py first.")
        return

    print(f"Tracking {len(tickers)} stocks")
    print()

    print("=== OHLCV Sync ===")
    sync_ohlcv(tickers)

    print("\n=== Fundamentals Sync ===")
    sync_fundamentals(tickers)

    # Print summary
    with sqlite3.connect(str(DB_PATH)) as conn:
        rows = conn.execute("SELECT COUNT(*) FROM eod_prices").fetchone()[0]
        latest = conn.execute("SELECT MAX(date) FROM eod_prices").fetchone()[0]
    print(f"\nDone. {rows:,} OHLCV rows, latest date: {latest}")


if __name__ == "__main__":
    main()
