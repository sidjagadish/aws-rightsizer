"""Tests for GET /api/recommendations and GET /api/recommendations/{id}."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models.finding import Finding

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


def create_finding(run_id: int, resource_id: int, metric_id: int) -> dict:
    """Insert a Finding directly via DB (no POST /findings endpoint yet)."""
    db = SessionLocal()
    finding = Finding(
        run_id=run_id,
        resource_id=resource_id,
        utilization_metric_id=metric_id,
        assessment="undersized",
        status="open",
        created_on=date.today(),
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)
    result = {"finding_id": finding.finding_id, "run_id": finding.run_id}
    db.close()
    return result


def setup_finding() -> dict:
    """Create the full chain: run → instance → metric → finding."""
    run = create_run()
    inst = create_instance()
    metric = create_metric(run["run_id"], inst["resource_id"])
    finding = create_finding(run["run_id"], inst["resource_id"], metric["metric_id"])
    return {**finding, "resource_id": inst["resource_id"]}


def create_recommendation(finding_id: int, **overrides) -> dict:
    payload = {
        "finding_id": finding_id,
        "recommended_config": "m5.large",
        "optimization_category": "rightsizing",
        "status": "pending",
        "created_on": "2025-01-10",
        **overrides,
    }
    resp = client.post("/api/recommendations", json=payload)
    assert resp.status_code == 201, f"Failed to create recommendation: {resp.text}"
    return resp.json()


# ── GET /api/recommendations/{recommendation_id} ────────────────

def test_get_recommendation_by_id():
    """Retrieve a recommendation by its ID."""
    finding = setup_finding()
    rec = create_recommendation(finding["finding_id"], confidence=0.88)

    resp = client.get(f"/api/recommendations/{rec['recommendation_id']}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["recommendation_id"] == rec["recommendation_id"]
    assert data["confidence"] == 0.88
    assert data["recommended_config"] == "m5.large"


def test_get_recommendation_not_found():
    """Non-existent recommendation_id → 404."""
    resp = client.get("/api/recommendations/999999")

    assert resp.status_code == 404
    assert "Recommendation" in resp.json()["detail"]


# ── GET /api/recommendations (list / filters) ───────────────────

def test_list_recommendations_no_filter():
    """List all recommendations returns a paginated response."""
    finding = setup_finding()
    create_recommendation(finding["finding_id"])

    resp = client.get("/api/recommendations")

    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


def test_list_recommendations_filter_by_finding_id():
    """Filter by finding_id returns only matching rows."""
    f_a = setup_finding()
    f_b = setup_finding()

    create_recommendation(f_a["finding_id"], recommended_config="c5.large")
    create_recommendation(f_b["finding_id"], recommended_config="r5.large")

    resp = client.get(f"/api/recommendations?finding_id={f_a['finding_id']}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["finding_id"] == f_a["finding_id"]


def test_list_recommendations_filter_by_run_id():
    """Filter by run_id (joins through Finding) returns only matching rows."""
    f_a = setup_finding()
    f_b = setup_finding()

    create_recommendation(f_a["finding_id"], recommended_config="c5.large")
    create_recommendation(f_b["finding_id"], recommended_config="r5.large")

    resp = client.get(f"/api/recommendations?run_id={f_a['run_id']}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    # verify all returned recs belong to a finding from that run
    for item in data["items"]:
        assert item["finding_id"] == f_a["finding_id"]


def test_list_recommendations_filter_by_status():
    """Filter by status returns only matching rows."""
    finding = setup_finding()

    create_recommendation(finding["finding_id"], status="pending")
    create_recommendation(finding["finding_id"], status="accepted")

    resp = client.get("/api/recommendations?status=accepted")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["status"] == "accepted"


def test_list_recommendations_filter_by_category():
    """Filter by optimization_category returns only matching rows."""
    finding = setup_finding()

    create_recommendation(finding["finding_id"], optimization_category="rightsizing")
    create_recommendation(finding["finding_id"], optimization_category="scheduling")

    resp = client.get("/api/recommendations?category=scheduling")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["optimization_category"] == "scheduling"


def test_list_recommendations_combined_filters():
    """Filter by finding_id AND status together."""
    finding = setup_finding()

    create_recommendation(finding["finding_id"], status="pending")
    create_recommendation(finding["finding_id"], status="accepted")

    resp = client.get(
        f"/api/recommendations?finding_id={finding['finding_id']}&status=accepted"
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["finding_id"] == finding["finding_id"]
        assert item["status"] == "accepted"


def test_list_recommendations_no_results():
    """Filter with non-existent finding_id → empty list."""
    resp = client.get("/api/recommendations?finding_id=999999")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_recommendations_pagination():
    """Page and page_size params work correctly."""
    finding = setup_finding()

    for _ in range(3):
        create_recommendation(finding["finding_id"])

    resp = client.get(
        f"/api/recommendations?finding_id={finding['finding_id']}&page=1&page_size=1"
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["page"] == 1
    assert data["page_size"] == 1
    assert data["total"] >= 3