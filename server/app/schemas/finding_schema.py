"""Pydantic schemas for Finding request / response validation."""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class FindingStatusEnum(str, Enum):
    """Allowed status values for findings (mirrors app.models.finding_status)."""

    open = "open"
    resolved = "resolved"
    dismissed = "dismissed"
    in_progress = "in_progress"


# ── Request schemas ──────────────────────────────────────────────

class FindingCreate(BaseModel):
    """Body for POST /findings."""

    run_id: int
    resource_id: int
    utilization_metric_id: int
    assessment: str
    status: FindingStatusEnum = FindingStatusEnum.open
    created_on: date
    updated_on: Optional[date] = None
    constraints: Optional[str] = None


# ── Response schemas ─────────────────────────────────────────────

class FindingResponse(BaseModel):
    """Single finding returned by GET /findings/{finding_id} or as a list item.

    Includes run_id, resource_id, and utilization_metric_id so consumers
    can traverse to related entities without extra queries.
    """

    finding_id: int
    run_id: int
    resource_id: int
    utilization_metric_id: int
    assessment: str
    status: FindingStatusEnum
    created_on: date
    updated_on: Optional[date] = None
    constraints: Optional[str] = None

    model_config = {"from_attributes": True}


class FindingListResponse(BaseModel):
    """Wrapper for paginated GET /findings."""

    items: list[FindingResponse]
    total: int
    page: int
    page_size: int