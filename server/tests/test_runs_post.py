"""Tests for POST /runs."""

import pytest
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import get_db
from app.models.scan_run import ScanRun
from app.models.finding_status import FindingStatus


# ── Test DB setup ────────────────────────────────────────────────

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/rightsizer"

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture()
def db_session():
    """Yield a real DB session; clean up test rows after."""
    session = TestingSessionLocal()
    created_ids = []

    yield session, created_ids

    for run_id in created_ids:
        session.query(ScanRun).filter(ScanRun.run_id == run_id).delete()
    session.commit()
    session.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with the DB dependency overridden."""
    session, created_ids = db_session

    def _override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    # Wrap TestClient so any POST that creates a run tracks it for cleanup
    test_client = TestClient(app)
    original_post = test_client.post

    def tracked_post(*args, **kwargs):
        resp = original_post(*args, **kwargs)
        if resp.status_code == 201 and "run_id" in resp.json():
            created_ids.append(resp.json()["run_id"])
        return resp

    test_client.post = tracked_post

    yield test_client
    app.dependency_overrides.clear()


class TestCreateRun:

    def test_create_minimal(self, client):
        """POST with only required fields succeeds."""
        payload = {
            "model_version": "v1.0",
            "observation_window": "7d",
        }

        resp = client.post("/api/runs/", json=payload)

        assert resp.status_code == 201
        body = resp.json()
        assert body["model_version"] == "v1.0"
        assert body["observation_window"] == "7d"
        assert body["initiated_by"] == "system"  # default
        assert body["status"] == "open"
        assert body["scanned_count"] == 0
        assert body["completed_on"] is None
        assert body["started_on"] is not None
        assert body["run_id"] is not None

    def test_create_with_all_fields(self, client):
        """POST with every field populates them correctly."""
        payload = {
            "model_version": "v2.5",
            "observation_window": "14d",
            "initiated_by": "tom",
            "id_filter": [10, 20, 30],
            "region_filter": ["us-east-1", "eu-west-1"],
        }

        resp = client.post("/api/runs/", json=payload)

        assert resp.status_code == 201
        body = resp.json()
        assert body["model_version"] == "v2.5"
        assert body["observation_window"] == "14d"
        assert body["initiated_by"] == "tom"
        assert body["id_filter"] == [10, 20, 30]
        assert body["region_filter"] == ["us-east-1", "eu-west-1"]

    def test_create_persists_to_db(self, client, db_session):
        """Created run is actually in the database."""
        session, _ = db_session
        payload = {
            "model_version": "v3.0",
            "observation_window": "30d",
        }

        resp = client.post("/api/runs/", json=payload)
        run_id = resp.json()["run_id"]

        db_row = session.query(ScanRun).filter(ScanRun.run_id == run_id).first()
        assert db_row is not None
        assert db_row.model_version == "v3.0"
        assert db_row.observation_window == "30d"

    def test_create_sets_started_on_automatically(self, client):
        """started_on is set server-side, not by the caller."""
        payload = {
            "model_version": "v1.0",
            "observation_window": "7d",
        }

        before = datetime.now(timezone.utc)
        resp = client.post("/api/runs/", json=payload)
        after = datetime.now(timezone.utc)

        started = datetime.fromisoformat(resp.json()["started_on"])
        # started_on should be between before and after the request
        assert before.replace(tzinfo=None) <= started <= after.replace(tzinfo=None)

    def test_create_status_always_open(self, client):
        """Even if caller tries to set status, it should be open."""
        payload = {
            "model_version": "v1.0",
            "observation_window": "7d",
        }
        # ScanRunCreate schema doesn't have a status field,
        # so extra fields are ignored by Pydantic
        resp = client.post("/api/runs/", json={**payload, "status": "resolved"})

        assert resp.status_code == 201
        assert resp.json()["status"] == "open"

    def test_create_missing_required_field(self, client):
        """Missing model_version → 422."""
        payload = {
            "observation_window": "7d",
        }

        resp = client.post("/api/runs/", json=payload)
        assert resp.status_code == 422

    def test_create_empty_body(self, client):
        """Empty JSON body → 422."""
        resp = client.post("/api/runs/", json={})
        assert resp.status_code == 422

    def test_create_then_retrieve(self, client):
        """Round-trip: POST a run then GET it by ID."""
        payload = {
            "model_version": "v1.0",
            "observation_window": "7d",
            "initiated_by": "roundtrip-test",
        }

        create_resp = client.post("/api/runs/", json=payload)
        run_id = create_resp.json()["run_id"]

        get_resp = client.get(f"/api/runs/{run_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["initiated_by"] == "roundtrip-test"
        assert get_resp.json()["run_id"] == run_id