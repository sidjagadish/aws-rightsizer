"""Pydantic schemas for EC2Instance request / response validation."""

from typing import Optional

from pydantic import BaseModel


# ── Request schemas ──────────────────────────────────────────────

class EC2InstanceCreate(BaseModel):
    """Body for POST /instances."""

    arn: str
    region: str
    owner_id: int
    architecture: str
    platform: str
    tenancy: str
    tags: Optional[list[str]] = None


# ── Response schemas ─────────────────────────────────────────────

class EC2InstanceResponse(BaseModel):
    """Single instance returned by GET /instances/{resource_id} or as a list item."""

    resource_id: int
    arn: str
    region: str
    owner_id: int
    architecture: str
    platform: str
    tenancy: str
    tags: Optional[list[str]] = None

    model_config = {"from_attributes": True}


class EC2InstanceListResponse(BaseModel):
    """Wrapper for paginated GET /instances."""

    items: list[EC2InstanceResponse]
    total: int
    page: int
    page_size: int