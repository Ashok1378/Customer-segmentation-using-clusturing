"""
segmentation.py - Business-level cluster profiling and segment labelling.
"""
import json
import os
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_PROFILES_PATH = os.path.join(settings.MODELS_DIR, "cluster_profiles.json")


class SegmentationService:
    """
    Generates human-readable cluster profiles and segment labels from raw
    clustering results.
    """

    # -----------------------------------------------------------------------
    # Label generation
    # -----------------------------------------------------------------------

    def generate_segment_label(
        self, profile: Dict[str, Any], overall_stats: Dict[str, Any]
    ) -> str:
        """
        Assign a descriptive label to a cluster based on its average feature
        values compared to overall dataset medians.

        Priority order (first match wins):
          1. High Income + High Spending  -> 'High Value Customers'
          2. Low Income  + Low  Spending  -> 'Budget Customers'
          3. High Frequency + High Spending -> 'Frequent Buyers'
          4. Low  Spending + Low Frequency  -> 'Low Engagement Customers'
          5. High Income  + Low  Spending   -> 'Conservative Spenders'
          6. Young (age < median) + High Spending -> 'Young Spenders'
          7. else -> 'Segment {cluster_id + 1}'
        """
        med_income = overall_stats.get("median_income", 0)
        med_spending = overall_stats.get("median_spending", 0)
        med_frequency = overall_stats.get("median_frequency", 0)
        med_age = overall_stats.get("median_age", 0)

        avg_income = profile.get("avg_income", 0)
        avg_spending = profile.get("avg_spending_score", 0)
        avg_frequency = profile.get("avg_purchase_frequency", 0)
        avg_age = profile.get("avg_age", 0)

        cluster_id = profile.get("cluster_id", 0)

        # Only apply customer-specific persona rules if income and spending actually exist in data
        if med_income > 0 and med_spending > 0:
            high_income = avg_income >= med_income
            low_income = avg_income < med_income
            high_spending = avg_spending >= med_spending
            low_spending = avg_spending < med_spending
            high_frequency = avg_frequency >= med_frequency
            low_frequency = avg_frequency < med_frequency
            young = avg_age < med_age if med_age > 0 else False

            if high_income and high_spending:
                return "High Value Customers"
            if low_income and low_spending:
                return "Budget Customers"
            if high_frequency and high_spending:
                return "Frequent Buyers"
            if low_spending and low_frequency:
                return "Low Engagement Customers"
            if high_income and low_spending:
                return "Conservative Spenders"
            if young and high_spending:
                return "Young Spenders"

        return f"Segment {cluster_id + 1}"

    # -----------------------------------------------------------------------
    # Characteristics
    # -----------------------------------------------------------------------

    def generate_characteristics(
        self, profile: Dict[str, Any], overall_stats: Dict[str, Any]
    ) -> List[str]:
        """
        Build a list of plain-English bullet points describing the cluster.
        Works for standard customer data and arbitrary uploaded datasets.
        """
        characteristics: List[str] = []

        avg_age = profile.get("avg_age", 0)
        avg_income = profile.get("avg_income", 0)
        avg_spending = profile.get("avg_spending_score", 0)
        avg_frequency = profile.get("avg_purchase_frequency", 0)
        size = profile.get("size", 0)
        feat_avgs = profile.get("feature_averages", {})

        med_income = overall_stats.get("median_income", 0)
        med_spending = overall_stats.get("median_spending", 0)
        med_frequency = overall_stats.get("median_frequency", 0)
        med_age = overall_stats.get("median_age", 0)

        # If standard customer columns are present
        if med_income > 0 and med_spending > 0:
            if med_age > 0 and avg_age > 0:
                if avg_age < med_age * 0.85:
                    characteristics.append(f"Younger customers (avg age: {avg_age:.0f})")
                elif avg_age > med_age * 1.15:
                    characteristics.append(f"Older customers (avg age: {avg_age:.0f})")
                else:
                    characteristics.append(f"Middle-aged customers (avg age: {avg_age:.0f})")

            income_k = avg_income / 1000
            if avg_income > med_income * 1.2:
                characteristics.append(f"High annual income (avg: ${income_k:.1f}k)")
            elif avg_income < med_income * 0.8:
                characteristics.append(f"Lower annual income (avg: ${income_k:.1f}k)")
            else:
                characteristics.append(f"Average annual income (avg: ${income_k:.1f}k)")

            if avg_spending > med_spending * 1.2:
                characteristics.append(f"High spending score (avg: {avg_spending:.1f}/100)")
            elif avg_spending < med_spending * 0.8:
                characteristics.append(f"Low spending score (avg: {avg_spending:.1f}/100)")
            else:
                characteristics.append(f"Moderate spending score (avg: {avg_spending:.1f}/100)")

            if med_frequency > 0 and avg_frequency > 0:
                if avg_frequency > med_frequency * 1.2:
                    characteristics.append(f"High purchase frequency (avg: {avg_frequency:.1f} purchases)")
                elif avg_frequency < med_frequency * 0.8:
                    characteristics.append(f"Low purchase frequency (avg: {avg_frequency:.1f} purchases)")
                else:
                    characteristics.append(f"Moderate purchase frequency (avg: {avg_frequency:.1f} purchases)")

        # For any custom or additional features present
        for feat, val in list(feat_avgs.items())[:4]:
            if feat not in ["Age", "AnnualIncome", "SpendingScore", "PurchaseFrequency"]:
                characteristics.append(f"Avg {feat.replace('_', ' ')}: {val:.2f}")

        characteristics.append(f"Cluster size: {size} records")
        return characteristics

    # -----------------------------------------------------------------------
    # Profile generation
    # -----------------------------------------------------------------------

    def generate_cluster_profiles(
        self,
        df_original: pd.DataFrame,
        labels: np.ndarray,
        features: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Compute per-cluster statistics from the original (unscaled) DataFrame
        and the cluster label array.

        Returns a list of profile dicts sorted by cluster_id, with noise
        cluster (-1 from DBSCAN) placed last if present.
        """
        df = df_original.copy()
        df["_cluster"] = labels

        # Helper to find column by keywords
        def _find_col(cols, keywords):
            for c in cols:
                clean = c.lower().replace(" ", "").replace("_", "").replace("-", "")
                for kw in keywords:
                    if kw in clean:
                        return c
            return None

        age_col = _find_col(df.columns, ["age"])
        income_col = _find_col(df.columns, ["annualincome", "income"])
        spending_col = _find_col(df.columns, ["spendingscore", "spending", "score"])
        frequency_col = _find_col(df.columns, ["purchasefrequency", "frequency", "purchase"])
        gender_col = _find_col(df.columns, ["gender", "sex"])

        # ── Overall stats for relative comparison ───────────────────────────
        overall_stats: Dict[str, Any] = {
            "median_age": float(df[age_col].median()) if age_col and df[age_col].dtype.kind in "iuf" else 0.0,
            "median_income": float(df[income_col].median()) if income_col and df[income_col].dtype.kind in "iuf" else 0.0,
            "median_spending": float(df[spending_col].median()) if spending_col and df[spending_col].dtype.kind in "iuf" else 0.0,
            "median_frequency": float(df[frequency_col].median()) if frequency_col and df[frequency_col].dtype.kind in "iuf" else 0.0,
        }

        profiles: List[Dict[str, Any]] = []

        unique_clusters = sorted(set(labels))
        # Move noise (-1) to end
        if -1 in unique_clusters:
            unique_clusters = [c for c in unique_clusters if c != -1] + [-1]

        for cluster_id in unique_clusters:
            cluster_df = df[df["_cluster"] == cluster_id]
            size = len(cluster_df)

            profile: Dict[str, Any] = {
                "cluster_id": int(cluster_id),
                "size": size,
            }

            # Safe column averages
            profile["avg_age"] = (
                float(round(cluster_df[age_col].mean(), 2)) if age_col and cluster_df[age_col].dtype.kind in "iuf" else 0.0
            )
            profile["avg_income"] = (
                float(round(cluster_df[income_col].mean(), 2))
                if income_col and cluster_df[income_col].dtype.kind in "iuf"
                else 0.0
            )
            profile["avg_spending_score"] = (
                float(round(cluster_df[spending_col].mean(), 2))
                if spending_col and cluster_df[spending_col].dtype.kind in "iuf"
                else 0.0
            )
            profile["avg_purchase_frequency"] = (
                float(round(cluster_df[frequency_col].mean(), 2))
                if frequency_col and cluster_df[frequency_col].dtype.kind in "iuf"
                else 0.0
            )

            # Gender distribution (if available)
            if gender_col and gender_col in cluster_df.columns:
                gender_counts = cluster_df[gender_col].value_counts().to_dict()
                profile["gender_distribution"] = {
                    str(k): int(v) for k, v in gender_counts.items()
                }

            # Feature-level averages for all requested features
            feature_avgs: Dict[str, float] = {}
            for feat in features:
                if feat in cluster_df.columns:
                    feature_avgs[feat] = float(round(cluster_df[feat].mean(), 4))
            profile["feature_averages"] = feature_avgs

            # Label and characteristics
            if cluster_id == -1:
                profile["label"] = "Noise / Outliers"
                profile["characteristics"] = ["Points not assigned to any cluster by DBSCAN"]
            else:
                profile["label"] = self.generate_segment_label(profile, overall_stats)
                profile["characteristics"] = self.generate_characteristics(
                    profile, overall_stats
                )

            profiles.append(profile)

        logger.info("Generated %d cluster profiles.", len(profiles))
        return profiles

    # -----------------------------------------------------------------------
    # Persistence
    # -----------------------------------------------------------------------

    def save_profiles(self, profiles: List[Dict[str, Any]]) -> None:
        """Save cluster profiles to backend/models/cluster_profiles.json."""
        os.makedirs(settings.MODELS_DIR, exist_ok=True)
        with open(_PROFILES_PATH, "w", encoding="utf-8") as fp:
            json.dump(profiles, fp, indent=2, default=str)
        logger.info("Cluster profiles saved to %s.", _PROFILES_PATH)

    def load_profiles(self) -> List[Dict[str, Any]]:
        """Load cluster profiles from disk. Returns empty list if file absent."""
        if not os.path.exists(_PROFILES_PATH):
            logger.warning("Cluster profiles file not found at %s.", _PROFILES_PATH)
            return []
        with open(_PROFILES_PATH, "r", encoding="utf-8") as fp:
            profiles = json.load(fp)
        logger.info("Loaded %d cluster profiles from disk.", len(profiles))
        return profiles
