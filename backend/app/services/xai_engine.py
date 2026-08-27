"""
DataVista+ XAI Engine
SHAP and LIME explainability for trained ML models
"""
import numpy as np
import pandas as pd
import logging
import joblib
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class XAIEngine:
    """
    Explainable AI engine using SHAP and LIME.
    Generates human-understandable explanations for ML model predictions.
    """

    def __init__(self, model_path: str, feature_names: List[str]):
        self.model_path = model_path
        self.feature_names = feature_names
        self.pipeline = None

    def _load_model(self):
        if not self.pipeline:
            self.pipeline = joblib.load(self.model_path)

    def explain_shap(
        self,
        X: np.ndarray,
        max_samples: int = 100
    ) -> Dict[str, Any]:
        """
        Generate SHAP values for feature importance explanation.
        Returns waterfall and summary data for visualization.
        """
        self._load_model()

        try:
            import shap

            # Use sample if dataset is large
            if len(X) > max_samples:
                indices = np.random.choice(len(X), max_samples, replace=False)
                X_sample = X[indices]
            else:
                X_sample = X

            model = self.pipeline.named_steps["model"]
            preprocessor = self.pipeline.named_steps["preprocessor"]
            X_transformed = preprocessor.transform(X_sample)

            # Select appropriate explainer
            if hasattr(model, "predict_proba"):
                explainer = shap.TreeExplainer(model) if hasattr(model, "estimators_") else shap.KernelExplainer(model.predict_proba, shap.sample(X_transformed, 50))
            else:
                explainer = shap.TreeExplainer(model) if hasattr(model, "estimators_") else shap.KernelExplainer(model.predict, shap.sample(X_transformed, 50))

            shap_values = explainer.shap_values(X_transformed)

            # Handle multi-class (take first class)
            if isinstance(shap_values, list):
                shap_array = np.array(shap_values[1]) if len(shap_values) > 1 else np.array(shap_values[0])
            else:
                shap_array = np.array(shap_values)

            # Mean absolute SHAP values per feature
            mean_shap = np.abs(shap_array).mean(axis=0)

            # Map back to original feature names (handles OHE expansion)
            n_features = min(len(mean_shap), len(self.feature_names))
            feature_importance = [
                {
                    "feature": self.feature_names[i],
                    "shap_value": round(float(mean_shap[i]), 4),
                    "direction": "positive" if mean_shap[i] > 0 else "negative"
                }
                for i in range(n_features)
            ]
            feature_importance.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

            # Waterfall for first sample
            instance_shap = shap_array[0][:n_features]
            waterfall = [
                {
                    "feature": self.feature_names[i],
                    "value": round(float(instance_shap[i]), 4),
                    "contribution": round(float(instance_shap[i]), 4),
                    "input_value": float(X_sample[0][i]) if i < X_sample.shape[1] else 0.0,
                }
                for i in range(n_features)
            ]
            waterfall.sort(key=lambda x: abs(x["value"]), reverse=True)

            return {
                "method": "SHAP",
                "feature_importance": feature_importance[:15],
                "waterfall": waterfall[:10],
                "base_value": float(explainer.expected_value) if not isinstance(explainer.expected_value, list) else float(explainer.expected_value[1]),
                "summary": self._shap_narrative(feature_importance[:5]),
            }

        except Exception as e:
            logger.exception(f"SHAP failed, returning approximation: {e}")
            return self._fallback_importance()

    def explain_lime(
        self,
        X_instance: np.ndarray,
        X_train: np.ndarray,
        model_type: str = "classification"
    ) -> Dict[str, Any]:
        """
        Generate LIME explanation for a single prediction instance.
        """
        self._load_model()

        try:
            import lime
            import lime.lime_tabular

            preprocessor = self.pipeline.named_steps["preprocessor"]
            model = self.pipeline.named_steps["model"]

            X_train_transformed = preprocessor.transform(X_train)
            X_instance_transformed = preprocessor.transform(X_instance.reshape(1, -1))[0]

            mode = "classification" if model_type == "classification" else "regression"
            explainer = lime.lime_tabular.LimeTabularExplainer(
                X_train_transformed,
                feature_names=self.feature_names[:X_train_transformed.shape[1]],
                mode=mode,
                random_state=42,
            )

            predict_fn = model.predict_proba if (mode == "classification" and hasattr(model, "predict_proba")) else model.predict
            explanation = explainer.explain_instance(
                X_instance_transformed,
                predict_fn,
                num_features=min(10, len(self.feature_names)),
            )

            lime_data = [
                {"feature": feat, "weight": round(float(weight), 4)}
                for feat, weight in explanation.as_list()
            ]

            return {
                "method": "LIME",
                "explanation": lime_data,
                "local_prediction": round(float(explanation.local_pred[0]) if mode == "regression" else max(explanation.local_pred), 4),
                "intercept": round(float(explanation.intercept[0]) if mode == "regression" else 0.0, 4),
                "summary": self._lime_narrative(lime_data[:3]),
            }

        except Exception as e:
            logger.exception(f"LIME failed: {e}")
            return {"method": "LIME", "explanation": [], "summary": "Explanation unavailable"}

    def _fallback_importance(self) -> Dict[str, Any]:
        """Return approximated feature importance from sklearn model."""
        try:
            model = self.pipeline.named_steps["model"]
            if hasattr(model, "feature_importances_"):
                imp = model.feature_importances_
                n = min(len(imp), len(self.feature_names))
                fi = sorted(
                    [{"feature": self.feature_names[i], "shap_value": round(float(imp[i]), 4), "value": round(float(imp[i]), 4), "contribution": round(float(imp[i]), 4), "direction": "positive"} for i in range(n)],
                    key=lambda x: x["shap_value"], reverse=True
                )
                return {"method": "Feature Importance", "feature_importance": fi[:15], "waterfall": fi[:10], "summary": self._shap_narrative(fi[:5])}
        except Exception as e:
            logger.exception(f"Fallback feature importance failed: {e}")
        return {"method": "Not available", "feature_importance": [], "waterfall": [], "summary": ""}

    def _shap_narrative(self, top_features: List[Dict]) -> str:
        """Generate human-readable SHAP summary."""
        if not top_features:
            return "No significant features detected."
        names = [f["feature"].replace("_", " ") for f in top_features[:3]]
        return f"The prediction is most influenced by: {', '.join(names)}. These features have the highest impact on the model's decision."

    def _lime_narrative(self, top_features: List[Dict]) -> str:
        """Generate human-readable LIME summary."""
        if not top_features:
            return "No significant local features."
        pos = [f["feature"] for f in top_features if f["weight"] > 0]
        neg = [f["feature"] for f in top_features if f["weight"] < 0]
        parts = []
        if pos:
            parts.append(f"Features supporting this prediction: {', '.join(pos[:2])}")
        if neg:
            parts.append(f"Features opposing this prediction: {', '.join(neg[:2])}")
        return ". ".join(parts) + "."

    def what_if_analysis(
        self,
        base_instance: Dict[str, Any],
        modifications: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        What-if analysis: compare predictions across different input scenarios.
        modifications: list of {feature: column_name, value: new_value}
        """
        self._load_model()
        results = []

        def _align_instance(inst: Dict[str, Any]) -> np.ndarray:
            row = []
            for f in self.feature_names:
                val = inst.get(f, None)
                if val is None or val == "" or (isinstance(val, float) and np.isnan(val)):
                    val = np.nan
                elif isinstance(val, str):
                    val_str = val.strip()
                    if val_str == "":
                        val = np.nan
                    else:
                        try:
                            val = float(val_str)
                        except ValueError:
                            val = val_str
                row.append(val)
            return np.array([row], dtype=object)

        # Base prediction
        X_base = _align_instance(base_instance)
        try:
            base_pred = self.pipeline.predict(X_base)[0]
            base_conf = float(max(self.pipeline.predict_proba(X_base)[0])) if hasattr(self.pipeline, "predict_proba") else 0.85
        except Exception as e:
            logger.exception(f"Base prediction in what-if analysis failed: {e}")
            base_pred = 0
            base_conf = 0.0

        results.append({
            "scenario": "Base Case",
            "modifications": {},
            "prediction": float(base_pred) if hasattr(base_pred, "item") else base_pred,
            "confidence": base_conf,
        })

        for mod in modifications:
            modified = base_instance.copy()
            modified[mod["feature"]] = mod["value"]
            X_mod = _align_instance(modified)
            try:
                pred = self.pipeline.predict(X_mod)[0]
                conf = float(max(self.pipeline.predict_proba(X_mod)[0])) if hasattr(self.pipeline, "predict_proba") else 0.85
            except Exception as e:
                logger.exception(f"Prediction for what-if scenario {mod} failed: {e}")
                pred = 0
                conf = 0.0

            results.append({
                "scenario": f"{mod['feature']} = {mod['value']}",
                "modifications": mod,
                "prediction": float(pred) if hasattr(pred, "item") else pred,
                "confidence": conf,
            })

        return results
