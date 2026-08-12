"""DataVista+ ORM Models - Queries"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    natural_language_query = Column(Text, nullable=False)
    generated_sql = Column(Text)
    sql_explanation = Column(Text)
    intent = Column(String(100))
    confidence_score = Column(Float)
    execution_time_ms = Column(Integer)
    row_count_returned = Column(Integer)
    status = Column(String(50), default="success")
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="queries")
    dataset = relationship("Dataset", back_populates="queries")
    saved_query = relationship("SavedQuery", back_populates="query", uselist=False)
    feedback = relationship("Feedback", back_populates="query")


class SavedQuery(Base):
    __tablename__ = "saved_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query_id = Column(Integer, ForeignKey("queries.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_favorite = Column(Boolean, default=False)
    tags = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="saved_queries")
    query = relationship("Query", back_populates="saved_query")
