"""
validators.py - Input validation helpers for the Customer Segmentation API.
"""
import os
from typing import Dict, List, Tuple, Any

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# File validators
# ---------------------------------------------------------------------------

def validate_csv_file(file) -> Tuple[bool, str]:
    """
    Validate an uploaded file object (FastAPI UploadFile compatible).

    Checks:
      - File extension must be in ALLOWED_EXTENSIONS (.csv)
      - File size must be < MAX_FILE_SIZE (50 MB)

    Returns:
        (is_valid: bool, error_message: str)
        error_message is empty string when valid.
    """
    if file is None:
        return False, "No file provided."

    filename: str = file.filename or ""
    _, ext = os.path.splitext(filename.lower())

    if ext not in settings.ALLOWED_EXTENSIONS:
        return (
            False,
            f"Invalid file extension '{ext}'. Only {settings.ALLOWED_EXTENSIONS} files are allowed.",
        )

    # FastAPI stores the file in a SpooledTemporaryFile; seek to end to get size.
    try:
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset pointer
    except Exception:
        # If we cannot determine size, allow and rely on downstream processing
        logger.warning("Could not determine file size for '%s'.", filename)
        return True, ""

    if file_size > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        return (
            False,
            f"File size {actual_mb:.1f} MB exceeds the maximum allowed size of {max_mb:.0f} MB.",
        )

    return True, ""


# ---------------------------------------------------------------------------
# Customer input validators
# ---------------------------------------------------------------------------

def validate_customer_input(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate and clean a customer data dictionary.

    Expected keys (all optional but warned when missing):
        Age, AnnualIncome, SpendingScore, PurchaseFrequency, Gender

    Returns:
        (cleaned_data: dict, errors: list[str])
        errors is an empty list when all values are valid.
    """
    cleaned: Dict[str, Any] = {}
    errors: List[str] = []

    # ── Age ─────────────────────────────────────────────────────────────────
    if "Age" in data:
        try:
            age = float(data["Age"])
            if age < 0 or age > 120:
                errors.append(f"Age must be between 0 and 120, got {age}.")
            else:
                cleaned["Age"] = age
        except (TypeError, ValueError):
            errors.append(f"Age must be a numeric value, got '{data['Age']}'.")
    else:
        errors.append("Age is required.")

    # ── AnnualIncome ────────────────────────────────────────────────────────
    if "AnnualIncome" in data:
        try:
            income = float(data["AnnualIncome"])
            if income < 0:
                errors.append(f"AnnualIncome must be >= 0, got {income}.")
            else:
                cleaned["AnnualIncome"] = income
        except (TypeError, ValueError):
            errors.append(f"AnnualIncome must be a numeric value, got '{data['AnnualIncome']}'.")
    else:
        errors.append("AnnualIncome is required.")

    # ── SpendingScore ───────────────────────────────────────────────────────
    if "SpendingScore" in data:
        try:
            score = float(data["SpendingScore"])
            if score < 0 or score > 100:
                errors.append(f"SpendingScore must be between 0 and 100, got {score}.")
            else:
                cleaned["SpendingScore"] = score
        except (TypeError, ValueError):
            errors.append(
                f"SpendingScore must be a numeric value, got '{data['SpendingScore']}'."
            )
    else:
        errors.append("SpendingScore is required.")

    # ── PurchaseFrequency ───────────────────────────────────────────────────
    if "PurchaseFrequency" in data:
        try:
            freq = float(data["PurchaseFrequency"])
            if freq < 0:
                errors.append(f"PurchaseFrequency must be >= 0, got {freq}.")
            else:
                cleaned["PurchaseFrequency"] = freq
        except (TypeError, ValueError):
            errors.append(
                f"PurchaseFrequency must be a numeric value, got '{data['PurchaseFrequency']}'."
            )
    else:
        errors.append("PurchaseFrequency is required.")

    # ── Gender ──────────────────────────────────────────────────────────────
    valid_genders = {"Male", "Female", "Other"}
    if "Gender" in data:
        gender_raw = str(data["Gender"]).strip().capitalize()
        if gender_raw not in valid_genders:
            errors.append(
                f"Gender must be one of {list(valid_genders)}, got '{data['Gender']}'."
            )
        else:
            cleaned["Gender"] = gender_raw
    else:
        # Gender is optional; default to 'Other'
        cleaned["Gender"] = "Other"

    return cleaned, errors


# ---------------------------------------------------------------------------
# Feature validators
# ---------------------------------------------------------------------------

def validate_features(features: List[str], available_columns: List[str]) -> List[str]:
    """
    Return the subset of *features* that exist in *available_columns*.

    Logs a warning for each requested feature not found in the dataset.
    Raises ValueError if the resulting valid feature list is empty.
    """
    available_set = set(available_columns)
    valid: List[str] = []
    for feat in features:
        if feat in available_set:
            valid.append(feat)
        else:
            logger.warning(
                "Requested feature '%s' not found in dataset columns. It will be skipped.", feat
            )

    if not valid:
        raise ValueError(
            f"None of the requested features {features} are present in the dataset columns "
            f"{available_columns}."
        )

    return valid


# ---------------------------------------------------------------------------
# Cluster count validator
# ---------------------------------------------------------------------------

def validate_k(k: int, n_samples: int) -> bool:
    """
    Return True when k is a valid cluster count for a dataset with *n_samples* rows.

    Rules:
      - k must be an integer >= 2
      - k must be strictly less than n_samples (need at least one sample per cluster)
    """
    if not isinstance(k, int) or k < 2:
        logger.warning("Invalid k=%s: must be an integer >= 2.", k)
        return False

    if k >= n_samples:
        logger.warning(
            "Invalid k=%s: must be less than the number of samples (%s).", k, n_samples
        )
        return False

    return True
