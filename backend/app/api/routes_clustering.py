"""
routes_clustering.py - Preprocessing, elbow/silhouette analysis, training,
comparison, segments, PCA and report-download endpoints.
"""
import io
import json
import os
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import CLUSTER_PROFILES_PATH, OUTPUT_DIR, settings
from app.schemas import (
    ClusteringAnalysisRequest,
    ClusteringTrainRequest,
    PreprocessRequest,
)
from app.services.clustering import ClusteringService
from app.services.evaluation import (
    compare_models,
    find_optimal_k_elbow,
    find_optimal_k_silhouette,
)
from app.services.preprocessing import PreprocessingService
from app.services.segmentation import SegmentationService
from app.utils.logger import get_logger

router = APIRouter(tags=["Clustering"])
logger = get_logger(__name__)

# ─── Module-level singletons ──────────────────────────────────────────────────
_preprocessing_service = PreprocessingService()
_clustering_service = ClusteringService()
_segmentation_service = SegmentationService()

# Session state shared across endpoints in this module
_session: Dict[str, Any] = {
    "X_scaled": None,
    "cleaned_df": None,
    "preprocess_report": None,
    "all_results": [],
    "last_labels": None,
    "last_algorithm": None,
    "pca_data": None,
}


def _get_upload_path() -> str:
    """Return the path to the most recently uploaded CSV file."""
    upload_dir = settings.UPLOAD_DIR
    if not os.path.isdir(upload_dir):
        raise HTTPException(status_code=404, detail="No dataset uploaded yet.")
    csvs = [
        f for f in os.listdir(upload_dir)
        if f.endswith(".csv") and not f.startswith(".")
    ]
    if not csvs:
        raise HTTPException(status_code=404, detail="No dataset uploaded yet.")
    # Sort by modification time (most recent first)
    csvs.sort(
        key=lambda f: os.path.getmtime(os.path.join(upload_dir, f)),
        reverse=True,
    )
    return os.path.join(upload_dir, csvs[0])


def _ensure_preprocessed() -> None:
    """
    Ensure dataset is preprocessed in _session. If not, auto-preprocesses
    the uploaded CSV or falls back to sample_customer_data.csv.
    """
    if _session["X_scaled"] is not None and _session["cleaned_df"] is not None:
        return

    filepath = None
    try:
        filepath = _get_upload_path()
    except Exception:
        # Check if sample customer data exists in data/sample_customer_data.csv
        sample_path = os.path.join(os.path.dirname(settings.UPLOAD_DIR), "data", "sample_customer_data.csv")
        if os.path.exists(sample_path):
            filepath = sample_path

    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=400, detail="No dataset uploaded yet. Please upload a CSV first.")

    try:
        df = _preprocessing_service.load_dataset(filepath)
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        features = [c for c in num_cols if not c.lower().endswith("id")]
        if len(features) < 2:
            features = [c for c in settings.DEFAULT_FEATURES if c in df.columns]
        if len(features) < 2:
            features = num_cols

        result = _preprocessing_service.preprocess(
            filepath=filepath,
            features=features,
            remove_duplicates=True,
        )
        if not result.get("success"):
            raise HTTPException(status_code=422, detail=result.get("message", "Preprocessing failed"))

        _session["X_scaled"] = result["X_scaled"]
        _session["cleaned_df"] = _preprocessing_service._raw_df
        _session["preprocess_report"] = result
        logger.info("Auto-preprocessed dataset '%s' with %d features", filepath, len(features))
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Auto-preprocessing failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Auto-preprocessing failed: {exc}")


# ─── POST /api/preprocess ─────────────────────────────────────────────────────

@router.post("/api/preprocess", summary="Preprocess the uploaded dataset")
def preprocess_dataset(req: PreprocessRequest):
    """
    Run the full preprocessing pipeline on the most recently uploaded CSV.
    Cleans, encodes, scales, and stores the result for downstream clustering.
    """
    filepath = _get_upload_path()

    result = _preprocessing_service.preprocess(
        filepath=filepath,
        features=req.features,
        remove_duplicates=req.remove_duplicates,
    )

    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["message"])

    _session["X_scaled"] = result["X_scaled"]
    _session["cleaned_df"] = _preprocessing_service._raw_df
    _session["preprocess_report"] = result

    logger.info("Preprocessing complete. X_scaled shape: %s", result["X_scaled"].shape)

    return {
        "success": True,
        "message": result["message"],
        "original_records": result["original_records"],
        "processed_records": result["processed_records"],
        "removed_duplicates": result["removed_duplicates"],
        "imputed_values": result["imputed_values"],
        "features_used": result["features_used"],
        "warnings": result["warnings"],
        "available_features": _preprocessing_service.selected_features,
    }


