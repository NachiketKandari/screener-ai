"""CLI: argument parsing and output formatting."""

import argparse
import csv
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from screener.config import Config, ConfigError
from screener.screener import Screener, QueryError


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="screener",
        description="Text-to-SQL stock screening for Indian markets.",
    )
    parser.add_argument(
        "query",
        nargs="+",
        help="Natural language screening query (e.g. 'stocks with PE < 15 and ROE > 20%%')",
    )
    parser.add_argument(
        "--format",
        choices=["table", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max rows to return (overrides STRATTEST_MAX_ROWS)",
    )
    args = parser.parse_args()

    user_question = " ".join(args.query)

    try:
        cfg = Config()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.limit is not None:
        cfg.max_rows = args.limit

    screener = Screener(cfg)

    try:
        columns, rows = screener.query(user_question)
    except QueryError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(e.exit_code)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not rows:
        if screener.warnings:
            for w in screener.warnings:
                print(f"Warning: {w}", file=sys.stderr)
        print("No stocks matched.", file=sys.stderr)
        sys.exit(0)

    if args.format == "csv":
        _format_csv(columns, rows)
    else:
        _format_table(columns, rows)

    print(f"{len(rows)} rows", file=sys.stderr)
    if screener.warnings:
        for w in screener.warnings:
            print(f"Warning: {w}", file=sys.stderr)
    sys.exit(0)


def _format_csv(columns, rows):
    writer = csv.writer(sys.stdout)
    writer.writerow(columns)
    writer.writerows(rows)


def _format_table(columns, rows):
    console = Console()
    table = Table(title="Screener Results")

    for col in columns:
        table.add_column(col, no_wrap=False)

    for row in rows:
        table.add_row(*[_fmt_cell(v) for v in row])

    console.print(table)


def _fmt_cell(value):
    if value is None:
        return "—"
    if isinstance(value, float):
        s = f"{value:.2f}".rstrip("0").rstrip(".")
        return s
    return str(value)
