"""
routes_dataset.py - Dataset upload, summary, sample and download endpoints.
"""
import os
import shutil
from typing import Any, Dict

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas import DatasetSummary
from app.services.preprocessing import PreprocessingService
from app.utils.logger import get_logger
from app.utils.validators import validate_csv_file

logger = get_logger(__name__)
router = APIRouter(prefix="/api/dataset", tags=["Dataset"])

# Module-level singleton and state ─────────────────────────────────────────
_preprocessing_service = PreprocessingService()

# Paths used for downloads
_PROCESSED_CSV = os.path.join(settings.OUTPUTS_DIR, "processed_data.csv")
_CLUSTERED_CSV = os.path.join(settings.OUTPUTS_DIR, "clustered_data.csv")
_UPLOAD_FILEPATH: Dict[str, str] = {}   # {"path": "<filepath>"}
_CACHED_SUMMARY: Dict[str, Any] = {}


# ───────────────────────────────────────────────────────────────────────────
# POST /api/dataset/upload
# ───────────────────────────────────────────────────────────────────────────

@router.post("/upload", summary="Upload a CSV dataset")
async def upload_dataset(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Accept a CSV file, save it to the uploads directory, and return a
    dataset summary (row/column counts, missing values, sample rows, etc.).
    """
    # Validate
    is_valid, error_msg = validate_csv_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Save to uploads/
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_filename = os.path.basename(file.filename or "upload.csv")
    dest_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    try:
        with open(dest_path, "wb") as out_file:
            shutil.copyfileobj(file.file, out_file)
    except Exception as exc:
        logger.exception("Failed to save uploaded file.")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {exc}")

    _UPLOAD_FILEPATH["path"] = dest_path
    logger.info("File uploaded and saved to '%s'.", dest_path)

    # Generate summary
    try:
        df = _preprocessing_service.load_dataset(dest_path)
        summary = _preprocessing_service.get_dataset_summary(df)
        _CACHED_SUMMARY.update(summary)
    except Exception as exc:
        logger.exception("Failed to generate dataset summary.")
        raise HTTPException(
            status_code=422,
            detail=f"File saved but summary generation failed: {exc}",
        )

    # Persist dataset and customer records to database (SQL & MongoDB)
    try:
        from app.services.db_service import db_service
        db_id = db_service.save_dataset(safe_filename, dest_path, df, summary)
        logger.info("Dataset persisted to DB with ID: %s", db_id)

        from app.services.mongo_service import mongo_service
        if mongo_service.connected:
            mongo_service.save_dataset(
                filename=safe_filename,
                filepath=dest_path,
                total_records=len(df),
                total_features=len(df.columns),
                features=df.columns.tolist(),
                summary=summary,
            )
            customers_batch = []
            id_col = next((c for c in df.columns if c.lower() in ["customerid", "customer_id", "id", "station_id"]), None)
            for idx, row in df.head(500).iterrows():
                row_dict = row.to_dict()
                customers_batch.append({
                    "customer_ref": str(row_dict.get(id_col, f"REC_{idx}")),
                    "age": float(row_dict.get("Age")) if "Age" in row_dict and pd.notna(row_dict.get("Age")) else None,
                    "gender": str(row_dict.get("Gender")) if "Gender" in row_dict and pd.notna(row_dict.get("Gender")) else None,
                    "annual_income": float(row_dict.get("AnnualIncome")) if "AnnualIncome" in row_dict and pd.notna(row_dict.get("AnnualIncome")) else None,
                    "spending_score": float(row_dict.get("SpendingScore")) if "SpendingScore" in row_dict and pd.notna(row_dict.get("SpendingScore")) else None,
                    "purchase_frequency": float(row_dict.get("PurchaseFrequency")) if "PurchaseFrequency" in row_dict and pd.notna(row_dict.get("PurchaseFrequency")) else None,
                })
            mongo_service.save_customer_batch(customers_batch)
    except Exception as exc:
        logger.warning("Could not persist dataset to database: %s", exc)

    return {
        "success": True,
        "message": f"File '{safe_filename}' uploaded and saved to database successfully.",
        "filename": safe_filename,
        "filepath": dest_path,
        **summary,
    }


# ───────────────────────────────────────────────────────────────────────────
# GET /api/dataset/summary
# ───────────────────────────────────────────────────────────────────────────

@router.get("/summary", response_model=DatasetSummary, summary="Get dataset summary")
async def get_summary() -> DatasetSummary:
    """
    Return the cached summary of the last uploaded dataset.
    Raises 404 if no dataset has been uploaded yet.
    """
    if not _CACHED_SUMMARY:
        raise HTTPException(
            status_code=404,
            detail="No dataset summary found. Please upload a dataset first.",
        )
    return DatasetSummary(**_CACHED_SUMMARY)


# ───────────────────────────────────────────────────────────────────────────
# GET /api/dataset/sample
# ───────────────────────────────────────────────────────────────────────────

@router.get("/sample", summary="Get first 10 rows of the dataset")
async def get_sample() -> Dict[str, Any]:
    """
    Return the first 10 rows of the last uploaded dataset.
    Raises 404 if no dataset has been uploaded yet.
    """
    filepath = _UPLOAD_FILEPATH.get("path")
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail="No dataset found. Please upload a dataset first.",
        )

    try:
        df = _preprocessing_service.load_dataset(filepath)
        sample = df.head(10).fillna("").to_dict(orient="records")
        columns = df.columns.tolist()
    except Exception as exc:
        logger.exception("Failed to read sample data.")
        raise HTTPException(status_code=500, detail=f"Failed to read sample: {exc}")

    return {
        "columns": columns,
        "rows": sample,
        "total_records": len(df),
    }


# ───────────────────────────────────────────────────────────────────────────
# GET /api/dataset/download/processed
# ───────────────────────────────────────────────────────────────────────────

@router.get("/download/processed", summary="Download preprocessed CSV")
async def download_processed_csv() -> FileResponse:
    """
    Download the preprocessed CSV generated by the preprocessing pipeline.
    """
    if not os.path.exists(_PROCESSED_CSV):
        raise HTTPException(
            status_code=404,
            detail="Preprocessed file not found. Please run preprocessing first.",
        )
    return FileResponse(
        path=_PROCESSED_CSV,
        media_type="text/csv",
        filename="processed_data.csv",
    )


# ───────────────────────────────────────────────────────────────────────────
# GET /api/dataset/download/clustered
# ───────────────────────────────────────────────────────────────────────────

@router.get("/download/clustered", summary="Download clustered CSV")
async def download_clustered_csv() -> FileResponse:
    """
    Download the CSV that includes cluster label assignments.
    """
    if not os.path.exists(_CLUSTERED_CSV):
        raise HTTPException(
            status_code=404,
            detail="Clustered file not found. Please run clustering first.",
        )
    return FileResponse(
        path=_CLUSTERED_CSV,
        media_type="text/csv",
        filename="clustered_data.csv",
    )
