
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.models.ec2_instance import EC2Instance
from app.schemas.ec2_instance_schema import (
    EC2InstanceCreate,
    EC2InstanceResponse,
    EC2InstanceListResponse,
)


insta_router = APIRouter(prefix="/instances", tags=["instance"])


#POST /instances create/upsert an instance (you decide behavior)

@insta_router.post("/", response_model=EC2InstanceResponse, status_code=201)
def create_or_update_instance(payload: EC2InstanceCreate, db: Session = Depends(get_db)):
    existing = db.query(EC2Instance).filter(EC2Instance.arn == payload.arn).first()

    if existing:
        existing.region = payload.region
        existing.owner_id = payload.owner_id
        existing.architecture = payload.architecture
        existing.platform = payload.platform
        existing.tenancy = payload.tenancy
        existing.tags = payload.tags
        db.commit()
        db.refresh(existing)
        return existing

    new_instance = EC2Instance(
        arn=payload.arn,
        region=payload.region,
        owner_id=payload.owner_id,
        architecture=payload.architecture,
        platform=payload.platform,
        tenancy=payload.tenancy,
        tags=payload.tags,
    )
    db.add(new_instance)
    db.commit()
    db.refresh(new_instance)
    return new_instance



#GET /instances list instances (filters: account/region/instance_id)
@insta_router.get("/", response_model=EC2InstanceListResponse)
def list_instances(
    owner_id: Optional[int] = Query(None, description="Filter by AWS account (owner ID)"),
    region: Optional[str] = Query(None, description="Filter by AWS region"),
    resource_id: Optional[int] = Query(None, description="Filter by instance resource ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),):
    query = db.query(EC2Instance)

    if owner_id is not None:
        query = query.filter(EC2Instance.owner_id == owner_id)
    if region is not None:
        query = query.filter(EC2Instance.region == region)
    if resource_id is not None:
        query = query.filter(EC2Instance.resource_id == resource_id)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return EC2InstanceListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )



#GET /instances/{resource_id} get one
@insta_router.get("/{resource_id}", response_model=EC2InstanceResponse)
def get_instance(resource_id: int, db: Session = Depends(get_db)):
    instance = db.query(EC2Instance).filter(EC2Instance.resource_id == resource_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail=f"Instance {resource_id} not found")
    return instance