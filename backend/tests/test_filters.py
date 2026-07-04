"""Tests for GET /api/filters/options and GET /api/health."""

import os

import pytest
from fastapi.testclient import TestClient


class TestFilterOptions:
    """Filter options endpoint tests."""

    def test_returns_sectors(self, client: TestClient):
        response = client.get("/api/filters/options")
        assert response.status_code == 200
        body = response.json()
        assert "sectors" in body
        assert len(body["sectors"]) == 4
        assert "Consumer Defensive" in body["sectors"]
        assert "Energy" in body["sectors"]
        assert "Financial Services" in body["sectors"]
        assert "Technology" in body["sectors"]

    def test_returns_industries(self, client: TestClient):
        response = client.get("/api/filters/options")
        assert response.status_code == 200
        body = response.json()
        assert "industries" in body
        assert len(body["industries"]) == 4
        assert "Banking" in body["industries"]
        assert "Beverages" in body["industries"]
        assert "Oil & Gas" in body["industries"]
        assert "Software" in body["industries"]

    def test_returns_sort_columns(self, client: TestClient):
        response = client.get("/api/filters/options")
        assert response.status_code == 200
        body = response.json()
        assert "sort_columns" in body
        assert len(body["sort_columns"]) == 10
        # Verify the structure of each entry
        for entry in body["sort_columns"]:
            assert "value" in entry
            assert "label" in entry
        # Spot-check a known column
        values = [sc["value"] for sc in body["sort_columns"]]
        assert "market_cap_crore" in values
        assert "pe_ratio" in values
        assert "roe_pct" in values

    def test_sectors_are_sorted_alphabetically(self, client: TestClient):
        response = client.get("/api/filters/options")
        assert response.status_code == 200
        body = response.json()
        assert body["sectors"] == sorted(body["sectors"])


class TestHealth:
    """Health-check endpoint tests."""

    def test_health_returns_ok(self, client: TestClient):
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["stock_count"] == 5

    def test_health_has_latest_data_date(self, client: TestClient):
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert body["latest_data_date"] is not None
        # Our test data has 2026-07-03 as the max date
        assert "2026-07-03" in body["latest_data_date"]

    def test_health_has_db_size(self, client: TestClient):
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert body["db_size_mb"] is not None
        assert body["db_size_mb"] >= 0

    def test_health_stale_field(self, client: TestClient):
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert "stale" in body
        assert isinstance(body["stale"], bool)
        # Test data date (2026-07-03) is only 1 day old (today is 2026-07-04)
        assert body["stale"] is False

    def test_health_with_missing_db(self, tmp_path):
        """Health check handles missing database gracefully."""
        from backend.main import create_app

        app = create_app()
        app.state.db_path = str(tmp_path / "nonexistent.db")

        from fastapi.testclient import TestClient as TC

        client = TC(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        # Should return error status but not a 500
        assert body["status"] == "error"
