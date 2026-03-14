"""Tests for POST /api/findings endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Helpers ──────────────────────────────────────────────────────

def create_run() -> dict:
    resp = client.post("/api/runs", json={
        "model_version": "v1.0",
        "observation_window": "7d",
        "initiated_by": "test",
    })
    assert resp.status_code in (200, 201)
    return resp.json()


def create_instance() -> dict:
    resp = client.post("/api/instances", json={
        "arn": "arn:aws:ec2:us-east-1:1234:instance/i-test",
        "region": "us-east-1",
        "owner_id": 1234,
        "architecture": "x86_64",
        "platform": "linux",
        "tenancy": "default",
    })
    assert resp.status_code in (200, 201)
    return resp.json()


def create_metric(run_id: int, resource_id: int) -> dict:
    resp = client.post("/api/metrics", json={
        "run_id": run_id,
        "resource_id": resource_id,
        "window_start": "2025-01-01",
        "window_end": "2025-01-08",
        "period": 300,
        "source": "cloudwatch",
    })
    assert resp.status_code == 201
    return resp.json()


def setup_prerequisites() -> dict:
    """Create the full chain: run → instance → metric. Return all IDs."""
    run = create_run()
    inst = create_instance()
    metric = create_metric(run["run_id"], inst["resource_id"])
    return {
        "run_id": run["run_id"],
        "resource_id": inst["resource_id"],
        "metric_id": metric["metric_id"],
    }


def _base_payload(prereqs: dict) -> dict:
    return {
        "run_id": prereqs["run_id"],
        "resource_id": prereqs["resource_id"],
        "utilization_metric_id": prereqs["metric_id"],
        "assessment": "undersized",
        "status": "open",
        "created_on": "2025-01-10",
    }


# ── Happy-path tests ────────────────────────────────────────────

def test_create_finding_minimal():
    """POST with required fields succeeds; optional fields are null."""
    prereqs = setup_prerequisites()
    payload = _base_payload(prereqs)

    resp = client.post("/api/findings", json=payload)

    assert resp.status_code == 201
    data = resp.json()
    assert data["finding_id"] is not None
    assert data["run_id"] == prereqs["run_id"]
    assert data["resource_id"] == prereqs["resource_id"]
    assert data["utilization_metric_id"] == prereqs["metric_id"]
    assert data["assessment"] == "undersized"
    assert data["status"] == "open"
    assert data["constraints"] is None
    assert data["updated_on"] is None


def test_create_finding_all_fields():
    """POST with every field populated returns them all."""
    prereqs = setup_prerequisites()
    payload = {
        **_base_payload(prereqs),
        "constraints": "must stay in us-east-1",
        "updated_on": "2025-01-12",
    }

    resp = client.post("/api/findings", json=payload)

    assert resp.status_code == 201
    data = resp.json()
    assert data["constraints"] == "must stay in us-east-1"
    assert data["updated_on"] == "2025-01-12"


def test_create_finding_each_valid_status():
    """All four FindingStatus values are accepted."""
    for status_val in ("open", "resolved", "dismissed", "in_progress"):
        prereqs = setup_prerequisites()
        payload = {**_base_payload(prereqs), "status": status_val}

        resp = client.post("/api/findings", json=payload)
        assert resp.status_code == 201, f"status={status_val} failed: {resp.text}"
        assert resp.json()["status"] == status_val


def test_create_finding_defaults_to_open():
    """Omitting status defaults to 'open'."""
    prereqs = setup_prerequisites()
    payload = _base_payload(prereqs)
    del payload["status"]

    resp = client.post("/api/findings", json=payload)

    assert resp.status_code == 201
    assert resp.json()["status"] == "open"


def test_create_multiple_findings_per_run():
    """A single run can have multiple findings."""
    prereqs = setup_prerequisites()
    p1 = {**_base_payload(prereqs), "assessment": "undersized"}
    p2 = {**_base_payload(prereqs), "assessment": "oversized"}

    r1 = client.post("/api/findings", json=p1)
    r2 = client.post("/api/findings", json=p2)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["finding_id"] != r2.json()["finding_id"]


# ── FK enforcement tests ────────────────────────────────────────

def test_create_finding_invalid_run_id():
    """Non-existent run_id → 404."""
    prereqs = setup_prerequisites()
    payload = {**_base_payload(prereqs), "run_id": 999999}

    resp = client.post("/api/findings", json=payload)
    assert resp.status_code == 404
    assert "ScanRun" in resp.json()["detail"]


def test_create_finding_invalid_resource_id():
    """Non-existent resource_id → 404."""
    prereqs = setup_prerequisites()
    payload = {**_base_payload(prereqs), "resource_id": 999999}

    resp = client.post("/api/findings", json=payload)
    assert resp.status_code == 404
    assert "EC2Instance" in resp.json()["detail"]


def test_create_finding_invalid_metric_id():
    """Non-existent utilization_metric_id → 404."""
    prereqs = setup_prerequisites()
    payload = {**_base_payload(prereqs), "utilization_metric_id": 999999}

    resp = client.post("/api/findings", json=payload)
    assert resp.status_code == 404
    assert "UtilizationMetric" in resp.json()["detail"]


# ── Validation tests ────────────────────────────────────────────

def test_create_finding_invalid_status():
    """Invalid status value → 422 (constrained to FindingStatus enum)."""
    prereqs = setup_prerequisites()
    payload = {**_base_payload(prereqs), "status": "banana"}

    resp = client.post("/api/findings", json=payload)
    assert resp.status_code == 422


def test_create_finding_missing_required_field():
    """Omitting assessment → 422."""
    prereqs = setup_prerequisites()
    payload = {
        "run_id": prereqs["run_id"],
        "resource_id": prereqs["resource_id"],
        "utilization_metric_id": prereqs["metric_id"],
        # "assessment" intentionally omitted
        "created_on": "2025-01-10",
    }

    resp = client.post("/api/findings", json=payload)
    assert resp.status_code == 422


def test_create_finding_invalid_date():
    """Bad date string → 422."""
    prereqs = setup_prerequisites()
    payload = {**_base_payload(prereqs), "created_on": "not-a-date"}

    resp = client.post("/api/findings", json=payload)
    assert resp.status_code == 422


def test_create_finding_empty_body():
    """Empty JSON body → 422."""
    resp = client.post("/api/findings", json={})
    assert resp.status_code == 422