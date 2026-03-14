"""Recommendation endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.recommendation import Recommendation
from app.models.finding import Finding
from app.schemas.recommendation_schema import (
    RecommendationCreate,
    RecommendationListResponse,
    RecommendationResponse,
)

recommendations_router = APIRouter(tags=["recommendations"])


# ── POST /recommendations ────────────────────────────────────────

@recommendations_router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_recommendation(
    payload: RecommendationCreate, db: Session = Depends(get_db)
):
    """Create a recommendation record.

    Validates that the referenced finding_id exists before inserting.
    """
    finding = db.get(Finding, payload.finding_id)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding {payload.finding_id} not found",
        )

    rec = Recommendation(**payload.model_dump())
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


# ── GET /recommendations ─────────────────────────────────────────

@recommendations_router.get(
    "/recommendations",
    response_model=RecommendationListResponse,
)
def list_recommendations(
    finding_id: Optional[int] = Query(None, description="Filter by finding_id"),
    run_id: Optional[int] = Query(None, description="Filter by run_id (via finding)"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by recommendation status"
    ),
    category: Optional[str] = Query(None, description="Filter by optimization_category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List recommendations with optional filters.

    run_id filter works by joining through the Finding table.
    """
    query = db.query(Recommendation)

    if finding_id is not None:
        query = query.filter(Recommendation.finding_id == finding_id)

    if run_id is not None:
        query = query.join(Finding, Recommendation.finding_id == Finding.finding_id).filter(
            Finding.run_id == run_id
        )

    if status_filter is not None:
        query = query.filter(Recommendation.status == status_filter)

    if category is not None:
        query = query.filter(Recommendation.optimization_category == category)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return RecommendationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ── GET /recommendations/{recommendation_id} ────────────────────

@recommendations_router.get(
    "/recommendations/{recommendation_id}",
    response_model=RecommendationResponse,
)
def get_recommendation(recommendation_id: int, db: Session = Depends(get_db)):
    """Retrieve a single recommendation by ID."""
    rec = db.get(Recommendation, recommendation_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {recommendation_id} not found",
        )
    return rec