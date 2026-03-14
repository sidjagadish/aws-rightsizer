from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY

from app.db import Base


class EC2Instance(Base):
    __tablename__ = "ec2_instance"

    resource_id = Column(Integer, primary_key=True,autoincrement=True)
    arn = Column(String, unique=True, nullable=False, index=True)
    region = Column(String, nullable=False, index=True)
    owner_id = Column(Integer, nullable=False, index=True)
    architecture = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    tenancy = Column(String, nullable=False)
    tags = Column(ARRAY(String), nullable=True)


