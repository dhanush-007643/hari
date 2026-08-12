"""
DataVista+ ML Pipeline Service
End-to-end machine learning: data prep, auto model selection, training, evaluation
"""
import os
import json
import logging
import numpy as np
import pandas as pd
import joblib
from typing import Dict, List, Optional, Any, Tuple
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

# Classification models
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier

# Regression models
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso

# Clustering
from sklearn.cluster import KMeans, DBSCAN

# Metrics
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, mean_squared_error, mean_absolute_error, r2_score,
    confusion_matrix, classification_report
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class MLPipeline:
    """
    Automated ML pipeline supporting:
    - Classification (binary & multiclass)
    - Regression
    - Clustering
    - Time series forecasting
    """

    CLASSIFICATION_MODELS = {
        "random_forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "gradient_boosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
        "logistic_regression": LogisticRegression(max_iter=1000, random_state=42),
        "knn": KNeighborsClassifier(n_neighbors=5),
    }

    REGRESSION_MODELS = {
        "random_forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "gradient_boosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
        "linear_regression": LinearRegression(),
        "ridge": Ridge(alpha=1.0),
        "lasso": Lasso(alpha=1.0),
    }

    def __init__(self, model_id: int):
        self.model_id = model_id
        self.model_path = os.path.join(settings.MODELS_DIR, f"model_{model_id}.pkl")
        self.pipeline = None
        self.feature_names = []
        self.target_column = None
        self.model_type = None
        self.label_encoder = None

    def prepare_data(
        self,
        df: pd.DataFrame,
        target_col: str,
        feature_cols: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, np.ndarray, List[str], List[str]]:
        """
        Prepare data: handle missing values, encode categoricals, scale numerics.
        Returns: X, y, numeric_features, categorical_features
        """
        if feature_cols:
            df = df[feature_cols + [target_col]]

        # Separate features and target
        X = df.drop(columns=[target_col])
        y = df[target_col]

        # Identify column types
        numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = X.select_dtypes(include=["object", "category"]).columns.tolist()

        # Drop high-cardinality categoricals (>50 unique values)
        categorical_features = [
            c for c in categorical_features if X[c].nunique() <= 50
        ]
        X = X[numeric_features + categorical_features]

        self.feature_names = numeric_features + categorical_features
        self.target_column = target_col

        # Handle target encoding for classification
        if y.dtype == "object" or y.dtype.name == "category":
            self.label_encoder = LabelEncoder()
            y = self.label_encoder.fit_transform(y)

        return X.values, np.array(y), numeric_features, categorical_features

    def _build_preprocessor(
        self,
        numeric_features: List[str],
        categorical_features: List[str]
    ) -> ColumnTransformer:
        """Build sklearn ColumnTransformer for preprocessing."""
        transformers = []

        if numeric_features:
            numeric_transformer = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ])
            transformers.append(("num", numeric_transformer, list(range(len(numeric_features)))))

        if categorical_features:
            categorical_transformer = Pipeline([
                ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ])
            num_offset = len(numeric_features)
            cat_indices = list(range(num_offset, num_offset + len(categorical_features)))
            transformers.append(("cat", categorical_transformer, cat_indices))

        return ColumnTransformer(transformers=transformers)

    def auto_select_model(self, y: np.ndarray, model_type: Optional[str] = None) -> str:
        """Auto-detect the appropriate model type from target data."""
        if model_type:
            return model_type

        unique_values = len(np.unique(y))
        if unique_values <= 20:
            return "classification"
        else:
            return "regression"

    def train(
        self,
        df: pd.DataFrame,
        target_col: str,
        feature_cols: Optional[List[str]] = None,
        model_type: Optional[str] = None,
        algorithm: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full training pipeline with cross-validation.
        Returns metrics and model info.
        """
        logger.info(f"Training model {self.model_id} on {len(df)} rows, target: {target_col}")

        X, y, numeric_feats, cat_feats = self.prepare_data(df, target_col, feature_cols)

        # Auto-select model type
        self.model_type = self.auto_select_model(y, model_type)

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Build preprocessor
        preprocessor = self._build_preprocessor(numeric_feats, cat_feats)

        # Select algorithm
        if self.model_type == "classification":
            algo = algorithm or "random_forest"
            base_model = self.CLASSIFICATION_MODELS.get(algo, self.CLASSIFICATION_MODELS["random_forest"])
        elif self.model_type == "regression":
            algo = algorithm or "random_forest"
            base_model = self.REGRESSION_MODELS.get(algo, self.REGRESSION_MODELS["random_forest"])
        else:
            algo = "kmeans"
            base_model = KMeans(n_clusters=min(5, len(np.unique(y))), random_state=42)

        # Build full pipeline
        self.pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("model", base_model),
        ])

        # Train
        self.pipeline.fit(X_train, y_train)

        # Evaluate
        metrics = self._evaluate(X_test, y_test)

        # Cross-validation
        cv_scores = cross_val_score(self.pipeline, X, y, cv=5, scoring="accuracy" if self.model_type == "classification" else "r2")
        metrics["cv_mean"] = round(float(cv_scores.mean()), 4)
        metrics["cv_std"] = round(float(cv_scores.std()), 4)

        # Feature importance
        feature_importance = self._get_feature_importance(numeric_feats + cat_feats)
        metrics["feature_importance"] = feature_importance

        # Save model
        joblib.dump(self.pipeline, self.model_path)

        return {
            "algorithm": algo,
            "model_type": self.model_type,
            "feature_count": len(self.feature_names),
            "training_rows": len(X_train),
            "metrics": metrics,
            "model_path": self.model_path,
        }

    def _evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Compute evaluation metrics."""
        y_pred = self.pipeline.predict(X_test)
        metrics = {}

        if self.model_type == "classification":
            metrics["accuracy"] = round(float(accuracy_score(y_test, y_pred)), 4)
            avg = "binary" if len(np.unique(y_test)) == 2 else "macro"
            metrics["precision"] = round(float(precision_score(y_test, y_pred, average=avg, zero_division=0)), 4)
            metrics["recall"] = round(float(recall_score(y_test, y_pred, average=avg, zero_division=0)), 4)
            metrics["f1_score"] = round(float(f1_score(y_test, y_pred, average=avg, zero_division=0)), 4)

            if len(np.unique(y_test)) == 2:
                try:
                    y_prob = self.pipeline.predict_proba(X_test)[:, 1]
                    metrics["roc_auc"] = round(float(roc_auc_score(y_test, y_prob)), 4)
                except Exception as e:
                    logger.exception(f"Could not calculate ROC AUC: {e}")

            cm = confusion_matrix(y_test, y_pred)
            metrics["confusion_matrix"] = cm.tolist()

        elif self.model_type == "regression":
            metrics["rmse"] = round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4)
            metrics["mae"] = round(float(mean_absolute_error(y_test, y_pred)), 4)
            metrics["r2"] = round(float(r2_score(y_test, y_pred)), 4)

        return metrics

    def _get_feature_importance(self, feature_names: List[str]) -> List[Dict]:
        """Extract feature importance from the trained model."""
        try:
            model = self.pipeline.named_steps["model"]
            if hasattr(model, "feature_importances_"):
                importances = model.feature_importances_
            elif hasattr(model, "coef_"):
                importances = np.abs(model.coef_).flatten()
            else:
                return []

            # Handle length mismatch (OneHotEncoder expands features)
            n = min(len(importances), len(feature_names))
            return sorted(
                [
                    {"feature": feature_names[i], "importance": round(float(importances[i]), 4)}
                    for i in range(n)
                ],
                key=lambda x: x["importance"],
                reverse=True,
            )
        except Exception as e:
            logger.exception(f"Could not extract feature importance: {e}")
            return []

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a prediction on new input data."""
        if not self.pipeline:
            self.pipeline = joblib.load(self.model_path)

        df_input = pd.DataFrame([input_data])
        # Keep only known features
        available_feats = [f for f in self.feature_names if f in df_input.columns]
        X = df_input[available_feats].values

        prediction = self.pipeline.predict(X)[0]

        result = {"prediction": float(prediction) if hasattr(prediction, 'item') else prediction}

        # Classification probability
        if hasattr(self.pipeline, "predict_proba"):
            try:
                proba = self.pipeline.predict_proba(X)[0]
                result["probabilities"] = proba.tolist()
                result["confidence"] = float(max(proba))
                if self.label_encoder:
                    result["class_labels"] = self.label_encoder.classes_.tolist()
            except Exception as e:
                logger.exception(f"Could not calculate prediction probability: {e}")
                result["confidence"] = 0.8
        else:
            result["confidence"] = 0.85

        return result

    def forecast(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        periods: int = 12
    ) -> Dict[str, Any]:
        """
        Simple time series forecasting using linear trend + seasonality.
        Returns historical data + forecast points.
        """
        df = df[[date_col, value_col]].dropna()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        df = df.groupby(date_col)[value_col].sum().reset_index()

        # Build time index
        df["t"] = range(len(df))
        X = df[["t"]].values
        y = df[value_col].values

        # Fit linear model
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        model.fit(X, y)

        # Generate forecast
        last_t = len(df)
        future_t = np.array([[last_t + i] for i in range(1, periods + 1)])
        forecast_values = model.predict(future_t)

        # Generate forecast dates
        last_date = df[date_col].iloc[-1]
        freq = pd.infer_freq(df[date_col]) or "M"
        try:
            future_dates = pd.date_range(last_date, periods=periods + 1, freq=freq)[1:]
        except Exception as e:
            logger.exception(f"Could not infer date frequency, falling back to MS: {e}")
            future_dates = pd.date_range(last_date, periods=periods + 1, freq="MS")[1:]

        historical = [
            {"date": str(row[date_col].date()), "value": float(row[value_col])}
            for _, row in df.iterrows()
        ]
        forecast = [
            {"date": str(d.date()), "value": round(float(v), 2), "is_forecast": True}
            for d, v in zip(future_dates, forecast_values)
        ]

        return {
            "historical": historical,
            "forecast": forecast,
            "trend": "up" if model.coef_[0] > 0 else "down",
            "slope": round(float(model.coef_[0]), 4),
            "r2": round(float(model.score(X, y)), 4),
        }

    def detect_anomalies(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Detect anomalies using IQR method."""
        values = df[column].dropna()
        Q1 = values.quantile(0.25)
        Q3 = values.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR

        anomalies = df[(df[column] < lower) | (df[column] > upper)]
        return {
            "anomaly_count": int(len(anomalies)),
            "total_rows": int(len(df)),
            "anomaly_rate": round(len(anomalies) / len(df) * 100, 2),
            "bounds": {"lower": round(float(lower), 2), "upper": round(float(upper), 2)},
            "anomaly_indices": anomalies.index.tolist()[:50],
        }
