"""UtilizationMetric endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.utilization_metric import UtilizationMetric
from app.models.scan_run import ScanRun
from app.models.ec2_instance import EC2Instance
from app.schemas.metrics_schema import (
    MetricCreate,
    MetricListResponse,
    MetricResponse,
)

metrics_router = APIRouter(tags=["metrics"])


# ── POST /metrics ────────────────────────────────────────────────

@metrics_router.post(
    "/metrics",
    response_model=MetricResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_metric(payload: MetricCreate, db: Session = Depends(get_db)):
    """Create a utilization metric record.

    Validates that the referenced run_id and resource_id exist
    before inserting.
    """
    run = db.get(ScanRun, payload.run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ScanRun {payload.run_id} not found",
        )

    resource = db.get(EC2Instance, payload.resource_id)
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"EC2Instance {payload.resource_id} not found",
        )

    metric = UtilizationMetric(**payload.model_dump())
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


# ── GET /metrics ─────────────────────────────────────────────────

@metrics_router.get(
    "/metrics",
    response_model=MetricListResponse,
)
def list_metrics(
    run_id: Optional[int] = Query(None, description="Filter by run_id"),
    resource_id: Optional[int] = Query(None, description="Filter by resource_id"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List utilization metrics with optional filters."""
    query = db.query(UtilizationMetric)

    if run_id is not None:
        query = query.filter(UtilizationMetric.run_id == run_id)
    if resource_id is not None:
        query = query.filter(UtilizationMetric.resource_id == resource_id)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return MetricListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ── GET /metrics/{metric_id} ────────────────────────────────────

@metrics_router.get(
    "/metrics/{metric_id}",
    response_model=MetricResponse,
)
def get_metric(metric_id: int, db: Session = Depends(get_db)):
    """Retrieve a single utilization metric by ID."""
    metric = db.get(UtilizationMetric, metric_id)
    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metric {metric_id} not found",
        )
    return metric