# Screener Module — Design Spec

## Overview

Text-to-SQL CLI for stock screening. User asks a natural language question, the system generates SQL via DeepSeek V4 Flash, validates with sqlglot, executes against a read-only SQLite connection, and returns results as a table or CSV.

## Component Layout

```
screener/
  __init__.py
  __main__.py           # python -m screener entrypoint
  cli.py                # argparse + output formatting
  screener.py           # core Screener class (orchestrator)
  prompt_builder.py     # assembles prompt from schema + glossary + examples
  glossary.py           # column glossary with human descriptions + thresholds
  examples.py           # few-shot example registry with keyword tags
  config.py             # env-var config
```

The `Screener` class is the single public entrypoint — CLI calls it now, future API wraps it unchanged.

## Core Flow

```
User: "stocks with PE < 15 and ROE > 20%"
  │
  ▼
cli.py: argparse → screener.query(user_text)
  │
  ▼
Screener.query():
  1. PromptBuilder.build(user_text) → full prompt string
     - glossary.py provides column descriptions with units and thresholds
     - examples.py matches keywords (PE, ROE → valuation examples)
     - injects top 3 matching examples + full DDL + SQLite rules + user question
  2. LLM call (openai SDK → DeepSeek) → raw SQL string
  3. Strip markdown fences, extract SELECT statement
  4. sqlglot.parse(sql) → catch syntax errors
  5. If parse fails → feed error + question → one retry
  6. Open READ-ONLY SQLite connection, 30s timeout
  7. Execute with row limit (1000)
  8. Return (columns, rows) tuple
  │
  ▼
cli.py: format as table (rich) or CSV, print row count to stderr
```

## Prompt Structure

### System message

```
You are a SQL generator for a SQLite database of Indian stock market data.
Generate ONLY a SELECT query — no explanations, no markdown, no code fences.
```

### SQLite rules

- TEXT dates in ISO format. Use `date('now')`, `strftime()`, `julianday()`.
- LIKE is case-insensitive for ASCII. No ILIKE, no REGEXP.
- No CONCAT() — use `||`.
- No IF() — use `CASE WHEN ... END`.
- Booleans are 1/0, not TRUE/FALSE.
- Always LIMIT, never FETCH FIRST or TOP.
- IFNULL() or COALESCE() for nulls, not NVL() or ISNULL().
- No RIGHT JOIN or FULL OUTER JOIN.

### Full DDL

Injected from `data_pipeline/schema.sql` — both tables with all columns, indexes, and comments.

### Glossary

Column-by-column descriptions including:
- What the column represents
- Units (e.g., market_cap_crore is in ₹ crore, percentage columns are already ×100)
- Common thresholds (PE < 15 = value, ROE > 15 = good)
- Gotchas (NULL PE for unprofitable companies, sector uses exact values)
- Join semantics (ticker joins to eod_prices)

### Examples

3 few-shot examples selected by keyword overlap with user question. Each stored as `(question, sql, tags)` tuple in `examples.py`.

## Config

All via environment variables (loaded from `.env`):

| Variable | Default | Description |
|---|---|---|
| DEEPSEEK_API_KEY | (required) | DeepSeek API key |
| DEEPSEEK_BASE_URL | https://api.deepseek.com | API endpoint |
| STRATTEST_MODEL | deepseek-v4-flash | Model name |
| STRATTEST_DB_PATH | db/strattest.db | Database path, relative to repo root |
| STRATTEST_QUERY_TIMEOUT | 30 | Query timeout in seconds |
| STRATTEST_MAX_ROWS | 1000 | Max result rows |

## Error Handling

| Failure | Behavior | Exit code |
|---|---|---|
| API error (network, auth, rate limit) | Print error, exit | 1 |
| sqlglot parse failure | Retry once with error context; if still fails, print both attempts + error, exit | 2 |
| SQLite execute error | Print SQL + SQLite error, exit | 3 |
| Query timeout (30s) | Print SQL, suggest narrowing, exit | 4 |
| 0 results | Print "No stocks matched." + the SQL used | 0 |
| Success | Format results, print row count to stderr | 0 |

## CLI Interface

```
python -m screener [--format table|csv] [--limit N] "natural language query"
```

- `--format table` (default): rich-formatted terminal table
- `--format csv`: machine-readable CSV
- `--limit N`: override the default 1000 row cap

## Dependencies

Added to `requirements.txt`:
```
openai>=1.0.0        # DeepSeek API via OpenAI SDK
rich>=13.0.0         # formatted terminal output
python-dotenv>=1.0.0 # .env loading
```

Existing: `sqlglot`, `pandas` (both already in project).

## Testing

- `screener/test_prompt_builder.py` — verify DDL injection, example selection, glossary completeness
- `screener/test_glossary.py` — every schema column has a glossary entry
- Manual smoke test: `python -m screener "banks with PE under 15 and ROE above 15"` against real DB
