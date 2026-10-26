"""
routes_prediction.py - Single-customer cluster prediction endpoint.
"""
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.schemas import PredictionRequest, PredictionResponse
from app.services.clustering import ClusteringService
from app.services.preprocessing import PreprocessingService
from app.services.segmentation import SegmentationService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/prediction", tags=["Prediction"])

# ── Singletons ───────────────────────────────────────────────────────────────
_prep_service = PreprocessingService()
_cluster_service = ClusteringService()
_seg_service = SegmentationService()

# Default algorithm priority for prediction
_ALGORITHM_PRIORITY = ["kmeans", "hierarchical", "dbscan"]


# ───────────────────────────────────────────────────────────────────────────
# POST /api/prediction/predict
# ───────────────────────────────────────────────────────────────────────────

@router.post("/predict", response_model=PredictionResponse, summary="Predict customer segment")
async def predict_customer_segment(request: PredictionRequest) -> PredictionResponse:
    """
    Given a single customer's features, predict which cluster/segment they
    belong to using the last trained model.

    Steps:
      1. Load preprocessor (scaler + encoders) from disk.
      2. Transform the customer dict into a scaled feature vector.
      3. Load the best available trained model.
      4. Predict the cluster label.
      5. Fetch the matching cluster profile.
      6. Return segment info.
    """

    # ── 1. Load preprocessor ─────────────────────────────────────────────────
    try:
        _prep_service.load_preprocessor()
    except FileNotFoundError:
        # Attempt auto-training
        try:
            from app.api.routes_clustering import _ensure_preprocessed, train_all_models
            _ensure_preprocessed()
            train_all_models()
            _prep_service.load_preprocessor()
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Preprocessor not found. Please upload a dataset and train a model first: {exc}",
            )
    except Exception as exc:
        logger.exception("Failed to load preprocessor.")
        raise HTTPException(status_code=500, detail=f"Failed to load preprocessor: {exc}")

    # ── 2. Build customer dict using field names that match feature names ─────
    customer_dict: Dict[str, Any] = {
        "Age": request.age,
        "age": request.age,
        "AnnualIncome": request.annual_income,
        "Annual Income": request.annual_income,
        "Annual Income (k$)": request.annual_income,
        "annual_income": request.annual_income,
        "Income": request.annual_income,
        "income": request.annual_income,
        "SpendingScore": request.spending_score,
        "Spending Score": request.spending_score,
        "Spending Score (1-100)": request.spending_score,
        "spending_score": request.spending_score,
        "PurchaseFrequency": request.purchase_frequency,
        "Purchase Frequency": request.purchase_frequency,
        "purchase_frequency": request.purchase_frequency,
        "Gender": request.gender,
        "gender": request.gender,
    }

    # ── 3. Transform ─────────────────────────────────────────────────────────
    try:
        X_single = _prep_service.preprocess_single(customer_dict)
    except Exception as exc:
        logger.exception("Failed to preprocess customer input.")
        raise HTTPException(
            status_code=422,
            detail=f"Failed to preprocess customer data: {exc}",
        )

    # ── 4. Load model and predict ─────────────────────────────────────────────
    model = None
    used_algorithm = ""
    for algo in _ALGORITHM_PRIORITY:
        try:
            model = _cluster_service.load_model(algo)
            used_algorithm = algo
            logger.info("Using trained '%s' model for prediction.", algo)
            break
        except FileNotFoundError:
            continue

    if model is None:
        try:
            from app.api.routes_clustering import _ensure_preprocessed, train_all_models
            _ensure_preprocessed()
            train_all_models()
            model = _cluster_service.load_model("kmeans")
            used_algorithm = "kmeans"
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No trained clustering model found. "
                    "Please train a model via /api/clustering/train first."
                ),
            )

    try:
        if hasattr(model, "predict"):
            cluster_id: int = int(model.predict(X_single)[0])
        else:
            kmeans_model = _cluster_service.load_model("kmeans")
            cluster_id = int(kmeans_model.predict(X_single)[0])
            used_algorithm = "kmeans"
    except Exception as exc:
        logger.exception("Model prediction failed.")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}")

    # ── 5. Fetch cluster profile ──────────────────────────────────────────────
    profiles: List[Dict[str, Any]] = _seg_service.load_profiles()

    matching_profile: Dict[str, Any] = {}
    segment_label = f"Segment {cluster_id + 1}"
    characteristics: List[str] = []

    for profile in profiles:
        if profile.get("cluster_id") == cluster_id:
            matching_profile = profile
            segment_label = profile.get("label", segment_label)
            characteristics = profile.get("characteristics", [])
            break

    if not matching_profile:
        # No profile stored — build a minimal one on the fly
        logger.warning(
            "No profile found for cluster_id=%d. Returning generic response.", cluster_id
        )
        matching_profile = {
            "cluster_id": cluster_id,
            "label": segment_label,
            "note": "Profile not available. Please retrain and inspect /api/segments.",
        }

    # ── 6. Save prediction to Database (SQL & MongoDB) ──────────────────────
    try:
        from app.services.db_service import db_service
        db_service.save_prediction(
            age=request.age,
            gender=request.gender,
            annual_income=request.annual_income,
            spending_score=request.spending_score,
            purchase_frequency=request.purchase_frequency,
            predicted_cluster=cluster_id,
            segment_label=segment_label,
            algorithm_used=used_algorithm,
            characteristics=characteristics,
        )
        from app.services.mongo_service import mongo_service
        mongo_service.save_prediction(
            age=request.age,
            gender=request.gender,
            annual_income=request.annual_income,
            spending_score=request.spending_score,
            purchase_frequency=request.purchase_frequency,
            predicted_cluster=cluster_id,
            segment_label=segment_label,
            algorithm_used=used_algorithm,
            characteristics=characteristics,
        )
    except Exception as exc:
        logger.warning("Could not persist prediction to database: %s", exc)

    # ── 7. Return ─────────────────────────────────────────────────────────────
    return PredictionResponse(
        success=True,
        cluster_id=cluster_id,
        segment_label=segment_label,
        segment_profile=matching_profile,
        characteristics=characteristics,
        message=(
            f"Customer assigned to cluster {cluster_id} "
            f"('{segment_label}') using {used_algorithm} model."
        ),
    )
