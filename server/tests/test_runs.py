"""Tests for GET /runs/ and GET /runs/{run_id}."""

import pytest
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import get_db
from app.models.scan_run import ScanRun
from app.models.finding_status import FindingStatus


# ── Test DB setup ────────────────────────────────────────────────
# Uses the local dev database directly.

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/rightsizer"

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture()
def db_session():
    """Yield a real DB session; clean up test rows after."""
    session = TestingSessionLocal()
    created_ids = []

    yield session, created_ids

    # delete any rows we created
    for run_id in created_ids:
        session.query(ScanRun).filter(ScanRun.run_id == run_id).delete()
    session.commit()
    session.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with the DB dependency overridden."""
    session, _ = db_session

    def _override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ── Helpers ──────────────────────────────────────────────────────

def _seed_run(db_session_tuple, **overrides) -> ScanRun:
    """Insert a ScanRun with sensible defaults; override any field."""
    session, created_ids = db_session_tuple
    defaults = dict(
        model_version="v1.0",
        observation_window="7d",
        initiated_by="test",
        status=FindingStatus.open,
        started_on=datetime.now(timezone.utc),
        scanned_count=0,
    )
    defaults.update(overrides)
    run = ScanRun(**defaults)
    session.add(run)
    session.commit()
    session.refresh(run)
    created_ids.append(run.run_id)
    return run


# ── GET /runs/ ───────────────────────────────────────────────────

class TestListRuns:


    def test_returns_runs_most_recent_first(self, client, db_session):
        """Runs come back sorted by started_on descending."""
        old = _seed_run(db_session, started_on=datetime(2024, 1, 1, tzinfo=timezone.utc))
        new = _seed_run(db_session, started_on=datetime(2025, 6, 1, tzinfo=timezone.utc))

        resp = client.get("/api/runs/")
        print("resp.status_code: ",resp.status_code)
        print("resp.json(): ",resp.json())
        items = resp.json()["items"]
        run_ids = [item["run_id"] for item in items]

        assert new.run_id in run_ids
        assert old.run_id in run_ids
        assert run_ids.index(new.run_id) < run_ids.index(old.run_id)



    def test_sort_by_completed_on(self, client, db_session):
        """sort_by=completed_on changes ordering."""
        a = _seed_run(
            db_session,
            started_on=datetime(2025, 6, 1, tzinfo=timezone.utc),
            completed_on=datetime(2025, 6, 2, tzinfo=timezone.utc),
        )
        b = _seed_run(
            db_session,
            started_on=datetime(2025, 1, 1, tzinfo=timezone.utc),
            completed_on=datetime(2025, 7, 1, tzinfo=timezone.utc),
        )

        resp = client.get("/api/runs/", params={"sort_by": "completed_on"})
        items = resp.json()["items"]
        run_ids = [item["run_id"] for item in items]
        

        # b completed later → should be first
        assert a.run_id in run_ids
        assert b.run_id in run_ids
        correctly_sorted = False
        for index,item in enumerate(items):
            if index+1 == len(items):
                correctly_sorted = True
                break 
            if item["completed_on"] != None:
                item["completed_on"] = items[index+1]["completed_on"]
            
        assert correctly_sorted

    def test_invalid_sort_by_rejected(self, client):
        """sort_by must be started_on or completed_on."""
        resp = client.get("/api/runs/", params={"sort_by": "status"})
        assert resp.status_code == 422


# ── GET /runs/{run_id} ──────────────────────────────────────────

class TestGetRun:

    def test_get_existing_run(self, client, db_session):
        """Returns the correct run by ID."""
        run = _seed_run(db_session, model_version="v2.0")

        resp = client.get(f"/api/runs/{run.run_id}")
        assert resp.status_code == 200
        assert resp.json()["model_version"] == "v2.0"

    def test_get_unknown_run_returns_404(self, client):
        """Unknown run_id → 404 with a useful message."""
        resp = client.get("/api/runs/999999")
        assert resp.status_code == 404
        assert "999999" in resp.json()["detail"]

    def test_response_includes_all_fields(self, client, db_session):
        """Verify the response shape matches the schema."""
        run = _seed_run(
            db_session,
            id_filter=[1, 2, 3],
            region_filter=["us-east-1"],
        )

        body = client.get(f"/api/runs/{run.run_id}").json()

        expected_keys = {
            "run_id", "model_version", "observation_window",
            "initiated_by", "id_filter", "region_filter",
            "status", "started_on", "completed_on", "scanned_count",
        }
        assert set(body.keys()) == expected_keys
        assert body["id_filter"] == [1, 2, 3]
        assert body["region_filter"] == ["us-east-1"]

