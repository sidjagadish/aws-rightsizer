import enum
from sqlalchemy import Column, String, Integer, DateTime, Enum
from sqlalchemy.dialects.postgresql import ARRAY
from app.db import Base

class FindingStatus(enum.Enum):
    open = "open"
    resolved = "resolved"
    dismissed = "dismissed"
    in_progress = "in_progress"



class ScanRun(Base):
    __tablename__ = "scan_run"

    run_id = Column(String, primary_key=True)
    model_version = Column(String)
    id_filter = Column(ARRAY(Integer), nullable=True)
    region_filter = Column(ARRAY(String), nullable=True)
    observation_window = Column(String)
    status = Column(Enum(FindingStatus), nullable=False, default=FindingStatus.open)
    started_on = Column(DateTime)
    completed_on = Column(DateTime)
    scanned_count = Column(Integer, default=0)
    initiated_by = Column(String, default=0)