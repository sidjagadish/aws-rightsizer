"""Thorough tests for POST /api/metrics endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Helpers ──────────────────────────────────────────────────────

def create_run() -> dict:
    """POST a ScanRun and return the response JSON."""
    resp = client.post("/api/runs", json={
        "model_version": "v1.0",
        "observation_window": "7d",
        "initiated_by": "test",
    })
    assert resp.status_code in (200, 201), f"Failed to create run: {resp.text}"
    return resp.json()


def create_instance() -> dict:
    """POST an EC2Instance and return the response JSON."""
    resp = client.post("/api/instances", json={
        "arn": "arn:aws:ec2:us-east-1:1234:instance/i-test",
        "region": "us-east-1",
        "owner_id": 1234,
        "architecture": "x86_64",
        "platform": "linux",
        "tenancy": "default",
    })
    assert resp.status_code in (200, 201), f"Failed to create instance: {resp.text}"
    return resp.json()


def _base_payload(run_id: int, resource_id: int) -> dict:
    """Return a minimal valid metric payload."""
    return {
        "run_id": run_id,
        "resource_id": resource_id,
        "window_start": "2025-01-01",
        "window_end": "2025-01-08",
        "period": 300,
        "source": "cloudwatch",
    }


# ── Happy-path tests ────────────────────────────────────────────

def test_create_metric_minimal_fields():
    """POST with only required fields succeeds; optional metric cols are null."""
    run = create_run()
    instance = create_instance()

    resp = client.post("/api/metrics", json=_base_payload(run["run_id"], instance["resource_id"]))

    assert resp.status_code == 201
    data = resp.json()
    assert data["metric_id"] is not None
    assert data["cpu_avg"] is None
    assert data["memory_avg"] is None
    assert data["network_p99"] is None


def test_create_metric_all_fields():
    """POST with every metric column populated returns them all."""
    run = create_run()
    instance = create_instance()

    payload = {
        **_base_payload(run["run_id"], instance["resource_id"]),
        "missing_data": 0.02,
        "cpu_avg": 12.5,   "cpu_max": 78.3,   "cpu_p95": 65.0,   "cpu_p99": 74.1,
        "power_avg": 5.0,  "power_max": 20.0,  "power_p95": 18.0,  "power_p99": 19.5,
        "memory_avg": 45.0, "memory_max": 88.0, "memory_p95": 80.0, "memory_p99": 85.0,
        "network_avg": 1.2, "network_max": 9.8, "network_p95": 7.5, "network_p99": 9.0,
    }

    resp = client.post("/api/metrics", json=payload)

    assert resp.status_code == 201
    data = resp.json()
    assert data["cpu_avg"] == 12.5
    assert data["power_p99"] == 19.5
    assert data["memory_max"] == 88.0
    assert data["network_p95"] == 7.5
    assert data["missing_data"] == 0.02


def test_create_two_metrics_same_run():
    """A single run can have multiple metrics (e.g. different windows)."""
    run = create_run()
    inst = create_instance()

    p1 = {**_base_payload(run["run_id"], inst["resource_id"]), "window_start": "2025-01-01", "window_end": "2025-01-08"}
    p2 = {**_base_payload(run["run_id"], inst["resource_id"]), "window_start": "2025-01-08", "window_end": "2025-01-15"}

    r1 = client.post("/api/metrics", json=p1)
    r2 = client.post("/api/metrics", json=p2)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["metric_id"] != r2.json()["metric_id"]


# ── FK enforcement tests ────────────────────────────────────────

def test_create_metric_invalid_run_id():
    """Non-existent run_id → 404."""
    instance = create_instance()
    payload = _base_payload(999999, instance["resource_id"])

    resp = client.post("/api/metrics", json=payload)
    assert resp.status_code == 404
    assert "ScanRun" in resp.json()["detail"]


def test_create_metric_invalid_resource_id():
    """Non-existent resource_id → 404."""
    run = create_run()
    payload = _base_payload(run["run_id"], 999999)

    resp = client.post("/api/metrics", json=payload)
    assert resp.status_code == 404
    assert "EC2Instance" in resp.json()["detail"]


def test_create_metric_both_fks_invalid():
    """Both run_id and resource_id invalid → 404 (run checked first)."""
    payload = _base_payload(999999, 999999)

    resp = client.post("/api/metrics", json=payload)
    assert resp.status_code == 404


# ── Validation tests ────────────────────────────────────────────

def test_create_metric_missing_required_field():
    """Omitting a required field (source) → 422 validation error."""
    run = create_run()
    instance = create_instance()

    payload = {
        "run_id": run["run_id"],
        "resource_id": instance["resource_id"],
        "window_start": "2025-01-01",
        "window_end": "2025-01-08",
        "period": 300,
        # "source" intentionally omitted
    }

    resp = client.post("/api/metrics", json=payload)
    assert resp.status_code == 422


def test_create_metric_invalid_date_format():
    """Bad date string → 422 validation error."""
    run = create_run()
    instance = create_instance()

    payload = {
        **_base_payload(run["run_id"], instance["resource_id"]),
        "window_start": "not-a-date",
    }

    resp = client.post("/api/metrics", json=payload)
    assert resp.status_code == 422


def test_create_metric_empty_body():
    """Empty JSON body → 422."""
    resp = client.post("/api/metrics", json={})
    assert resp.status_code == 422