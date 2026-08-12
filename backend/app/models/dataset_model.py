"""DataVista+ ORM Models - Datasets"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    source_type = Column(String(50), default="upload")
    file_path = Column(String(500))
    connection_string = Column(String(1000))
    row_count = Column(Integer)
    column_count = Column(Integer)
    file_size_bytes = Column(Integer)
    data_quality_score = Column(Float)
    status = Column(String(50), default="active")
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="datasets")
    tables = relationship("DatasetTable", back_populates="dataset", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="dataset")
    models = relationship("MLModel", back_populates="dataset")
    insights = relationship("Insight", back_populates="dataset")
    kpis = relationship("BusinessKPI", back_populates="dataset")


class DatasetTable(Base):
    __tablename__ = "dataset_tables"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"))
    table_name = Column(String(255), nullable=False)
    row_count = Column(Integer)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dataset = relationship("Dataset", back_populates="tables")
    columns = relationship("DatasetColumn", back_populates="table", cascade="all, delete-orphan")


class DatasetColumn(Base):
    __tablename__ = "dataset_columns"

    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("dataset_tables.id", ondelete="CASCADE"))
    column_name = Column(String(255), nullable=False)
    data_type = Column(String(100))
    is_nullable = Column(Boolean, default=True)
    is_primary_key = Column(Boolean, default=False)
    is_foreign_key = Column(Boolean, default=False)
    sample_values = Column(Text)
    description = Column(Text)
    business_term = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    table = relationship("DatasetTable", back_populates="columns")
