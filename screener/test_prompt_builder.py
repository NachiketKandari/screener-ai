from screener.prompt_builder import PromptBuilder


def test_build_includes_system_message():
    pb = PromptBuilder()
    prompt = pb.build("test query")
    assert "SQL generator" in prompt
    assert "Indian stock market" in prompt


def test_build_includes_sqlite_rules():
    pb = PromptBuilder()
    prompt = pb.build("test query")
    assert "No RIGHT JOIN" in prompt
    assert "No CONCAT()" in prompt
    assert "IFNULL() or COALESCE()" in prompt
    assert "Always LIMIT" in prompt


def test_build_includes_ddl():
    pb = PromptBuilder()
    prompt = pb.build("test query")
    assert "CREATE TABLE" in prompt
    assert "eod_prices" in prompt
    assert "stock_fundamentals" in prompt


def test_build_includes_glossary():
    pb = PromptBuilder()
    prompt = pb.build("test query")
    assert "pe_ratio" in prompt
    assert "roe_pct" in prompt


def test_build_includes_user_question():
    pb = PromptBuilder()
    prompt = pb.build("find cheap banks with low debt")
    assert "find cheap banks with low debt" in prompt


def test_build_includes_examples():
    pb = PromptBuilder()
    prompt = pb.build("stocks with PE under 15 and growth above 20%")
    assert "[EXAMPLES]" in prompt
    assert "pe_ratio" in prompt.lower()


def test_example_selection_falls_back_for_unmatched_query():
    pb = PromptBuilder()
    prompt = pb.build("xyzzy flurbo glarp")
    assert "[EXAMPLES]" in prompt
    assert "SELECT" in prompt


def test_promptbuilder_uses_schema_from_data_pipeline():
    pb = PromptBuilder()
    prompt = pb.build("test")
    assert "PRIMARY KEY (ticker, date)" in prompt


def test_build_includes_limit_instruction():
    pb = PromptBuilder()
    prompt = pb.build("test query")
    assert "LIMIT" in prompt
