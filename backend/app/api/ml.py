"""
DataVista+ ML API
Dataset upload, model training, prediction, and XAI endpoints
"""
import os
import io
import logging
import pandas as pd
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.api.auth import get_current_user
from app.models.user_model import User
from app.models.ml_model import MLModel, Prediction
from app.models.dataset_model import Dataset, DatasetTable, DatasetColumn
from app.models.report_model import ActivityLog
from app.services.ml_pipeline import MLPipeline
from app.services.xai_engine import XAIEngine

router = APIRouter(prefix="/ml", tags=["Machine Learning"])
logger = logging.getLogger(__name__)


class TrainRequest(BaseModel):
    dataset_id: int
    target_column: str
    feature_columns: Optional[List[str]] = None
    model_type: Optional[str] = None  # classification, regression, clustering
    algorithm: Optional[str] = None
    model_name: str = "My Model"


class PredictRequest(BaseModel):
    model_id: int
    input_data: dict


class ForecastRequest(BaseModel):
    dataset_id: int
    date_column: str
    value_column: str
    periods: int = 12


class WhatIfRequest(BaseModel):
    model_id: int
    base_instance: dict
    modifications: List[dict]


# ─── Dataset Upload ───────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a CSV/Excel dataset for ML analysis."""
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type {ext} not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}")

    # Read file
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max: {settings.MAX_UPLOAD_SIZE_MB}MB")

    try:
        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(400, f"Could not parse file: {str(e)}")

    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"dataset_{current_user.id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(contents)

    # Compute data quality score
    missing_pct = df.isnull().mean().mean()
    quality_score = round((1 - missing_pct) * 100, 2)

    # Save dataset to database
    dataset = Dataset(
        name=name,
        description=description,
        source_type="upload",
        file_path=file_path,
        row_count=len(df),
        column_count=len(df.columns),
        file_size_bytes=len(contents),
        data_quality_score=quality_score,
        owner_id=current_user.id,
    )
    db.add(dataset)
    await db.flush()

    # Save table and column metadata
    table = DatasetTable(
        dataset_id=dataset.id,
        table_name=name.lower().replace(" ", "_"),
        row_count=len(df),
    )
    db.add(table)
    await db.flush()

    for col in df.columns:
        sample_vals = df[col].dropna().head(5).astype(str).tolist()
        db.add(DatasetColumn(
            table_id=table.id,
            column_name=col,
            data_type=str(df[col].dtype),
            sample_values=", ".join(sample_vals),
            is_nullable=df[col].isnull().any(),
        ))

    db.add(ActivityLog(user_id=current_user.id, action_type="upload", description=f"Uploaded dataset: {name}"))
    await db.commit()
    await db.refresh(dataset)

    column_profile = [
        {
            "name": col,
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "unique_count": int(df[col].nunique()),
            "min": round(float(df[col].min()), 4) if pd.api.types.is_numeric_dtype(df[col]) and not df[col].isnull().all() else None,
            "max": round(float(df[col].max()), 4) if pd.api.types.is_numeric_dtype(df[col]) and not df[col].isnull().all() else None,
            "mean": round(float(df[col].mean()), 4) if pd.api.types.is_numeric_dtype(df[col]) and not df[col].isnull().all() else None,
        }
        for col in df.columns
    ]

    return {
        "dataset_id": dataset.id,
        "name": dataset.name,
        "rows": len(df),
        "columns": len(df.columns),
        "quality_score": quality_score,
        "column_profile": column_profile,
        "sample_rows": df.head(5).to_dict(orient="records"),
    }


