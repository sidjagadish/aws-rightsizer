"""Tests for GET /api/findings and GET /api/findings/{finding_id}."""

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
    run = create_run()
    inst = create_instance()
    metric = create_metric(run["run_id"], inst["resource_id"])
    return {
        "run_id": run["run_id"],
        "resource_id": inst["resource_id"],
        "metric_id": metric["metric_id"],
    }


def create_finding(prereqs: dict, **overrides) -> dict:
    payload = {
        "run_id": prereqs["run_id"],
        "resource_id": prereqs["resource_id"],
        "utilization_metric_id": prereqs["metric_id"],
        "assessment": "undersized",
        "status": "open",
        "created_on": "2025-01-10",
        **overrides,
    }
    resp = client.post("/api/findings", json=payload)
    assert resp.status_code == 201, f"Failed to create finding: {resp.text}"
    return resp.json()


# ── GET /api/findings/{finding_id} ──────────────────────────────

def test_get_finding_by_id():
    """Retrieve a finding by its ID; response includes all linkage IDs."""
    prereqs = setup_prerequisites()
    finding = create_finding(prereqs, assessment="oversized", constraints="keep same AZ")

    resp = client.get(f"/api/findings/{finding['finding_id']}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["finding_id"] == finding["finding_id"]
    assert data["run_id"] == prereqs["run_id"]
    assert data["resource_id"] == prereqs["resource_id"]
    assert data["utilization_metric_id"] == prereqs["metric_id"]
    assert data["assessment"] == "oversized"
    assert data["constraints"] == "keep same AZ"


def test_get_finding_not_found():
    """Non-existent finding_id → 404."""
    resp = client.get("/api/findings/999999")

    assert resp.status_code == 404
    assert "Finding" in resp.json()["detail"]


# ── GET /api/findings (list / filters) ──────────────────────────

def test_list_findings_no_filter():
    """List all findings returns a paginated response."""
    prereqs = setup_prerequisites()
    create_finding(prereqs)

    resp = client.get("/api/findings")

    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_list_findings_filter_by_run_id():
    """Filter by run_id returns only matching rows."""
    p_a = setup_prerequisites()
    p_b = setup_prerequisites()

    create_finding(p_a, assessment="finding_a")
    create_finding(p_b, assessment="finding_b")

    resp = client.get(f"/api/findings?run_id={p_a['run_id']}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["run_id"] == p_a["run_id"]


def test_list_findings_filter_by_resource_id():
    """Filter by resource_id returns only matching rows."""
    p_a = setup_prerequisites()
    p_b = setup_prerequisites()

    create_finding(p_a)
    create_finding(p_b)

    resp = client.get(f"/api/findings?resource_id={p_a['resource_id']}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["resource_id"] == p_a["resource_id"]


def test_list_findings_filter_by_status():
    """Filter by status returns only matching rows."""
    prereqs = setup_prerequisites()

    create_finding(prereqs, status="open")
    create_finding(prereqs, status="resolved")

    resp = client.get("/api/findings?status=resolved")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["status"] == "resolved"


def test_list_findings_filter_by_assessment():
    """Filter by assessment returns only matching rows."""
    prereqs = setup_prerequisites()

    create_finding(prereqs, assessment="undersized")
    create_finding(prereqs, assessment="oversized")

    resp = client.get("/api/findings?assessment=oversized")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["assessment"] == "oversized"


def test_list_findings_combined_filters():
    """Filter by run_id AND status together."""
    prereqs = setup_prerequisites()

    create_finding(prereqs, status="open")
    create_finding(prereqs, status="dismissed")

    resp = client.get(
        f"/api/findings?run_id={prereqs['run_id']}&status=dismissed"
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["run_id"] == prereqs["run_id"]
        assert item["status"] == "dismissed"


def test_list_findings_invalid_status_filter():
    """Filtering with an invalid status value → 422."""
    resp = client.get("/api/findings?status=banana")

    assert resp.status_code == 422


def test_list_findings_no_results():
    """Filter with non-existent run_id → empty list."""
    resp = client.get("/api/findings?run_id=999999")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_findings_pagination():
    """Page and page_size params work correctly."""
    prereqs = setup_prerequisites()

    for _ in range(3):
        create_finding(prereqs)

    resp = client.get(
        f"/api/findings?run_id={prereqs['run_id']}&page=1&page_size=1"
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["page"] == 1
    assert data["page_size"] == 1
    assert data["total"] >= 3