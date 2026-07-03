"""Core orchestrator: build prompt -> LLM -> validate -> execute."""

import re
import sqlite3
from typing import Any

import sqlglot
import sqlglot.expressions as exp

from screener.config import Config
from screener.prompt_builder import PromptBuilder


class QueryError(Exception):
    def __init__(self, message: str, exit_code: int, sql: str | None = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.sql = sql


class Screener:
    def __init__(
        self,
        config: Config,
        prompt_builder: PromptBuilder | None = None,
        llm_callable=None,
    ):
        self._cfg = config
        self._prompt_builder = prompt_builder or PromptBuilder()
        self.warnings: list[str] = []
        if llm_callable is not None:
            self._llm = llm_callable
        else:
            self._llm = lambda prompt: _llm_call(
                prompt,
                api_key=self._cfg.api_key,
                base_url=self._cfg.base_url,
                model=self._cfg.model,
            )

    def query(self, user_question: str) -> tuple[tuple[str, ...], list[tuple[Any, ...]]]:
        prompt = self._prompt_builder.build(user_question)

        # Attempt 1
        raw = self._llm(prompt)
        sql = _extract_sql(raw)

        # Validate and possibly retry
        try:
            sqlglot.parse(sql)
        except Exception as parse_err:
            retry_prompt = (
                prompt
                + f"\n\nYour previous SQL had a syntax error: {parse_err}\n"
                + "Generate corrected SQL. Output ONLY the SQL, no explanations."
            )
            raw = self._llm(retry_prompt)
            sql = _extract_sql(raw)
            try:
                sqlglot.parse(sql)
            except Exception as parse_err2:
                raise QueryError(
                    f"Syntax error after retry: {parse_err2}\n\n"
                    f"SQL attempted:\n{sql}",
                    exit_code=2,
                    sql=sql,
                )

        # Safety: only SELECT
        if not sql.strip().upper().startswith("SELECT"):
            raise QueryError(
                f"Non-SELECT statement rejected.\n\nSQL:\n{sql}",
                exit_code=3,
                sql=sql,
            )

        self.warnings = _check_null_safety(sql)

        # Execute
        try:
            conn = sqlite3.connect(
                f"file:{self._cfg.db_path_absolute}?mode=ro", uri=True
            )
            conn.execute("PRAGMA query_only = ON")
        except sqlite3.OperationalError as e:
            raise QueryError(
                f"Cannot open database: {e}", exit_code=3, sql=sql
            )

        try:
            conn.execute(f"PRAGMA busy_timeout = {self._cfg.query_timeout * 1000}")
            # Add LIMIT if not present
            if "LIMIT" not in sql.upper():
                sql = sql.rstrip(";") + f" LIMIT {self._cfg.max_rows}"
            cursor = conn.execute(sql)
            columns = tuple(d[0] for d in cursor.description) if cursor.description else ()
            rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            raise QueryError(
                f"Query execution failed: {e}\n\nSQL:\n{sql}",
                exit_code=3,
                sql=sql,
            )
        finally:
            conn.close()

        return columns, rows


def _extract_sql(raw: str) -> str:
    """Extract SQL from LLM response, stripping markdown fences if present."""
    s = raw.strip()
    # Remove ```sql ... ``` or ``` ... ``` fences
    m = re.search(r"```(?:sql)?\s*\n?(.*?)```", s, re.DOTALL)
    if m:
        s = m.group(1).strip()
    return s


def _llm_call(
    prompt: str,
    api_key: str,
    base_url: str,
    model: str,
) -> str:
    """Call DeepSeek via OpenAI-compatible SDK."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )
    return response.choices[0].message.content


# Columns that frequently have NULL in the data (all fundamentals except identity)
_NULLABLE_COLUMNS = frozenset({
    "pe_ratio", "forward_pe", "pb_ratio", "peg_ratio", "price_to_sales",
    "eps_ttm", "eps_forward", "book_value_per_share", "revenue_per_share",
    "roe_pct", "roa_pct", "profit_margins_pct", "operating_margins_pct",
    "gross_margins_pct", "ebitda_margins_pct",
    "revenue_growth_pct", "earnings_growth_pct", "earnings_quarterly_growth_pct",
    "debt_to_equity", "current_ratio", "quick_ratio", "payout_ratio",
    "dividend_yield_pct", "five_year_avg_dividend_yield_pct",
    "beta",
    "target_mean_price", "target_high_price", "target_low_price",
    "recommendation", "number_of_analysts",
    "held_pct_insiders", "held_pct_institutions",
    "free_cashflow", "operating_cashflow", "total_cash_per_share",
    "total_debt", "total_revenue", "ebitda",
})


def _check_null_safety(sql: str) -> list[str]:
    """Check WHERE clause for nullable columns used without IS NOT NULL / > 0 guards."""
    try:
        tree = sqlglot.parse_one(sql)
    except Exception:
        return []

    where = tree.find(exp.Where)
    if not where:
        return []

    columns: set[str] = set()
    guarded: set[str] = set()

    for node in where.walk():
        if isinstance(node, exp.Column):
            col = node.name.lower()
            if col in _NULLABLE_COLUMNS:
                columns.add(col)
        elif isinstance(node, exp.Is):
            if isinstance(node.this, exp.Column):
                guarded.add(node.this.name.lower())
        elif isinstance(node, (exp.GT, exp.GTE)):
            if isinstance(node.left, exp.Column) and _is_zero(node.right):
                guarded.add(node.left.name.lower())

    unguarded = columns - guarded
    if not unguarded:
        return []

    return [
        f"'{c}' used in WHERE without IS NOT NULL or > 0 "
        f"— rows with NULL {c} are silently excluded"
        for c in sorted(unguarded)
    ]


def _is_zero(node: exp.Expression) -> bool:
    return isinstance(node, exp.Literal) and node.this in ("0", "0.0")
