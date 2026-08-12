"""DataVista+ ORM Models - Insights, Recommendations, KPIs"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    insight_type = Column(String(100))  # trend, anomaly, correlation, summary
    title = Column(String(500))
    description = Column(Text)
    supporting_data = Column(JSON)
    confidence_score = Column(Float)
    impact_level = Column(String(50))  # high, medium, low
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dataset = relationship("Dataset", back_populates="insights")
    recommendations = relationship("Recommendation", back_populates="insight")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    insight_id = Column(Integer, ForeignKey("insights.id"))
    title = Column(String(500))
    description = Column(Text)
    action_items = Column(JSON)
    priority = Column(Integer, default=5)
    expected_impact = Column(Text)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    insight = relationship("Insight", back_populates="recommendations")


class BusinessKPI(Base):
    __tablename__ = "business_kpis"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    name = Column(String(255), nullable=False)
    value = Column(Float)
    unit = Column(String(50))
    comparison_value = Column(Float)
    change_percent = Column(Float)
    trend = Column(String(50))  # up, down, stable
    threshold_min = Column(Float)
    threshold_max = Column(Float)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    dataset = relationship("Dataset", back_populates="kpis")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(255), nullable=False)
    kpi_name = Column(String(255))
    condition = Column(String(50))  # gt, lt, eq, gte, lte
    threshold_value = Column(Float)
    is_active = Column(Boolean, default=True)
    email_notify = Column(Boolean, default=False)
    last_triggered = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="alerts")
