"""Pydantic schemas for Recommendation request / response validation."""

from datetime import date
from typing import Optional

from pydantic import BaseModel


# ── Request schemas ──────────────────────────────────────────────

class RecommendationCreate(BaseModel):
    """Body for POST /recommendations."""

    finding_id: int
    recommended_config: str
    optimization_category: str
    monthly_cost_impact: Optional[float] = None
    confidence: Optional[float] = None
    status: str = "pending"
    created_on: date
    updated_on: Optional[date] = None


# ── Response schemas ─────────────────────────────────────────────

class RecommendationResponse(BaseModel):
    """Single recommendation returned by GET /recommendations/{id} or list item."""

    recommendation_id: int
    finding_id: int
    recommended_config: str
    optimization_category: str
    monthly_cost_impact: Optional[float] = None
    confidence: Optional[float] = None
    status: str
    created_on: date
    updated_on: Optional[date] = None

    model_config = {"from_attributes": True}


class RecommendationListResponse(BaseModel):
    """Wrapper for paginated GET /recommendations."""

    items: list[RecommendationResponse]
    total: int
    page: int
    page_size: int