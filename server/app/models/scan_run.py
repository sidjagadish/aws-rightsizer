from sqlalchemy import Column, String, Integer, DateTime
from app.db import Base


class ScanRun(Base):
    __tablename__ = "scan_run"

    run_id = Column(String, primary_key=True)
    status = Column(String, nullable=False, default="pending")
    model_version = Column(String)
    scanned_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    started_on = Column(DateTime)
    completed_on = Column(DateTime)