# ─── POST /api/clustering/analyze ─────────────────────────────────────────────

@router.post("/api/clustering/analyze", summary="Elbow + Silhouette analysis")
def analyze_elbow(req: ClusteringAnalysisRequest):
    """
    Compute WCSS (elbow) and silhouette scores over the requested K range.
    Returns optimal K recommendations from both methods.
    """
    _ensure_preprocessed()

    X = _session["X_scaled"]
    n_samples = len(X)

    if req.k_range:
        k_values = req.k_range
    else:
        k_min = getattr(req, "k_min", 2) or 2
        k_max = getattr(req, "k_max", 10) or 10
        k_values = list(range(k_min, k_max + 1))

    k_range = [k for k in k_values if 2 <= k < n_samples]
    if not k_range:
        raise HTTPException(
            status_code=400,
            detail=f"No valid K values in range {k_values}. Dataset has {n_samples} samples.",
        )

    try:
        result = _clustering_service.analyze_optimal_k(X, k_range)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Elbow analysis error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Elbow analysis failed: {exc}")

    return result


# ─── POST /api/clustering/train ───────────────────────────────────────────────

@router.post("/api/clustering/train", summary="Train a clustering model")
def train_model(req: ClusteringTrainRequest):
    """
    Train K-Means, Hierarchical, or DBSCAN on the preprocessed dataset.
    Saves the trained model, generates PCA coordinates and segment profiles.
    """
    _ensure_preprocessed()

    X = _session["X_scaled"]
    cleaned_df = _session["cleaned_df"]
    algorithm = req.algorithm.lower()
    k = req.n_clusters if getattr(req, "n_clusters", None) is not None else (req.k or 3)

    try:
        if algorithm == "kmeans":
            result = _clustering_service.train_kmeans(X, k)
        elif algorithm == "hierarchical":
            result = _clustering_service.train_hierarchical(X, k, req.linkage)
        elif algorithm == "dbscan":
            result = _clustering_service.train_dbscan(X, req.eps, req.min_samples)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown algorithm '{req.algorithm}'. Supported: kmeans, hierarchical, dbscan.",
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Training error (%s): %s", algorithm, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Training failed: {exc}")

    labels = np.array(result["labels"])

    # PCA visualisation data
    try:
        pca_data = _clustering_service.get_pca_coordinates(X, labels)
    except Exception as exc:
        logger.warning("PCA computation failed: %s", exc)
        pca_data = []

    _session["last_labels"] = labels
    _session["last_algorithm"] = algorithm
    _session["pca_data"] = pca_data

    # Segment profiles
    profiles = []
    if cleaned_df is not None and len(labels) == len(cleaned_df):
        try:
            profiles = _segmentation_service.generate_cluster_profiles(
                cleaned_df, labels, _preprocessing_service.selected_features
            )
            _segmentation_service.save_profiles(profiles)
            # Append clustered CSV
            _preprocessing_service.save_clustered_csv(labels, algorithm)
        except Exception as exc:
            logger.warning("Profile generation failed: %s", exc)

    # Cluster distribution
    unique, counts = np.unique(labels, return_counts=True)
    distribution = {str(int(u)): int(c) for u, c in zip(unique, counts)}

    # Update session results list (one entry per algorithm)
    _session["all_results"] = [
        r for r in _session["all_results"] if r["algorithm"] != result["algorithm"]
    ]
    # Store a JSON-serialisable copy (skip labels and centers - numpy arrays)
    session_result = {
        "algorithm": result.get("algorithm"),
        "n_clusters": result.get("n_clusters"),
        "silhouette_score": result.get("silhouette_score"),
        "davies_bouldin_score": result.get("davies_bouldin_score"),
        "wcss": result.get("wcss"),
        "noise_points": result.get("noise_points"),
    }
    _session["all_results"].append(session_result)

    # Persist clustering run and profiles to database (SQL & MongoDB)
    try:
        from app.services.db_service import db_service
        hyperparams = {"k": req.k, "eps": req.eps, "min_samples": req.min_samples, "linkage": req.linkage}
        run_id = db_service.save_clustering_run(
            algorithm=result["algorithm"],
            n_clusters=result["n_clusters"],
            metrics=session_result,
            profiles=profiles,
            hyperparameters=hyperparams,
        )
        logger.info("Clustering run saved to database with ID: %s", run_id)

        from app.services.mongo_service import mongo_service
        if mongo_service.connected:
            mongo_service.save_clustering_run(
                algorithm=result["algorithm"],
                n_clusters=result["n_clusters"],
                metrics=session_result,
                profiles=profiles,
                hyperparameters=hyperparams,
            )
    except Exception as exc:
        logger.warning("Could not persist clustering run to database: %s", exc)


    return {
        "success": True,
        "message": f"{result['algorithm'].upper()} training complete.",
        "algorithm": result["algorithm"],
        "metrics": {
            "algorithm": result["algorithm"],
            "n_clusters": result["n_clusters"],
            "silhouette_score": result.get("silhouette_score"),
            "davies_bouldin_score": result.get("davies_bouldin_score"),
            "wcss": result.get("wcss"),
            "noise_points": result.get("noise_points"),
        },
        "profiles": profiles,
        "pca_data": pca_data,
        "cluster_distribution": distribution,
    }


