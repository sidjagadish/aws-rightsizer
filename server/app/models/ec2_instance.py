from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY

from app.db import Base


class EC2Instance(Base):
    __tablename__ = "ec2_instance"

    resource_id = Column(Integer, primary_key=True)
    arn = Column(String, nullable=False)
    region = Column(String, nullable=False)
    owner_id = Column(Integer, nullable=False)
    architecture = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    tenancy = Column(String, nullable=False)
    tags = Column(ARRAY(String), nullable=True)