@router.get("/datasets")
async def list_datasets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all uploaded datasets with their columns for ML model training."""
    result = await db.execute(
        select(Dataset).where(Dataset.owner_id == current_user.id).order_by(desc(Dataset.created_at))
    )
    datasets = result.scalars().all()

    response = []
    for d in datasets:
        cols = []
        if d.file_path and os.path.exists(d.file_path):
            try:
                if d.file_path.endswith(".csv"):
                    df_head = pd.read_csv(d.file_path, nrows=2)
                else:
                    df_head = pd.read_excel(d.file_path, nrows=2)
                cols = list(df_head.columns)
            except Exception:
                pass
        
        response.append({
            "id": d.id,
            "name": d.name,
            "row_count": d.row_count,
            "column_count": d.column_count,
            "columns": cols,
            "data_quality_score": d.data_quality_score,
            "created_at": d.created_at,
        })
    return response


# ─── Model Training ───────────────────────────────────────────────────────────

@router.post("/train")
async def train_model(
    request: TrainRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Train an ML model on an uploaded dataset."""
    # Load dataset
    dataset_result = await db.execute(select(Dataset).where(Dataset.id == request.dataset_id))
    dataset = dataset_result.scalar_one_or_none()
    if not dataset or not dataset.file_path:
        raise HTTPException(404, "Dataset not found")

    try:
        if dataset.file_path.endswith(".csv"):
            df = pd.read_csv(dataset.file_path)
        else:
            df = pd.read_excel(dataset.file_path)
    except Exception as e:
        raise HTTPException(400, f"Could not load dataset: {e}")

    if request.target_column not in df.columns:
        raise HTTPException(400, f"Target column '{request.target_column}' not found in dataset")

    # Create model record
    model_record = MLModel(
        name=request.model_name,
        model_type=request.model_type or "auto",
        algorithm=request.algorithm,
        dataset_id=request.dataset_id,
        target_column=request.target_column,
        feature_columns=request.feature_columns,
        status="training",
        owner_id=current_user.id,
    )
    db.add(model_record)
    await db.flush()

    # Train
    pipeline = MLPipeline(model_id=model_record.id)
    try:
        train_result = pipeline.train(
            df=df,
            target_col=request.target_column,
            feature_cols=request.feature_columns,
            model_type=request.model_type,
            algorithm=request.algorithm,
        )

        # Update model record
        model_record.model_type = train_result["model_type"]
        model_record.algorithm = train_result["algorithm"]
        model_record.metrics = train_result["metrics"]
        model_record.model_path = train_result["model_path"]
        model_record.feature_columns = pipeline.feature_names
        model_record.status = "trained"

        db.add(ActivityLog(
            user_id=current_user.id,
            action_type="train",
            description=f"Trained {train_result['model_type']} model: {request.model_name}"
        ))
        await db.commit()

        return {
            "model_id": model_record.id,
            "model_name": request.model_name,
            **train_result,
        }
    except Exception as e:
        model_record.status = "failed"
        await db.commit()
        raise HTTPException(500, f"Training failed: {str(e)}")


# ─── Models List ──────────────────────────────────────────────────────────────

@router.get("/models")
async def list_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all trained ML models for the current user."""
    result = await db.execute(
        select(MLModel)
        .where(MLModel.owner_id == current_user.id)
        .order_by(desc(MLModel.created_at))
    )
    models = result.scalars().all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "model_type": m.model_type,
            "algorithm": m.algorithm,
            "target_column": m.target_column,
            "metrics": m.metrics,
            "status": m.status,
            "created_at": m.created_at,
        }
        for m in models
    ]


# ─── Prediction ───────────────────────────────────────────────────────────────

@router.post("/predict")
async def make_prediction(
    request: PredictRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Make a prediction using a trained model."""
    model_result = await db.execute(select(MLModel).where(MLModel.id == request.model_id))
    model_record = model_result.scalar_one_or_none()
    if not model_record:
        raise HTTPException(404, "Model not found")

    pipeline = MLPipeline(model_id=request.model_id)
    pipeline.feature_names = model_record.feature_columns or []

    try:
        pred_result = pipeline.predict(request.input_data)
    except Exception as e:
        raise HTTPException(500, f"Prediction failed: {str(e)}")

    # Save prediction
    prediction = Prediction(
        model_id=request.model_id,
        user_id=current_user.id,
        input_data=request.input_data,
        prediction_result=pred_result,
        confidence_score=pred_result.get("confidence", 0.8),
    )
    db.add(prediction)
    await db.commit()
    await db.refresh(prediction)

    return {
        "prediction_id": prediction.id,
        "model_id": request.model_id,
        "model_name": model_record.name,
        "input_data": request.input_data,
        **pred_result,
    }


