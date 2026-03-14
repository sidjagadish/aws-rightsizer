"""Finding endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.finding import Finding
from app.models.scan_run import ScanRun
from app.models.ec2_instance import EC2Instance
from app.models.utilization_metric import UtilizationMetric
from app.schemas.finding_schema import (
    FindingCreate,
    FindingListResponse,
    FindingResponse,
    FindingStatusEnum,
)

findings_router = APIRouter(tags=["findings"])


# ── POST /findings ───────────────────────────────────────────────

@findings_router.post(
    "/findings",
    response_model=FindingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_finding(payload: FindingCreate, db: Session = Depends(get_db)):
    """Create a finding record.

    Validates that the referenced run_id, resource_id, and
    utilization_metric_id all exist before inserting.
    Status is constrained to allowed FindingStatus values by the schema.
    """
    # ── FK existence checks ──────────────────────────────────
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

    metric = db.get(UtilizationMetric, payload.utilization_metric_id)
    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"UtilizationMetric {payload.utilization_metric_id} not found",
        )

    # ── Insert ───────────────────────────────────────────────
    data = payload.model_dump()
    # Convert the Pydantic enum to its string value for the DB enum column
    data["status"] = data["status"].value if hasattr(data["status"], "value") else data["status"]
    finding = Finding(**data)
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return finding


# ── GET /findings ────────────────────────────────────────────────

@findings_router.get(
    "/findings",
    response_model=FindingListResponse,
)
def list_findings(
    run_id: Optional[int] = Query(None, description="Filter by run_id"),
    resource_id: Optional[int] = Query(None, description="Filter by resource_id"),
    status_filter: Optional[FindingStatusEnum] = Query(
        None, alias="status", description="Filter by finding status"
    ),
    assessment: Optional[str] = Query(None, description="Filter by assessment value"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List findings with optional filters.

    run_id filter is index-backed for performance.
    """
    query = db.query(Finding)

    if run_id is not None:
        query = query.filter(Finding.run_id == run_id)
    if resource_id is not None:
        query = query.filter(Finding.resource_id == resource_id)
    if status_filter is not None:
        query = query.filter(Finding.status == status_filter.value)
    if assessment is not None:
        query = query.filter(Finding.assessment == assessment)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return FindingListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ── GET /findings/{finding_id} ──────────────────────────────────

@findings_router.get(
    "/findings/{finding_id}",
    response_model=FindingResponse,
)
def get_finding(finding_id: int, db: Session = Depends(get_db)):
    """Retrieve a single finding by ID.

    Response includes run_id, resource_id, and utilization_metric_id
    for easy traversal to related entities.
    """
    finding = db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding {finding_id} not found",
        )
    return finding