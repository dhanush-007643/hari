"""
DataVista+ Insight Engine
Automatic business insight generation, root cause analysis, and recommendations
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from scipy import stats

logger = logging.getLogger(__name__)


class InsightEngine:
    """
    Automatically generates business insights from data:
    - Trend detection
    - Anomaly flagging
    - Correlation analysis
    - AI-generated narrative summaries
    - Root cause analysis
    - Business recommendations
    """

    def generate_insights(self, df: pd.DataFrame, dataset_name: str = "Dataset") -> List[Dict[str, Any]]:
        """Generate a comprehensive list of insights from a DataFrame."""
        insights = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
        date_cols = [c for c in df.columns if any(d in c.lower() for d in ["date", "time", "created"])]

        # 1. Data Overview
        insights.append(self._data_overview(df, dataset_name))

        # 2. Trend insights (for numeric + date columns)
        for date_col in date_cols[:2]:
            for num_col in numeric_cols[:3]:
                trend = self._analyze_trend(df, date_col, num_col)
                if trend:
                    insights.append(trend)

        # 3. Anomaly detection
        for col in numeric_cols[:5]:
            anomaly = self._detect_anomaly(df, col)
            if anomaly:
                insights.append(anomaly)

        # 4. Top performers / segments
        for cat_col in cat_cols[:3]:
            for num_col in numeric_cols[:2]:
                segment = self._segment_analysis(df, cat_col, num_col)
                if segment:
                    insights.append(segment)

        # 5. Correlation insights
        if len(numeric_cols) >= 2:
            correlations = self._correlation_analysis(df, numeric_cols[:8])
            if correlations:
                insights.extend(correlations[:3])

        # 6. Distribution insights
        for col in numeric_cols[:4]:
            dist = self._distribution_insight(df, col)
            if dist:
                insights.append(dist)

        return insights[:20]  # Cap at 20 insights

    def _data_overview(self, df: pd.DataFrame, name: str) -> Dict:
        """Generate a data overview insight."""
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        quality_score = round(100 - missing_pct.mean(), 1)

        return {
            "type": "summary",
            "title": f"Dataset Overview: {name}",
            "description": (
                f"The dataset contains **{len(df):,} rows** and **{len(df.columns)} columns**. "
                f"Data quality score is **{quality_score}%**. "
                f"There are {missing.sum()} missing values across all columns. "
                f"Numeric columns: {len(df.select_dtypes(include=[np.number]).columns)}, "
                f"Categorical: {len(df.select_dtypes(include='object').columns)}."
            ),
            "confidence_score": 1.0,
            "impact_level": "medium",
            "supporting_data": {
                "rows": len(df), "columns": len(df.columns),
                "missing_values": int(missing.sum()), "quality_score": quality_score
            }
        }

    def _analyze_trend(self, df: pd.DataFrame, date_col: str, value_col: str) -> Optional[Dict]:
        """Detect and describe a trend in a time series."""
        try:
            df_clean = df[[date_col, value_col]].dropna()
            df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors="coerce")
            df_clean = df_clean.dropna().sort_values(date_col)

            if len(df_clean) < 5:
                return None

            monthly = df_clean.groupby(df_clean[date_col].dt.to_period("M"))[value_col].sum()
            if len(monthly) < 3:
                return None

            # Linear regression for trend
            x = np.arange(len(monthly))
            slope, intercept, r_value, p_value, _ = stats.linregress(x, monthly.values)

            if p_value > 0.1:  # Not statistically significant
                return None

            direction = "upward" if slope > 0 else "downward"
            pct_change = abs(slope / monthly.mean() * 100) if monthly.mean() != 0 else 0
            confidence = min(0.5 + abs(r_value) * 0.5, 0.99)

            return {
                "type": "trend",
                "title": f"{direction.capitalize()} Trend in {value_col.replace('_', ' ').title()}",
                "description": (
                    f"{value_col.replace('_', ' ').title()} shows a consistent **{direction} trend** over time. "
                    f"The monthly change rate is approximately **{pct_change:.1f}%**. "
                    f"R² = {r_value**2:.2f}, indicating {'strong' if abs(r_value) > 0.7 else 'moderate'} correlation with time."
                ),
                "confidence_score": round(confidence, 2),
                "impact_level": "high" if pct_change > 10 else "medium",
                "supporting_data": {
                    "slope": round(slope, 4),
                    "r_squared": round(r_value**2, 4),
                    "direction": direction,
                    "monthly_avg": round(monthly.mean(), 2),
                }
            }
        except Exception as e:
            logger.exception(f"Trend analysis failed for {value_col}: {e}")
            return None

    def _detect_anomaly(self, df: pd.DataFrame, col: str) -> Optional[Dict]:
        """Detect anomalies using IQR method and generate insight."""
        try:
            values = df[col].dropna()
            if len(values) < 20:
                return None

            Q1, Q3 = values.quantile([0.25, 0.75])
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            anomalies = values[(values < lower) | (values > upper)]
            anomaly_rate = len(anomalies) / len(values) * 100

            if anomaly_rate < 1 or anomaly_rate > 30:
                return None

            return {
                "type": "anomaly",
                "title": f"Anomalies Detected in {col.replace('_', ' ').title()}",
                "description": (
                    f"**{len(anomalies)} anomalous values** ({anomaly_rate:.1f}% of data) detected in "
                    f"**{col.replace('_', ' ').title()}**. "
                    f"Expected range: [{lower:.2f}, {upper:.2f}]. "
                    f"These outliers may indicate data entry errors, exceptional events, or fraud."
                ),
                "confidence_score": 0.82,
                "impact_level": "high" if anomaly_rate > 5 else "medium",
                "supporting_data": {
                    "anomaly_count": int(len(anomalies)),
                    "anomaly_rate": round(anomaly_rate, 2),
                    "lower_bound": round(lower, 2),
                    "upper_bound": round(upper, 2),
                    "max_value": round(float(values.max()), 2),
                    "min_value": round(float(values.min()), 2),
                }
            }
        except Exception as e:
            logger.exception(f"Anomaly detection failed for {col}: {e}")
            return None

    def _segment_analysis(self, df: pd.DataFrame, cat_col: str, num_col: str) -> Optional[Dict]:
        """Analyze performance by segment/category."""
        try:
            if df[cat_col].nunique() > 20 or df[cat_col].nunique() < 2:
                return None

            agg = df.groupby(cat_col)[num_col].agg(["sum", "mean", "count"]).round(2)
            top = agg.sort_values("sum", ascending=False).head(3)
            bottom = agg.sort_values("sum").head(1)

            top_name = top.index[0]
            top_val = top["sum"].iloc[0]
            total = agg["sum"].sum()
            top_share = top_val / total * 100 if total > 0 else 0

            return {
                "type": "segment",
                "title": f"Top {cat_col.replace('_',' ').title()} by {num_col.replace('_',' ').title()}",
                "description": (
                    f"**{top_name}** leads in {num_col.replace('_', ' ')} with a total of "
                    f"**{top_val:,.2f}**, representing **{top_share:.1f}%** of the overall total. "
                    f"The least performing segment is **{bottom.index[0]}** with {bottom['sum'].iloc[0]:,.2f}."
                ),
                "confidence_score": 0.90,
                "impact_level": "high" if top_share > 30 else "medium",
                "supporting_data": {
                    "top_segments": top.reset_index().to_dict(orient="records"),
                    "total": round(float(total), 2),
                }
            }
        except Exception as e:
            logger.exception(f"Segment analysis failed for {cat_col} and {num_col}: {e}")
            return None

    def _correlation_analysis(self, df: pd.DataFrame, numeric_cols: List[str]) -> List[Dict]:
        """Find strong correlations between numeric columns."""
        insights = []
        try:
            corr_matrix = df[numeric_cols].corr()
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    col1, col2 = numeric_cols[i], numeric_cols[j]
                    r = corr_matrix.loc[col1, col2]
                    if abs(r) >= 0.65:
                        direction = "positive" if r > 0 else "negative"
                        strength = "strong" if abs(r) > 0.8 else "moderate"
                        insights.append({
                            "type": "correlation",
                            "title": f"{strength.capitalize()} Correlation: {col1.replace('_',' ').title()} & {col2.replace('_',' ').title()}",
                            "description": (
                                f"There is a **{strength} {direction} correlation** (r = {r:.2f}) between "
                                f"**{col1.replace('_', ' ')}** and **{col2.replace('_', ' ')}**. "
                                f"{'As one increases, so does the other.' if r > 0 else 'As one increases, the other tends to decrease.'}"
                            ),
                            "confidence_score": min(abs(r), 0.98),
                            "impact_level": "medium",
                            "supporting_data": {"correlation": round(float(r), 4), "col1": col1, "col2": col2}
                        })
        except Exception as e:
            logger.exception(f"Correlation analysis failed: {e}")
        return insights

    def _distribution_insight(self, df: pd.DataFrame, col: str) -> Optional[Dict]:
        """Analyze value distribution for skewness."""
        try:
            values = df[col].dropna()
            if len(values) < 30:
                return None
            skewness = values.skew()
            if abs(skewness) < 0.5:
                return None

            direction = "right (positive)" if skewness > 0 else "left (negative)"
            return {
                "type": "distribution",
                "title": f"Skewed Distribution in {col.replace('_', ' ').title()}",
                "description": (
                    f"**{col.replace('_', ' ').title()}** has a **{direction} skew** (skewness = {skewness:.2f}). "
                    f"{'Most values are concentrated on the lower end with a long tail of high values.' if skewness > 0 else 'Most values are concentrated on the higher end.'} "
                    f"Consider log transformation for modeling."
                ),
                "confidence_score": 0.78,
                "impact_level": "low",
                "supporting_data": {
                    "skewness": round(float(skewness), 4),
                    "mean": round(float(values.mean()), 2),
                    "median": round(float(values.median()), 2),
                    "std": round(float(values.std()), 2),
                }
            }
        except Exception as e:
            logger.exception(f"Distribution insight analysis failed for {col}: {e}")
            return None

    def generate_kpis(self, df: pd.DataFrame) -> List[Dict]:
        """Auto-detect and compute business KPIs from a DataFrame."""
        kpis = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        # Revenue / Amount KPIs
        for col in numeric_cols:
            col_lower = col.lower()
            if any(kw in col_lower for kw in ["revenue", "amount", "sales", "income"]):
                total = df[col].sum()
                avg = df[col].mean()
                kpis.append({"name": f"Total {col.replace('_',' ').title()}", "value": round(float(total), 2), "unit": "USD", "trend": "up"})
                kpis.append({"name": f"Avg {col.replace('_',' ').title()}", "value": round(float(avg), 2), "unit": "USD", "trend": "stable"})

        # Count KPIs
        kpis.append({"name": "Total Records", "value": int(len(df)), "unit": "records", "trend": "up"})

        # Unique counts
        for col in df.columns:
            if any(kw in col.lower() for kw in ["customer", "product", "employee", "user"]):
                if col in df.columns:
                    unique_count = df[col].nunique()
                    kpis.append({"name": f"Unique {col.replace('_id', '').replace('_', ' ').title()}s", "value": int(unique_count), "unit": "count", "trend": "up"})

        return kpis[:8]

    def generate_recommendations(self, insights: List[Dict]) -> List[Dict]:
        """Generate actionable recommendations from insights."""
        recommendations = []
        for insight in insights:
            if insight["type"] == "trend" and insight.get("supporting_data", {}).get("direction") == "downward":
                recommendations.append({
                    "title": "Reverse Declining Trend",
                    "description": f"Based on the downward trend detected, immediate action may be needed.",
                    "action_items": [
                        "Investigate root cause of the decline",
                        "Review recent changes in operations or market conditions",
                        "Set up monitoring alerts for this metric"
                    ],
                    "priority": 1,
                    "expected_impact": "Stabilize metrics within 30 days",
                })
            elif insight["type"] == "anomaly":
                recommendations.append({
                    "title": "Investigate Data Anomalies",
                    "description": f"Anomalies detected require investigation to ensure data integrity.",
                    "action_items": [
                        "Review flagged records for data entry errors",
                        "Check for system or process changes causing outliers",
                        "Implement automated anomaly alerting"
                    ],
                    "priority": 2,
                    "expected_impact": "Improve data quality score by 5-10%",
                })
            elif insight["type"] == "segment" and insight["impact_level"] == "high":
                recommendations.append({
                    "title": "Capitalize on Top Performing Segment",
                    "description": "Allocate more resources to your best-performing segment.",
                    "action_items": [
                        "Increase marketing budget for top segment by 20%",
                        "Analyze what makes this segment successful",
                        "Apply successful strategies to other segments"
                    ],
                    "priority": 3,
                    "expected_impact": "Potential 10-15% revenue increase",
                })

        return recommendations
