from app.db import SessionLocal
from datetime import datetime
from app.models.scan_run import ScanRun,FindingStatus
from app.models.ec2_instance import EC2Instance
from app.models.finding import Finding, FindingStatus as FindingStatus_2
from app.models.recommendation import Recommendation
from app.models.utilization_metric import UtilizationMetric
import pytest
from sqlalchemy.exc import IntegrityError



def test_scan_run_create_and_flush():
    db = SessionLocal()
    try:
        run = ScanRun(
        run_id=1,
        model_version="v1.0",
        id_filter=[101, 102, 103],
        region_filter=["us-east-1", "eu-west-1"],
        observation_window="30d",
        status=FindingStatus.open,
        started_on=datetime(2025, 1, 1, 12, 0, 0),
        completed_on=datetime(2025, 1, 1, 13, 0, 0),
        scanned_count=0,
        initiated_by="test_user",)
        db.add(run)
        db.flush()
    finally:
        db.rollback()
        db.close()


def test_ec2_instance_create_and_flush():
    db = SessionLocal()
    try:
        instance = EC2Instance(
            resource_id=1,
            arn="arn:aws:ec2:us-east-1:123456789:instance/i-abc123",
            region="us-east-1",
            owner_id=123456789,
            architecture="x86_64",
            platform="linux",
            tenancy="default",
            tags=["env:prod", "team:backend"],
        )
        db.add(instance)
        db.flush()
        assert instance.resource_id == 1
    finally:
        db.rollback()
        db.close()




def test_recommendation_create_and_flush():
    db = SessionLocal()
    try:
        rec = Recommendation(
            recommendation_id=1,
            finding_id=1,
            recommended_config="m5.large",
            optimization_category="rightsizing",
            monthly_cost_impact=-25.50,
            confidence=0.92,
            status="active",
            created_on=datetime(2025, 1, 1),
            updated_on=datetime(2025, 1, 2),
        )
        db.add(rec)
        db.flush()
        assert rec.recommendation_id == 1
    finally:
        db.rollback()
        db.close()


def test_utilization_metric_create_and_flush():
    db = SessionLocal()
    try:
        run = ScanRun(
            run_id=1,
            model_version="v1.0",
            id_filter=[101],
            region_filter=["us-east-1"],
            observation_window="30d",
            status=FindingStatus.open,
            started_on=datetime(2025, 1, 1, 12, 0, 0),
            completed_on=datetime(2025, 1, 1, 13, 0, 0),
            scanned_count=0,
            initiated_by="test_user",
        )
        db.add(run)
        db.flush()

        instance = EC2Instance(
            resource_id=1,
            arn="arn:aws:ec2:us-east-1:123456789:instance/i-abc123",
            region="us-east-1",
            owner_id=123456789,
            architecture="x86_64",
            platform="linux",
            tenancy="default",
            tags=["env:prod", "team:backend"],
        )
        db.add(instance)
        db.flush()

        finding = Finding(
            finding_id=1,
            run_id=1,
            resource_id=1,
            utilization_metric_id=1,
            assessment="undersized",
            status=FindingStatus_2.open,
            created_on=datetime(2025, 1, 1),
            updated_on=datetime(2025, 1, 2),
            recommendations=[10, 11],
            constraints="memory_bound",
        )
        db.add(finding)
        db.flush()

        metric = UtilizationMetric(
            metric_id=1,
            run_id=1,
            resource_id=1,
            window_start=datetime(2025, 1, 1),
            window_end=datetime(2025, 1, 31),
            period=300,
            source="cloudwatch",
            missing_data=0.05,
            cpu_avg=12.5,
            cpu_max=85.0,
            cpu_p95=45.2,
            cpu_p99=72.1,
            power_avg=10.0,
            power_max=60.0,
            power_p95=35.0,
            power_p99=55.0,
            memory_avg=65.3,
            memory_max=92.0,
            memory_p95=80.5,
            memory_p99=88.7,
            network_avg=5.2,
            network_max=50.0,
            network_p95=20.0,
            network_p99=40.0,
        )
        db.add(metric)
        db.flush()
        assert metric.metric_id == 1
    finally:
        db.rollback()
        db.close()


def test_finding_metric_requires_valid_run_id():
    db = SessionLocal()
    try:
        finding = Finding(
            finding_id=1,
            run_id=1012,
            resource_id=1,
            utilization_metric_id=1,
            assessment="undersized",
            status=FindingStatus_2.open,
            created_on=datetime(2025, 1, 1),
            updated_on=datetime(2025, 1, 2),
            recommendations=[10, 11],
            constraints="memory_bound",
        )
        db.add(finding)
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()


def test_utilization_metric_requires_valid_run_id():
    db = SessionLocal()
    try:
        metric = UtilizationMetric(
            metric_id=99,
            run_id=999,  # no ScanRun with this id exists
            resource_id=1,
            window_start=datetime(2025, 1, 1),
            window_end=datetime(2025, 1, 31),
            period=300,
            source="cloudwatch",
        )
        db.add(metric)
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()