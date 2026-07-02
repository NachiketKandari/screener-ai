"""Robust fundamentals backfill with per-stock logging. Run directly: python3 backfill_fundamentals.py"""
import sqlite3, time, sys, os
from pathlib import Path
from datetime import date
import yfinance as yf

sys.stdout.reconfigure(line_buffering=True)

DB_PATH = Path(__file__).parent.parent / "db" / "strattest.db"

with sqlite3.connect(str(DB_PATH)) as conn:
    all_tickers = sorted([r[0] for r in conn.execute("SELECT DISTINCT ticker FROM eod_prices")])
    existing = {r[0] for r in conn.execute("SELECT ticker FROM stock_fundamentals")}

remaining = [t for t in all_tickers if t not in existing]
print(f"Already done: {len(existing)} | Remaining: {len(remaining)}")

BATCH = 200
COOLDOWN_EVERY = 300
COOLDOWN_SECS = 60

inserted = 0
skipped = 0
errors = 0

for i, ticker_name in enumerate(remaining):
    sym = f"{ticker_name}.NS"

    info = None
    for attempt in range(2):
        try:
            t = yf.Ticker(sym)
            info = t.info
            break
        except Exception:
            if attempt == 0:
                time.sleep(3)
            continue

    if not info or info.get("marketCap") is None:
        skipped += 1
        if skipped % 100 == 0:
            print(f"  Skipped {skipped} so far (no mcap), last: {ticker_name}")
    else:
        try:
            def get(key, default=None, scale=1.0):
                val = info.get(key)
                if val is None: return default
                try: return float(val) * scale
                except: return val

            with sqlite3.connect(str(DB_PATH)) as conn:
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
                    (ticker_name, date.today().isoformat(),
                     info.get("longName") or info.get("shortName"),
                     info.get("sector"), info.get("industry"), info.get("exchange"),
                     get("currentPrice"), get("marketCap", scale=1e-7),
                     get("trailingPE"), get("forwardPE"), get("priceToBook"),
                     get("pegRatio"), get("priceToSalesTrailing12Months"),
                     get("returnOnEquity", scale=100), get("returnOnAssets", scale=100),
                     get("profitMargins", scale=100), get("operatingMargins", scale=100),
                     get("grossMargins", scale=100), get("ebitdaMargins", scale=100),
                     get("trailingEps"), get("forwardEps"),
                     get("bookValue"), get("revenuePerShare"),
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
                     get("totalDebt"), get("totalRevenue"), get("ebitda")),
                )
                conn.commit()
            inserted += 1
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  ERROR [{ticker_name}]: {e}")

    total_processed = i + 1
    if total_processed % BATCH == 0:
        pct = total_processed / len(remaining) * 100
        print(f"  {total_processed}/{len(remaining)} ({pct:.0f}%) | inserted={inserted} skipped={skipped} errors={errors}")

    time.sleep(1.5)

    if total_processed % COOLDOWN_EVERY == 0:
        print(f"  Cooldown {COOLDOWN_SECS}s...")
        time.sleep(COOLDOWN_SECS)

print(f"\nDONE: inserted={inserted} skipped={skipped} errors={errors}")

with sqlite3.connect(str(DB_PATH)) as conn:
    f = conn.execute("SELECT COUNT(*) FROM stock_fundamentals").fetchone()[0]
size = os.path.getsize(str(DB_PATH)) / 1024**2
print(f"Total fundamentals: {f} | DB size: {size:.0f}MB")