# ─── POST /api/clustering/train-all ───────────────────────────────────────────

@router.post("/api/clustering/train-all", summary="Train all algorithms at once")
def train_all_models():
    """
    Train K-Means, Hierarchical, and DBSCAN on the preprocessed dataset.
    Populates the comparison table immediately.
    """
    _ensure_preprocessed()
    X = _session["X_scaled"]
    cleaned_df = _session["cleaned_df"]

    # 1. K-Means
    km_res = _clustering_service.train_kmeans(X, k=3)
    # 2. Hierarchical
    hc_res = _clustering_service.train_hierarchical(X, k=3, linkage="ward")
    # 3. DBSCAN
    db_res = _clustering_service.train_dbscan(X, eps=0.5, min_samples=5)

    trained = [km_res, hc_res, db_res]
    _session["all_results"] = []
    for res in trained:
        session_result = {
            "algorithm": res.get("algorithm"),
            "n_clusters": res.get("n_clusters"),
            "silhouette_score": res.get("silhouette_score"),
            "davies_bouldin_score": res.get("davies_bouldin_score"),
            "wcss": res.get("wcss"),
            "noise_points": res.get("noise_points"),
        }
        _session["all_results"].append(session_result)

    # Use K-Means as default active model for PCA and segments
    labels = np.array(km_res["labels"])
    _session["last_labels"] = labels
    _session["last_algorithm"] = "kmeans"
    try:
        _session["pca_data"] = _clustering_service.get_pca_coordinates(X, labels)
    except Exception:
        _session["pca_data"] = []

    profiles = []
    if cleaned_df is not None and len(labels) == len(cleaned_df):
        try:
            profiles = _segmentation_service.generate_cluster_profiles(
                cleaned_df, labels, _preprocessing_service.selected_features
            )
            _segmentation_service.save_profiles(profiles)
            _preprocessing_service.save_clustered_csv(labels, "kmeans")
        except Exception as exc:
            logger.warning("Profile generation failed in train_all: %s", exc)

    # Persist to database if connected
    try:
        from app.services.db_service import db_service
        for res in trained:
            s_res = {
                "algorithm": res.get("algorithm"),
                "n_clusters": res.get("n_clusters"),
                "silhouette_score": res.get("silhouette_score"),
                "davies_bouldin_score": res.get("davies_bouldin_score"),
                "wcss": res.get("wcss"),
                "noise_points": res.get("noise_points"),
            }
            db_service.save_clustering_run(
                algorithm=res["algorithm"],
                n_clusters=res["n_clusters"],
                metrics=s_res,
                profiles=profiles if res["algorithm"] == "kmeans" else [],
                hyperparameters={"k": 3} if res["algorithm"] != "dbscan" else {"eps": 0.5, "min_samples": 5},
            )
    except Exception as exc:
        logger.warning("Could not persist train_all runs: %s", exc)

    safe_results = list(_session["all_results"])
    table = compare_models(safe_results)
    return {
        "success": True,
        "message": "All 3 algorithms (K-Means, Hierarchical, DBSCAN) trained successfully.",
        "results": table,
        "models": table,
    }


# ─── GET /api/clustering/results ──────────────────────────────────────────────

@router.get("/api/clustering/results", summary="Get all trained model results")
def get_results():
    """Return metrics for all algorithms trained in the current session."""
    results = _session.get("all_results", [])
    if not results:
        # Try to auto-train if dataset available
        try:
            _ensure_preprocessed()
            train_all_models()
            results = _session.get("all_results", [])
        except Exception:
            pass

    return {
        "results": [
            {
                "algorithm": r.get("algorithm", "unknown"),
                "n_clusters": r.get("n_clusters", 0),
                "silhouette_score": r.get("silhouette_score"),
                "davies_bouldin_score": r.get("davies_bouldin_score"),
                "wcss": r.get("wcss"),
                "noise_points": r.get("noise_points"),
            }
            for r in results
        ]
    }


# ─── GET /api/clustering/comparison ───────────────────────────────────────────

