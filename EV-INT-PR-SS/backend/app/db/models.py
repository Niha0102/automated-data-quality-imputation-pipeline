import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer,
    Numeric, String, Text, BigInteger, JSON
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


def _uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    datasets = relationship("Dataset", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    format = Column(String(20), nullable=False)
    row_count = Column(BigInteger, nullable=True)
    column_count = Column(Integer, nullable=True)
    file_path = Column(Text, nullable=True)
    is_baseline = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="datasets")
    versions = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="dataset", cascade="all, delete-orphan")


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(String(36), primary_key=True, default=_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    job_id = Column(String(36), nullable=True)
    file_path = Column(Text, nullable=False)
    transform_params = Column(JSON, nullable=True)
    quality_score = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    dataset = relationship("Dataset", back_populates="versions")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="PENDING")
    pipeline_config = Column(JSON, nullable=False, default=dict)
    progress = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    dataset = relationship("Dataset", back_populates="jobs")
    user = relationship("User", back_populates="jobs")
    alerts = relationship("Alert", back_populates="job")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=True)
    type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    is_resolved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="alerts")
    job = relationship("Job", back_populates="alerts")
