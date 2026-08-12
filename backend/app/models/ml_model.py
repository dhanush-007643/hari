"""DataVista+ ORM Models - ML Models & Predictions"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class MLModel(Base):
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    model_type = Column(String(100), nullable=False)  # classification, regression, clustering, forecasting
    algorithm = Column(String(100))
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    target_column = Column(String(255))
    feature_columns = Column(JSON)
    hyperparameters = Column(JSON)
    metrics = Column(JSON)
    model_path = Column(String(500))
    status = Column(String(50), default="trained")
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    dataset = relationship("Dataset", back_populates="models")
    predictions = relationship("Prediction", back_populates="model")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("model_registry.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    input_data = Column(JSON)
    prediction_result = Column(JSON)
    confidence_score = Column(Float)
    shap_values = Column(JSON)
    lime_explanation = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    model = relationship("MLModel", back_populates="predictions")
    user = relationship("User", back_populates="predictions")
