from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey

from app.db import Base


class UtilizationMetric(Base):
    __tablename__ = "utilization_metric"

    metric_id = Column(Integer, primary_key=True)
    #run_id = Column(Integer, nullable=False)
    run_id = Column(Integer, ForeignKey("scan_run.run_id"), nullable=False)
    resource_id = Column(Integer, nullable=False)
    window_start = Column(Date, nullable=False)
    window_end = Column(Date, nullable=False)
    period = Column(Integer, nullable=False)
    source = Column(String, nullable=False)
    missing_data = Column(Float, nullable=True)
    cpu_avg = Column(Float, nullable=True)
    cpu_max = Column(Float, nullable=True)
    cpu_p95 = Column(Float, nullable=True)
    cpu_p99 = Column(Float, nullable=True)
    power_avg = Column(Float, nullable=True)
    power_max = Column(Float, nullable=True)
    power_p95 = Column(Float, nullable=True)
    power_p99 = Column(Float, nullable=True)
    memory_avg = Column(Float, nullable=True)
    memory_max = Column(Float, nullable=True)
    memory_p95 = Column(Float, nullable=True)
    memory_p99 = Column(Float, nullable=True)
    network_avg = Column(Float, nullable=True)
    network_max = Column(Float, nullable=True)
    network_p95 = Column(Float, nullable=True)
    network_p99 = Column(Float, nullable=True)