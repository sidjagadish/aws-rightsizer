"""
Unit tests for /api/db/ping health-check endpoint.

Place at: server/tests/test_db_ping.py
Run:      poetry run pytest tests/test_db_ping.py -v -s
Deps:     poetry add --group dev pytest httpx
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import get_db
from app.api.db import check_lists


# ── Unit tests for check_lists helper ────────────────────────────

class TestCheckLists:

    def test_identical_lists(self):
        assert check_lists(["a", "b"], ["a", "b"]) == []

    def test_items_missing_from_second_list(self):
        result = check_lists(["a", "b", "c"], ["a"])
        assert set(result) == {"b", "c"}

    def test_extra_items_in_second_list_ignored(self):
        assert check_lists(["a"], ["a", "b", "c"]) == []

    def test_both_empty(self):
        assert check_lists([], []) == []

    def test_first_empty(self):
        assert check_lists([], ["a", "b"]) == []

    def test_second_empty(self):
        result = check_lists(["a", "b"], [])
        assert set(result) == {"a", "b"}

    def test_no_overlap(self):
        result = check_lists(["a", "b"], ["c", "d"])
        assert set(result) == {"a", "b"}


# ── Endpoint tests ───────────────────────────────────────────────

client = TestClient(app)

# The five tables defined in app/models/
ALL_APP_TABLES = [
    "scan_run",
    "ec2_instance",
    "utilization_metric",
    "finding",
    "recommendation",
]


def _make_fake_db(fake_table_rows: list[str]):
    """
    Return a FastAPI dependency override for get_db.
    The yielded mock session handles SELECT 1 and information_schema.
    """
    def override():
        mock_session = MagicMock()

        def execute_side_effect(stmt):
            result = MagicMock()
            if "information_schema" in str(stmt):
                result.scalars.return_value.all.return_value = fake_table_rows
            return result

        mock_session.execute.side_effect = execute_side_effect
        yield mock_session

    return override


def _make_broken_db():
    """Dependency override that simulates a connection failure."""
    def override():
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("connection refused")
        yield mock_session

    return override


class TestDbPingHappyPath:

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_all_tables_present(self):
        db_tables = ALL_APP_TABLES + ["alembic_version"]
        app.dependency_overrides[get_db] = _make_fake_db(db_tables)

        response = client.get("/api/db/ping")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["database"] == "connected"

    # def test_extra_db_tables_still_ok(self):
    #     """Tables in DB beyond the schema shouldn't cause failure."""
    #     db_tables = ALL_APP_TABLES + ["alembic_version", "audit_log"]
    #     app.dependency_overrides[get_db] = _make_fake_db(db_tables)

    #     response = client.get("/api/db/ping")

    #     assert response.json()["status"] == "ok"


class TestDbPingSchemaErrors:

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_missing_some_tables(self):
        """DB reachable but missing most app tables."""
        db_tables = ["scan_run", "alembic_version"]
        app.dependency_overrides[get_db] = _make_fake_db(db_tables)

        response = client.get("/api/db/ping")

        body = response.json()
        print("body: ", body)
        assert body["database"] == "connected"
        assert "error" in body["status"].lower()
        for table in ["ec2_instance", "utilization_metric", "finding", "recommendation"]:
            assert table in body["status"]

    def test_completely_empty_db(self):
        app.dependency_overrides[get_db] = _make_fake_db([])

        response = client.get("/api/db/ping")

        body = response.json()
        assert "error" in body["status"].lower()

    def test_db_unreachable_returns_500(self):
        app.dependency_overrides[get_db] = _make_broken_db()

        response = client.get("/api/db/ping")

        assert response.status_code == 503


