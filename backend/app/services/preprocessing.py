"""
preprocessing.py - Full data preprocessing pipeline for customer segmentation.
"""
import json
import os
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder, StandardScaler

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SCALER_PATH = os.path.join(settings.MODELS_DIR, "scaler.pkl")
_ENCODERS_PATH = os.path.join(settings.MODELS_DIR, "label_encoders.pkl")
_METADATA_PATH = os.path.join(settings.MODELS_DIR, "feature_metadata.json")
_PROCESSED_CSV_PATH = os.path.join(settings.OUTPUTS_DIR, "processed_data.csv")
_CLUSTERED_CSV_PATH = os.path.join(settings.OUTPUTS_DIR, "clustered_data.csv")


class PreprocessingService:
    """
    End-to-end preprocessing pipeline:
        load -> validate -> impute -> deduplicate -> clip invalids
        -> encode categoricals -> select features -> scale
    """

    def __init__(self) -> None:
        self.scaler: Optional[StandardScaler] = None
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.numerical_imputer: Optional[SimpleImputer] = None
        self.categorical_imputer: Optional[SimpleImputer] = None
        self.feature_metadata: Dict[str, Any] = {}
        self.selected_features: List[str] = []
        self.fitted: bool = False
        self._raw_df: Optional[pd.DataFrame] = None   # unscaled, post-cleaning copy

    # -----------------------------------------------------------------------
    # Data loading
    # -----------------------------------------------------------------------

    def load_dataset(self, filepath: str) -> pd.DataFrame:
        """
        Read a CSV file into a DataFrame.

        Tries UTF-8 first; falls back to latin-1 on encoding errors.
        Strips leading/trailing whitespace from string column values.
        """
        logger.info("Loading dataset from '%s' ...", filepath)
        try:
            df = pd.read_csv(filepath, encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning("UTF-8 decode failed; retrying with latin-1.")
            df = pd.read_csv(filepath, encoding="latin-1")

        # Strip whitespace from all object (string) columns
        str_cols = df.select_dtypes(include="object").columns
        for col in str_cols:
            df[col] = df[col].str.strip()

        logger.info("Dataset loaded: %d rows, %d columns.", len(df), len(df.columns))
        return df

    # -----------------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------------

    def validate_dataset(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Basic sanity checks on the loaded DataFrame.

        Returns (is_valid, warnings).
        """
        warnings: List[str] = []

        if len(df) < 10:
            return False, [f"Dataset has only {len(df)} rows; minimum required is 10."]

        if len(df.columns) < 2:
            return False, ["Dataset must have at least 2 columns."]

        # Warn about entirely empty columns
        for col in df.columns:
            if df[col].isna().all():
                warnings.append(f"Column '{col}' is entirely empty and will be ignored.")

        # Warn about very high missing-value rates
        for col in df.columns:
            missing_pct = df[col].isna().mean() * 100
            if missing_pct > 50:
                warnings.append(
                    f"Column '{col}' has {missing_pct:.1f}% missing values."
                )

        return True, warnings

    # -----------------------------------------------------------------------
    # Dataset summary (for /api/dataset/summary)
    # -----------------------------------------------------------------------

    def get_dataset_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Return a comprehensive summary dict suitable for the DatasetSummary schema.
        """
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include="object").columns.tolist()

        missing_values: Dict[str, int] = {
            col: int(df[col].isna().sum())
            for col in df.columns
            if df[col].isna().sum() > 0
        }

        duplicate_records = int(df.duplicated().sum())

        feature_stats: Dict[str, Any] = {}
        for col in numerical_cols:
            series = df[col].dropna()
            feature_stats[col] = {
                "mean": round(float(series.mean()), 4) if len(series) > 0 else None,
                "median": round(float(series.median()), 4) if len(series) > 0 else None,
                "std": round(float(series.std()), 4) if len(series) > 0 else None,
                "min": round(float(series.min()), 4) if len(series) > 0 else None,
                "max": round(float(series.max()), 4) if len(series) > 0 else None,
                "missing": int(df[col].isna().sum()),
            }
        for col in categorical_cols:
            value_counts = df[col].value_counts().head(10).to_dict()
            feature_stats[col] = {
                "unique_values": int(df[col].nunique()),
                "top_values": {str(k): int(v) for k, v in value_counts.items()},
                "missing": int(df[col].isna().sum()),
            }

        column_info: Dict[str, Any] = {}
        for col in df.columns:
            column_info[col] = {
                "dtype": str(df[col].dtype),
                "missing": int(df[col].isna().sum()),
                "unique": int(df[col].nunique()),
            }

        # Distributions for all numerical columns (5-8 bins)
        num_distributions: Dict[str, List[Dict[str, Any]]] = {}
        for col in numerical_cols:
            series = df[col].dropna()
            if len(series) > 0 and series.nunique() > 1:
                try:
                    counts, bin_edges = np.histogram(series, bins=min(6, series.nunique()))
                    num_distributions[col] = [
                        {
                            "name": f"{float(bin_edges[i]):.1f} - {float(bin_edges[i+1]):.1f}",
                            "bin_start": round(float(bin_edges[i]), 1),
                            "bin_end": round(float(bin_edges[i+1]), 1),
                            "count": int(counts[i]),
                        }
                        for i in range(len(counts))
                    ]
                except Exception:
                    pass

        # Distributions for all categorical columns
        cat_distributions: Dict[str, List[Dict[str, Any]]] = {}
        for col in categorical_cols:
            top_vals = df[col].value_counts().head(8).to_dict()
            cat_distributions[col] = [
                {"name": str(k), "count": int(v)} for k, v in top_vals.items()
            ]

        sample_data = df.head(10).fillna("").to_dict(orient="records")

        # Specific legacy aliases for customer dataset
        gender_dist = (
            df["Gender"].value_counts().to_dict()
            if "Gender" in df.columns
            else None
        )
        age_dist = num_distributions.get("Age")
        income_dist = num_distributions.get("AnnualIncome")
        spending_dist = num_distributions.get("SpendingScore")

        return {
            "total_records": len(df),
            "total_features": len(df.columns),
            "missing_values": missing_values,
            "missing_values_total": int(sum(missing_values.values())),
            "duplicate_records": duplicate_records,
            "duplicate_count": duplicate_records,
            "numerical_features": numerical_cols,
            "categorical_features": categorical_cols,
            "feature_stats": feature_stats,
            "statistics": feature_stats,
            "column_info": column_info,
            "numerical_distributions": num_distributions,
            "categorical_distributions": cat_distributions,
            "gender_distribution": gender_dist,
            "age_distribution": age_dist,
            "income_distribution": income_dist,
            "spending_distribution": spending_dist,
            "sample_data": sample_data,
        }

    # -----------------------------------------------------------------------
    # Missing value handling
    # -----------------------------------------------------------------------

    def handle_missing_values(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        Impute missing values:
          - Numerical columns: median strategy
          - Categorical columns: most frequent (mode) strategy

        Returns (imputed_df, {col: count_imputed}).
        """
        imputed_counts: Dict[str, int] = {}
        df = df.copy()

        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include="object").columns.tolist()

        # Numerical imputation
        if numerical_cols:
            missing_before = df[numerical_cols].isna().sum()
            self.numerical_imputer = SimpleImputer(strategy="median")
            df[numerical_cols] = self.numerical_imputer.fit_transform(df[numerical_cols])
            missing_after = df[numerical_cols].isna().sum()
            for col in numerical_cols:
                count = int(missing_before[col] - missing_after[col])
                if count > 0:
                    imputed_counts[col] = count

        # Categorical imputation
        if categorical_cols:
            for col in categorical_cols:
                n_missing = int(df[col].isna().sum())
                if n_missing > 0:
                    mode_val = df[col].mode()
                    fill_val = mode_val.iloc[0] if len(mode_val) > 0 else "Unknown"
                    df[col].fillna(fill_val, inplace=True)
                    imputed_counts[col] = n_missing

        logger.info("Imputed missing values: %s", imputed_counts)
        return df, imputed_counts

    # -----------------------------------------------------------------------
    # Duplicate removal
    # -----------------------------------------------------------------------

    def remove_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """Remove exact duplicate rows. Returns (deduplicated_df, count_removed)."""
        original_len = len(df)
        df = df.drop_duplicates().reset_index(drop=True)
        removed = original_len - len(df)
        if removed > 0:
            logger.info("Removed %d duplicate rows.", removed)
        return df, removed

    # -----------------------------------------------------------------------
    # Invalid value clipping
    # -----------------------------------------------------------------------

    def handle_invalid_values(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Clip known columns to valid domains:
          - Age:              [0, 120]
          - AnnualIncome:     [0, ∞)
          - SpendingScore:    [0, 100]
          - PurchaseFrequency:[0, ∞)

        Returns (df, list_of_warning_messages).
        """
        df = df.copy()
        warnings: List[str] = []

        rules = {
            "Age": (0, 120),
            "SpendingScore": (0, 100),
            "AnnualIncome": (0, None),
            "PurchaseFrequency": (0, None),
        }

        for col, (low, high) in rules.items():
            if col not in df.columns:
                continue
            original = df[col].copy()
            df[col] = df[col].clip(lower=low, upper=high)
            n_clipped = int((original != df[col]).sum())
            if n_clipped > 0:
                bound_str = f"[{low}, {high}]" if high is not None else f">= {low}"
                msg = (
                    f"Clipped {n_clipped} invalid values in '{col}' to valid range {bound_str}."
                )
                warnings.append(msg)
                logger.warning(msg)

        return df, warnings

    # -----------------------------------------------------------------------
    # Categorical encoding
    # -----------------------------------------------------------------------

    def encode_categorical(
        self, df: pd.DataFrame, fit: bool = True
    ) -> pd.DataFrame:
        """
        Label-encode all object-dtype columns.

        When *fit=True*: fit new LabelEncoders and store them.
        When *fit=False*: use stored encoders (for prediction transforms).

        Unseen categories during transform are mapped to -1.
        """
        df = df.copy()
        categorical_cols = df.select_dtypes(include="object").columns.tolist()

        for col in categorical_cols:
            if fit:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
            else:
                if col not in self.label_encoders:
                    logger.warning(
                        "No encoder found for column '%s'; encoding as -1.", col
                    )
                    df[col] = -1
                    continue
                le = self.label_encoders[col]
                known_classes = set(le.classes_)
                df[col] = df[col].astype(str).apply(
                    lambda x: le.transform([x])[0] if x in known_classes else -1
                )

        return df

    # -----------------------------------------------------------------------
    # Feature selection
    # -----------------------------------------------------------------------

    def select_features(
        self, df: pd.DataFrame, features: List[str]
    ) -> pd.DataFrame:
        """
        Return a DataFrame containing only the *features* that exist in *df*.
        Logs a warning for any requested feature that is missing.
        """
        available = [f for f in features if f in df.columns]
        missing = [f for f in features if f not in df.columns]
        if missing:
            logger.warning("Requested features not found in dataset: %s", missing)

        self.selected_features = available
        return df[available].copy()

    # -----------------------------------------------------------------------
    # Scaling
    # -----------------------------------------------------------------------

    def scale_features(
        self, df: pd.DataFrame, fit: bool = True
    ) -> np.ndarray:
        """
        Standardise features using StandardScaler.

        When *fit=True*: fit and transform (training pipeline).
        When *fit=False*: transform only (prediction pipeline).
        """
        if fit:
            self.scaler = StandardScaler()
            scaled = self.scaler.fit_transform(df.values.astype(float))
        else:
            if self.scaler is None:
                raise RuntimeError(
                    "Scaler is not fitted. Call preprocess() or load_preprocessor() first."
                )
            scaled = self.scaler.transform(df.values.astype(float))

        return scaled

    # -----------------------------------------------------------------------
    # Full pipeline
    # -----------------------------------------------------------------------

    def preprocess(
        self,
        filepath: str,
        features: List[str],
        remove_duplicates: bool = True,
    ) -> Dict[str, Any]:
        """
        Run the complete preprocessing pipeline and return a result dict:
          success, message, original_records, processed_records,
          removed_duplicates, imputed_values, features_used, warnings, X_scaled
        """
        result: Dict[str, Any] = {
            "success": False,
            "message": "",
            "original_records": 0,
            "processed_records": 0,
            "removed_duplicates": 0,
            "imputed_values": {},
            "features_used": [],
            "warnings": [],
            "X_scaled": None,
        }

        try:
            # 1. Load
            df = self.load_dataset(filepath)
            result["original_records"] = len(df)

            # 2. Validate
            is_valid, val_warnings = self.validate_dataset(df)
            result["warnings"].extend(val_warnings)
            if not is_valid:
                result["message"] = "; ".join(val_warnings)
                return result

            # 3. Handle missing
            df, imputed = self.handle_missing_values(df)
            result["imputed_values"] = imputed

            # 4. Remove duplicates
            if remove_duplicates:
                df, n_removed = self.remove_duplicates(df)
                result["removed_duplicates"] = n_removed

            # 5. Handle invalid values
            df, clip_warnings = self.handle_invalid_values(df)
            result["warnings"].extend(clip_warnings)

            # 6. Encode categoricals (fit)
            df = self.encode_categorical(df, fit=True)

            # Keep a clean unscaled copy for profiling
            self._raw_df = df.copy()

            # 7. Select features
            df_features = self.select_features(df, features)
            result["features_used"] = self.selected_features

            if df_features.empty or len(self.selected_features) == 0:
                result["message"] = "No valid features found after preprocessing."
                return result

            # 8. Scale
            X_scaled = self.scale_features(df_features, fit=True)

            # 9. Save
            self.save_preprocessor()

            # Save processed CSV for download
            os.makedirs(settings.OUTPUTS_DIR, exist_ok=True)
            df.to_csv(_PROCESSED_CSV_PATH, index=False)

            self.fitted = True
            result["success"] = True
            result["processed_records"] = len(df)
            result["X_scaled"] = X_scaled
            result["message"] = (
                f"Preprocessing complete. {len(df)} records processed "
                f"using features: {self.selected_features}."
            )
            logger.info(result["message"])

        except Exception as exc:
            logger.exception("Preprocessing pipeline failed.")
            result["message"] = f"Preprocessing failed: {str(exc)}"

        return result

    # -----------------------------------------------------------------------
    # Single-record preprocessing (prediction)
    # -----------------------------------------------------------------------

    def _resolve_feature_value(self, feat_name: str, row: Dict[str, Any], col_idx: int) -> float:
        """Resolve a feature value by exact name, normalized name, or semantic match with unit conversion."""
        raw_val = None
        if feat_name in row and row[feat_name] is not None and str(row[feat_name]) != "":
            raw_val = row[feat_name]
        else:
            target_norm = feat_name.lower().replace(" ", "").replace("_", "").replace("-", "")
            for k, v in row.items():
                k_norm = k.lower().replace(" ", "").replace("_", "").replace("-", "")
                if k_norm == target_norm:
                    raw_val = v
                    break

            if raw_val is None:
                for k, v in row.items():
                    k_lower = k.lower()
                    t_lower = feat_name.lower()
                    if ("income" in t_lower and "income" in k_lower) or \
                       (("spending" in t_lower or "score" in t_lower) and ("spending" in k_lower or "score" in k_lower)) or \
                       ("age" in t_lower and "age" in k_lower) or \
                       (("freq" in t_lower or "purchas" in t_lower) and ("freq" in k_lower or "purchas" in k_lower)):
                        raw_val = v
                        break

        if raw_val is None:
            return 0.0

        try:
            val = float(raw_val)
        except (ValueError, TypeError):
            return 0.0

        # Check unit scale for income (k$ vs dollars)
        if "income" in feat_name.lower() and self.scaler is not None and hasattr(self.scaler, "mean_"):
            if col_idx < len(self.scaler.mean_):
                expected_mean = self.scaler.mean_[col_idx]
                if expected_mean < 1000 and val > 1000:
                    val = val / 1000.0
                elif expected_mean > 1000 and 0 < val < 1000:
                    val = val * 1000.0

        return val

    def preprocess_single(self, customer_data: Dict[str, Any]) -> np.ndarray:
        """
        Transform a single customer dict using the already-fitted scaler and encoders.

        Loads from disk if not currently in memory.

        Returns a (1, n_features) numpy array ready for predict().
        """
        if not self.fitted:
            self.load_preprocessor()

        row: Dict[str, Any] = dict(customer_data)

        # Encode categorical columns using stored encoders
        for col, le in self.label_encoders.items():
            if col in row:
                val = str(row[col])
                if val in set(le.classes_):
                    row[col] = int(le.transform([val])[0])
                else:
                    logger.warning(
                        "Unseen category '%s' for column '%s'; encoding as -1.", val, col
                    )
                    row[col] = -1

        # Build DataFrame with only the selected features (in correct order)
        feature_values: List[float] = []
        for i, feat in enumerate(self.selected_features):
            val = self._resolve_feature_value(feat, row, i)
            feature_values.append(val)

        df_single = pd.DataFrame([feature_values], columns=self.selected_features)
        X_scaled = self.scale_features(df_single, fit=False)
        return X_scaled

    # -----------------------------------------------------------------------
    # Persistence
    # -----------------------------------------------------------------------

    def save_preprocessor(self) -> None:
        """Save scaler, label encoders, and feature metadata to backend/models/."""
        os.makedirs(settings.MODELS_DIR, exist_ok=True)

        if self.scaler is not None:
            joblib.dump(self.scaler, _SCALER_PATH)

        if self.label_encoders:
            joblib.dump(self.label_encoders, _ENCODERS_PATH)

        metadata = {
            "selected_features": self.selected_features,
            "fitted": self.fitted,
        }
        with open(_METADATA_PATH, "w", encoding="utf-8") as fp:
            json.dump(metadata, fp, indent=2)

        logger.info("Preprocessor saved (scaler, encoders, metadata).")

    def load_preprocessor(self) -> None:
        """Load scaler, label encoders, and metadata from backend/models/."""
        missing: List[str] = []
        for path, label in [
            (_SCALER_PATH, "scaler"),
            (_ENCODERS_PATH, "label encoders"),
            (_METADATA_PATH, "metadata"),
        ]:
            if not os.path.exists(path):
                missing.append(label)

        if missing:
            raise FileNotFoundError(
                f"Preprocessor files not found: {missing}. "
                "Please run the preprocessing pipeline first."
            )

        self.scaler = joblib.load(_SCALER_PATH)
        self.label_encoders = joblib.load(_ENCODERS_PATH)

        with open(_METADATA_PATH, "r", encoding="utf-8") as fp:
            metadata = json.load(fp)

        self.selected_features = metadata.get("selected_features", [])
        self.fitted = metadata.get("fitted", True)

        logger.info(
            "Preprocessor loaded. Features: %s", self.selected_features
        )

    def save_clustered_csv(
        self, labels: np.ndarray, algorithm: str = "kmeans"
    ) -> str:
        """
        Attach cluster labels to the raw (post-cleaning) DataFrame and save as CSV.

        Returns the output path.
        """
        if self._raw_df is None:
            raise RuntimeError("No preprocessed data in memory. Run preprocess() first.")

        df_out = self._raw_df.copy()
        df_out["Cluster"] = labels
        df_out["Algorithm"] = algorithm
        df_out.to_csv(_CLUSTERED_CSV_PATH, index=False)
        logger.info("Clustered CSV saved to %s.", _CLUSTERED_CSV_PATH)
        return _CLUSTERED_CSV_PATH
