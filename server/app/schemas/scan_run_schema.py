"""Pydantic schemas for ScanRun request / response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.finding_status import FindingStatus


# ── Request schemas ──────────────────────────────────────────────

class ScanRunCreate(BaseModel):
    """Body for POST /runs."""

    model_version: str
    observation_window: str
    initiated_by: str = "system"

    # optional filters the caller can supply at creation time
    id_filter: Optional[list[int]] = None
    region_filter: Optional[list[str]] = None


# ── Response schemas ─────────────────────────────────────────────

class ScanRunResponse(BaseModel):
    """Single run returned by GET /runs/{run_id} or as an item in a list."""

    run_id: int
    model_version: Optional[str] = None
    observation_window: Optional[str] = None
    initiated_by: Optional[str] = None
    id_filter: Optional[list[int]] = None
    region_filter: Optional[list[str]] = None
    status: FindingStatus
    started_on: Optional[datetime] = None
    completed_on: Optional[datetime] = None
    scanned_count: int = 0

    model_config = {"from_attributes": True}  # Pydantic v2 ORM mode


class ScanRunListResponse(BaseModel):
    """Wrapper for paginated GET /runs."""

    items: list[ScanRunResponse]
    total: int
    page: int
    page_size: int