"""ScanRun endpoints – POST /runs, GET /runs, GET /runs/{run_id}."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.scan_run import ScanRun
from app.models.finding_status import FindingStatus
from app.schemas.scan_run_schema import (
    ScanRunCreate,
    ScanRunResponse,
    ScanRunListResponse,
)

router = APIRouter(prefix="/runs", tags=["runs"])


# ── POST /runs ───────────────────────────────────────────────────

@router.post("/", response_model=ScanRunResponse, status_code=201)
def create_run(payload: ScanRunCreate, db: Session = Depends(get_db)):
    """Create a new ScanRun.

    Sets status to 'open' and stamps started_on automatically.
    """
    new_run = ScanRun(
        model_version=payload.model_version,
        observation_window=payload.observation_window,
        initiated_by=payload.initiated_by,
        id_filter=payload.id_filter,
        region_filter=payload.region_filter,
        status=FindingStatus.open,
        started_on=datetime.now(timezone.utc),
        scanned_count=0,
    )

    db.add(new_run)
    db.commit()
    db.refresh(new_run)

    return new_run


# ── GET /runs ────────────────────────────────────────────────────

@router.get("/", response_model=ScanRunListResponse)
def list_runs(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query(
        "started_on",
        pattern="^(started_on|completed_on)$",
        description="Column to sort by",
    ),
    db: Session = Depends(get_db),
):
    """Return ScanRuns, most-recent first, with offset pagination."""

    sort_column = getattr(ScanRun, sort_by)
    total = db.query(func.count(ScanRun.run_id)).scalar()

    items = (
        db.query(ScanRun)
        .order_by(sort_column.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return ScanRunListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ── GET /runs/{run_id} ──────────────────────────────────────────

@router.get("/{run_id}", response_model=ScanRunResponse)
def get_run(run_id: int, db: Session = Depends(get_db)):
    """Return a single ScanRun or 404."""

    run = db.query(ScanRun).filter(ScanRun.run_id == run_id).first()

    if run is None:
        raise HTTPException(status_code=404, detail=f"ScanRun {run_id} not found")

    return run

