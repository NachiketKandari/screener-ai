from screener.glossary import GLOSSARY


def test_glossary_covers_all_schema_columns():
    """Every column in schema.sql must have a glossary entry."""
    from pathlib import Path

    schema_path = (
        Path(__file__).parent.parent / "data_pipeline" / "schema.sql"
    )
    schema = schema_path.read_text()

    # Extract column names from CREATE TABLE statements
    missing = []
    in_create = False
    for line in schema.split("\n"):
        stripped = line.strip()
        if stripped.startswith("CREATE TABLE"):
            in_create = True
            continue
        if in_create and stripped.startswith(");"):
            in_create = False
            continue
        if in_create and stripped and not stripped.startswith("--") and not stripped.startswith("PRIMARY") and not stripped.startswith(")"):
            # Extract column name (first word before whitespace or comma)
            col = stripped.strip().split()[0].strip(",")
            if col and col not in GLOSSARY:
                missing.append(col)

    # Index columns are excluded — they don't appear in queries
    missing = [m for m in missing if not m.startswith("idx_")]

    assert missing == [], f"Missing glossary entries for: {missing}"


def test_glossary_has_key_columns():
    assert "pe_ratio" in GLOSSARY
    assert "roe_pct" in GLOSSARY
    assert "market_cap_crore" in GLOSSARY
    assert "sector" in GLOSSARY
    assert "ticker" in GLOSSARY
    assert "debt_to_equity" in GLOSSARY
    assert "revenue_growth_pct" in GLOSSARY
    assert "close" in GLOSSARY
    assert "beta" in GLOSSARY


def test_glossary_values_are_strings():
    for k, v in GLOSSARY.items():
        assert isinstance(v, str), f"Glossary entry '{k}' is not a string"
        assert len(v) > 20, f"Glossary entry '{k}' too short: {len(v)} chars"
