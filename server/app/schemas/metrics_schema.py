"""Pydantic schemas for UtilizationMetric request / response validation."""

from datetime import date
from typing import Optional

from pydantic import BaseModel


# ── Request schemas ──────────────────────────────────────────────

class MetricCreate(BaseModel):
    """Body for POST /metrics."""

    run_id: int
    resource_id: int
    window_start: date
    window_end: date
    period: int
    source: str
    missing_data: Optional[float] = None
    cpu_avg: Optional[float] = None
    cpu_max: Optional[float] = None
    cpu_p95: Optional[float] = None
    cpu_p99: Optional[float] = None
    power_avg: Optional[float] = None
    power_max: Optional[float] = None
    power_p95: Optional[float] = None
    power_p99: Optional[float] = None
    memory_avg: Optional[float] = None
    memory_max: Optional[float] = None
    memory_p95: Optional[float] = None
    memory_p99: Optional[float] = None
    network_avg: Optional[float] = None
    network_max: Optional[float] = None
    network_p95: Optional[float] = None
    network_p99: Optional[float] = None


# ── Response schemas ─────────────────────────────────────────────

class MetricResponse(BaseModel):
    """Single metric returned by GET /metrics/{metric_id} or as a list item."""

    metric_id: int
    run_id: int
    resource_id: int
    window_start: date
    window_end: date
    period: int
    source: str
    missing_data: Optional[float] = None
    cpu_avg: Optional[float] = None
    cpu_max: Optional[float] = None
    cpu_p95: Optional[float] = None
    cpu_p99: Optional[float] = None
    power_avg: Optional[float] = None
    power_max: Optional[float] = None
    power_p95: Optional[float] = None
    power_p99: Optional[float] = None
    memory_avg: Optional[float] = None
    memory_max: Optional[float] = None
    memory_p95: Optional[float] = None
    memory_p99: Optional[float] = None
    network_avg: Optional[float] = None
    network_max: Optional[float] = None
    network_p95: Optional[float] = None
    network_p99: Optional[float] = None

    model_config = {"from_attributes": True}


class MetricListResponse(BaseModel):
    """Wrapper for paginated GET /metrics."""

    items: list[MetricResponse]
    total: int
    page: int
    page_size: int