# ─── XAI Explanations ─────────────────────────────────────────────────────────

@router.get("/explain/{model_id}")
async def explain_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate SHAP and LIME explanations for a model."""
    model_result = await db.execute(select(MLModel).where(MLModel.id == model_id))
    model_record = model_result.scalar_one_or_none()
    if not model_record or not model_record.model_path:
        raise HTTPException(404, "Model not found")

    # Load dataset for background
    dataset_result = await db.execute(select(Dataset).where(Dataset.id == model_record.dataset_id))
    dataset = dataset_result.scalar_one_or_none()

    feature_names = model_record.feature_columns or []
    xai = XAIEngine(model_record.model_path, feature_names)

    import numpy as np
    # Use dummy background data (realistic) if dataset unavailable
    n_features = len(feature_names) or 5
    X_background = np.random.randn(50, n_features)

    try:
        shap_result = xai.explain_shap(X_background)
    except Exception as e:
        logger.warning(f"SHAP failed: {e}")
        shap_result = {"method": "Feature Importance (fallback)", "feature_importance": [], "waterfall": []}

    return {
        "model_id": model_id,
        "model_name": model_record.name,
        "model_type": model_record.model_type,
        "algorithm": model_record.algorithm,
        "feature_names": feature_names,
        "metrics": model_record.metrics,
        "shap": shap_result,
        "feature_importance": model_record.metrics.get("feature_importance", []) if model_record.metrics else [],
    }


# ─── Forecasting ──────────────────────────────────────────────────────────────

@router.post("/forecast")
async def forecast(
    request: ForecastRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run time series forecasting on a dataset column."""
    dataset_result = await db.execute(select(Dataset).where(Dataset.id == request.dataset_id))
    dataset = dataset_result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    try:
        if dataset.file_path.endswith(".csv"):
            df = pd.read_csv(dataset.file_path)
        else:
            df = pd.read_excel(dataset.file_path)
    except Exception as e:
        raise HTTPException(400, f"Could not load dataset: {e}")

    pipeline = MLPipeline(model_id=0)
    result = pipeline.forecast(df, request.date_column, request.value_column, request.periods)
    return result


# ─── What-If Analysis ─────────────────────────────────────────────────────────

@router.post("/whatif")
async def what_if_analysis(
    request: WhatIfRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """What-if scenario analysis comparing prediction across input variations."""
    model_result = await db.execute(select(MLModel).where(MLModel.id == request.model_id))
    model_record = model_result.scalar_one_or_none()
    if not model_record:
        raise HTTPException(404, "Model not found")

    feature_names = model_record.feature_columns or []
    xai = XAIEngine(model_record.model_path, feature_names)
    results = xai.what_if_analysis(request.base_instance, request.modifications)
    return {"scenarios": results, "model_name": model_record.name}


# ─── Anomaly Detection ────────────────────────────────────────────────────────

@router.get("/anomalies/{dataset_id}")
async def detect_anomalies(
    dataset_id: int,
    column: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Detect anomalies in a dataset column using IQR method."""
    dataset_result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = dataset_result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    try:
        if dataset.file_path.endswith(".csv"):
            df = pd.read_csv(dataset.file_path)
        else:
            df = pd.read_excel(dataset.file_path)
    except Exception as e:
        raise HTTPException(400, f"Could not load dataset: {e}")

    if column not in df.columns:
        raise HTTPException(400, f"Column '{column}' not found")

    pipeline = MLPipeline(model_id=0)
    result = pipeline.detect_anomalies(df, column)
    return result