@router.get("/api/clustering/comparison", summary="Get model comparison table")
def get_comparison():
    """
    Return a ranked comparison of all trained models.
    Includes metric interpretation guidance.
    """
    results = _session.get("all_results", [])
    if not results:
        # Attempt auto-training all models if data is available
        try:
            _ensure_preprocessed()
            train_all_models()
            results = _session.get("all_results", [])
        except Exception as exc:
            logger.info("Auto-train on get_comparison skipped: %s", exc)

    if not results:
        return {
            "results": [],
            "models": [],
            "interpretation": {
                "silhouette_score": "Higher is better (range -1 to 1). Values above 0.5 indicate well-separated clusters.",
                "davies_bouldin_score": "Lower is better (range >= 0). Values close to 0 indicate tight, well-separated clusters.",
                "wcss": "Lower is better, but interpret with the number of clusters. Use with the elbow chart.",
                "noise_points": "DBSCAN only. Points not assigned to any cluster.",
            },
        }

    # Strip non-serializable fields before comparison
    safe_results = []
    for r in results:
        safe_results.append({
            "algorithm": r.get("algorithm", "unknown"),
            "n_clusters": r.get("n_clusters", 0),
            "silhouette_score": r.get("silhouette_score"),
            "davies_bouldin_score": r.get("davies_bouldin_score"),
            "wcss": r.get("wcss"),
            "noise_points": r.get("noise_points"),
        })

    table = compare_models(safe_results)
    return {
        "results": table,
        "models": table,
        "interpretation": {
            "silhouette_score": (
                "Higher is better (range -1 to 1). Values above 0.5 indicate "
                "well-separated clusters."
            ),
            "davies_bouldin_score": (
                "Lower is better (range >= 0). Values close to 0 indicate tight, "
                "well-separated clusters."
            ),
            "wcss": (
                "Lower is better, but interpret with the number of clusters. "
                "Use with the elbow chart."
            ),
            "noise_points": "DBSCAN only. Points not assigned to any cluster.",
        },
    }


# ─── GET /api/segments ────────────────────────────────────────────────────────

@router.get("/api/segments", summary="Get cluster segment profiles")
def get_segments():
    """Return saved cluster profiles. Auto-trains if not yet available."""
    profiles = _segmentation_service.load_profiles()
    if not profiles:
        # Try to rebuild from in-session data
        if _session.get("cleaned_df") is not None and _session.get("last_labels") is not None:
            try:
                profiles = _segmentation_service.generate_cluster_profiles(
                    _session["cleaned_df"],
                    _session["last_labels"],
                    _preprocessing_service.selected_features,
                )
                _segmentation_service.save_profiles(profiles)
            except Exception as exc:
                logger.warning("Could not regenerate profiles: %s", exc)

    if not profiles:
        # Auto-train models if dataset is available
        try:
            _ensure_preprocessed()
            train_all_models()
            profiles = _segmentation_service.load_profiles()
        except Exception as exc:
            logger.info("Auto-generate profiles skipped: %s", exc)

    if not profiles:
        return {"profiles": [], "segments": []}

    return {"profiles": profiles, "segments": profiles}


# ─── GET /api/clustering/pca ──────────────────────────────────────────────────

@router.get("/api/clustering/pca", summary="Get PCA 2D visualisation data")
def get_pca():
    """Return PCA-reduced 2D coordinates for the last trained model."""
    pca_data = _session.get("pca_data")
    if not pca_data:
        if _session.get("X_scaled") is not None and _session.get("last_labels") is not None:
            try:
                pca_data = _clustering_service.get_pca_coordinates(
                    _session["X_scaled"], _session["last_labels"]
                )
                _session["pca_data"] = pca_data
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"PCA failed: {exc}")
        else:
            raise HTTPException(
                status_code=404,
                detail="No PCA data available. Train a model first.",
            )
    return {"pca_data": pca_data, "algorithm": _session.get("last_algorithm", "unknown")}


# ─── GET /api/clustering/download/report ──────────────────────────────────────

@router.get("/api/clustering/download/report", summary="Download CSV comparison report")
def download_report():
    """Download a CSV report of all trained model metrics."""
    results = _session.get("all_results", [])
    profiles = _segmentation_service.load_profiles()

    rows = []
    for r in results:
        rows.append({
            "Algorithm": r.get("algorithm", ""),
            "N_Clusters": r.get("n_clusters", ""),
            "Silhouette_Score": r.get("silhouette_score", ""),
            "Davies_Bouldin_Score": r.get("davies_bouldin_score", ""),
            "WCSS": r.get("wcss", ""),
            "Noise_Points": r.get("noise_points", ""),
        })

    df = pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["Algorithm", "N_Clusters", "Silhouette_Score",
                 "Davies_Bouldin_Score", "WCSS", "Noise_Points"]
    )

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=model_comparison_report.csv"},
    )
