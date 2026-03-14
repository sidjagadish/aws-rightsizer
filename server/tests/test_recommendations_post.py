"""Tests for POST /api/recommendations endpoint."""

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
    return finding


def _base_payload(finding_id: int) -> dict:
    return {
        "finding_id": finding_id,
        "recommended_config": "m5.large",
        "optimization_category": "rightsizing",
        "status": "pending",
        "created_on": "2025-01-10",
    }


# ── Happy-path tests ────────────────────────────────────────────

def test_create_recommendation_minimal():
    """POST with required fields only succeeds."""
    finding = setup_finding()
    payload = _base_payload(finding["finding_id"])

    resp = client.post("/api/recommendations", json=payload)

    assert resp.status_code == 201
    data = resp.json()
    assert data["recommendation_id"] is not None
    assert data["finding_id"] == finding["finding_id"]
    assert data["recommended_config"] == "m5.large"
    assert data["monthly_cost_impact"] is None
    assert data["confidence"] is None


def test_create_recommendation_all_fields():
    """POST with every field populated returns them all."""
    finding = setup_finding()
    payload = {
        **_base_payload(finding["finding_id"]),
        "monthly_cost_impact": -42.50,
        "confidence": 0.92,
        "updated_on": "2025-01-12",
    }

    resp = client.post("/api/recommendations", json=payload)

    assert resp.status_code == 201
    data = resp.json()
    assert data["monthly_cost_impact"] == -42.50
    assert data["confidence"] == 0.92
    assert data["updated_on"] == "2025-01-12"


def test_create_multiple_recommendations_per_finding():
    """A single finding can have multiple recommendations."""
    finding = setup_finding()
    p1 = {**_base_payload(finding["finding_id"]), "recommended_config": "m5.large"}
    p2 = {**_base_payload(finding["finding_id"]), "recommended_config": "m5.xlarge"}

    r1 = client.post("/api/recommendations", json=p1)
    r2 = client.post("/api/recommendations", json=p2)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["recommendation_id"] != r2.json()["recommendation_id"]


# ── FK enforcement tests ────────────────────────────────────────

def test_create_recommendation_invalid_finding_id():
    """Non-existent finding_id → 404."""
    payload = _base_payload(999999)

    resp = client.post("/api/recommendations", json=payload)
    assert resp.status_code == 404
    assert "Finding" in resp.json()["detail"]


# ── Validation tests ────────────────────────────────────────────

def test_create_recommendation_missing_required_field():
    """Omitting recommended_config → 422."""
    finding = setup_finding()
    payload = {
        "finding_id": finding["finding_id"],
        # "recommended_config" intentionally omitted
        "optimization_category": "rightsizing",
        "status": "pending",
        "created_on": "2025-01-10",
    }

    resp = client.post("/api/recommendations", json=payload)
    assert resp.status_code == 422


def test_create_recommendation_invalid_date():
    """Bad date string → 422."""
    finding = setup_finding()
    payload = {
        **_base_payload(finding["finding_id"]),
        "created_on": "not-a-date",
    }

    resp = client.post("/api/recommendations", json=payload)
    assert resp.status_code == 422


def test_create_recommendation_empty_body():
    """Empty JSON body → 422."""
    resp = client.post("/api/recommendations", json={})
    assert resp.status_code == 422