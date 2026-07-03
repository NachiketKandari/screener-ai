"""Assembles the full LLM prompt from schema, glossary, examples, and user query."""

from pathlib import Path

from screener.glossary import GLOSSARY
from screener.examples import EXAMPLES

SCHEMA_PATH = Path(__file__).parent.parent / "data_pipeline" / "schema.sql"

SYSTEM_PROMPT = (
    "You are a SQL generator for a SQLite database of Indian stock market data. "
    "Generate ONLY a SELECT query — no explanations, no markdown, no code fences."
)

SQLITE_RULES = """[SQLITE RULES]
- This is SQLite 3. No RIGHT JOIN, FULL OUTER JOIN, or window functions with RANGE.
- Dates are TEXT in ISO format ('2021-07-02'). Use date('now') for today,
  strftime('%Y-%m-%d', date_col, '+30 days') for arithmetic, julianday() for
  day differences.
- String matching: LIKE is case-insensitive for ASCII. No ILIKE, no REGEXP.
  Use UPPER() or LOWER() only when needed.
- No CONCAT() — use the || operator.
- No IF() — use CASE WHEN ... THEN ... ELSE ... END.
- Aggregation: GROUP_CONCAT() instead of STRING_AGG() or ARRAY_AGG().
- Booleans are 1/0, not TRUE/FALSE.
- Always LIMIT results — never FETCH FIRST or TOP.
- IFNULL() or COALESCE() for null handling, not NVL() or ISNULL().
- No SERIAL, no AUTO_INCREMENT — this is a read-only query, no DDL.
- CRITICAL: Most numeric columns (pe_ratio, roe_pct, debt_to_equity, eps_ttm,
  etc.) are nullable. NULL < X is NULL (not true), so WHERE pe_ratio < 15
  silently excludes stocks with no PE. Always add IS NOT NULL or > 0 when
  filtering nullable columns: WHERE pe_ratio < 15 AND pe_ratio > 0."""


class PromptBuilder:
    def __init__(self, max_examples: int = 3):
        self._schema = SCHEMA_PATH.read_text()
        self._max_examples = max_examples

    def build(self, user_question: str) -> str:
        parts = [
            SYSTEM_PROMPT,
            "",
            SQLITE_RULES,
            "",
            "[DDL]",
            self._schema,
            "",
            "[GLOSSARY]",
            self._build_glossary_section(),
            "",
            "[EXAMPLES]",
            self._build_examples_section(user_question),
            "",
            "[QUESTION]",
            user_question,
        ]
        return "\n".join(parts)

    def _build_glossary_section(self) -> str:
        lines = []
        for col, desc in GLOSSARY.items():
            lines.append(f"{col}: {desc}")
        return "\n".join(lines)

    def _build_examples_section(self, user_question: str) -> str:
        query_lower = user_question.lower()
        scored = []
        for ex in EXAMPLES:
            score = sum(
                1 for tag in ex["tags"] if tag.lower() in query_lower
            )
            scored.append((score, ex))

        scored.sort(key=lambda x: x[0], reverse=True)

        selected = [ex for score, ex in scored[: self._max_examples]]

        if not selected or scored[0][0] == 0:
            selected = EXAMPLES[: self._max_examples]

        lines = []
        for ex in selected:
            lines.append(f'Q: "{ex["question"]}"')
            lines.append(f"SQL: {ex['sql']}")
            lines.append("")
        return "\n".join(lines)
