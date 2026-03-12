from sqlalchemy import Column, Integer, Float, String, Date

from app.db import Base


class Recommendation(Base):
    __tablename__ = "recommendation"

    recommendation_id = Column(Integer, primary_key=True)
    finding_id = Column(Integer, nullable=False)
    recommended_config = Column(String, nullable=False)
    optimization_category = Column(String, nullable=False)
    monthly_cost_impact = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    status = Column(String, nullable=False)
    created_on = Column(Date, nullable=False)
    updated_on = Column(Date, nullable=True)