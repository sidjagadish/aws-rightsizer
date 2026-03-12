import enum

from sqlalchemy import Column, Integer, String, Date, Enum, ForeignKey 
from sqlalchemy.dialects.postgresql import ARRAY

from app.db import Base


class FindingStatus(enum.Enum):
    open = "open"
    resolved = "resolved"
    dismissed = "dismissed"
    in_progress = "in_progress"


class Finding(Base):
    __tablename__ = "finding"

    finding_id = Column(Integer, primary_key=True)
    run_id = Column(Integer,ForeignKey("scan_run.run_id"), nullable=False)
    resource_id = Column(Integer,ForeignKey("ec2_instance.resource_id"), nullable=False)

    utilization_metric_id = Column(Integer,ForeignKey("utilization_metric.metric_id"), nullable=False)
    assessment = Column(String, nullable=False)
    status = Column(Enum(FindingStatus), nullable=False, default=FindingStatus.open)
    created_on = Column(Date, nullable=False)
    updated_on = Column(Date, nullable=True)
    recommendations = Column(ARRAY(Integer),ForeignKey("recommendation.recommendation_id"), nullable=True)
    constraints = Column(String, nullable=True)