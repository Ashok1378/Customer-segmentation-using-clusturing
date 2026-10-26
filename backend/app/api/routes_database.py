"""
routes_database.py - API endpoints for inspecting database status, past prediction history,
historical clustering runs, and stored datasets.
"""
from typing import Any, Dict, List
from fastapi import APIRouter

from app.services.db_service import db_service
from app.utils.logger import get_logger

router = APIRouter(prefix="/api/database", tags=["Database"])
logger = get_logger(__name__)


@router.get("/status", summary="Check database connection and counts")
def get_database_status() -> Dict[str, Any]:
    """Return database engine status and total counts of stored records."""
    return db_service.get_status()


@router.get("/predictions", summary="Get recent customer prediction history")
def get_prediction_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Return list of historical customer segment predictions saved in database."""
    return db_service.get_recent_predictions(limit=limit)


@router.get("/runs", summary="Get clustering experiments history")
def get_clustering_runs(limit: int = 15) -> List[Dict[str, Any]]:
    """Return historical clustering model runs saved in database."""
    return db_service.get_clustering_runs(limit=limit)


@router.get("/datasets", summary="Get stored dataset records")
def get_stored_datasets(limit: int = 10) -> List[Dict[str, Any]]:
    """Return uploaded dataset records stored in database."""
    return db_service.get_datasets(limit=limit)


@router.get("/customers", summary="Get customer records stored in database")
def get_customer_records(dataset_id: int = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Return customer data rows stored in database."""
    return db_service.get_customer_records(dataset_id=dataset_id, limit=limit)


@router.post("/auto-connect", summary="Automatically discover and connect database")
def trigger_auto_connect() -> Dict[str, Any]:
    """Auto-discovers local MySQL or connects SQLite, creating tables automatically."""
    from app.database import auto_connect
    return auto_connect()


# --- MongoDB Endpoints ---
from pydantic import BaseModel
from app.services.mongo_service import mongo_service


class MongoConnectRequest(BaseModel):
    uri: str = "mongodb://localhost:27017"
    db_name: str = "customer_segmentation_db"


@router.get("/mongo/status", summary="Check MongoDB connection status and counts")
def get_mongo_status() -> Dict[str, Any]:
    """Return MongoDB connection status and collection document counts."""
    return mongo_service.get_status()


@router.post("/mongo/connect", summary="Connect to MongoDB (Local or Atlas)")
def connect_mongo(payload: MongoConnectRequest) -> Dict[str, Any]:
    """Connect to MongoDB with the provided URI and database name."""
    res = mongo_service.connect(uri=payload.uri, db_name=payload.db_name)
    return res


@router.post("/mongo/sync", summary="Sync all records from SQL database into MongoDB")
def sync_sql_to_mongo() -> Dict[str, Any]:
    """Copies all stored datasets, customers, runs, and predictions from SQL to MongoDB."""
    if not mongo_service.connected or mongo_service.db is None:
        return {"success": False, "message": "MongoDB is not connected. Connect MongoDB first."}

    # Fetch from SQL
    from app.services.db_service import db_service
    datasets = db_service.get_datasets(limit=50)
    customers = db_service.get_customer_records(limit=500)
    runs = db_service.get_clustering_runs(limit=50)
    predictions = db_service.get_recent_predictions(limit=100)

    # Sync to MongoDB
    synced = {
        "datasets": 0,
        "customers": 0,
        "clustering_runs": 0,
        "predictions": 0,
    }

    if datasets:
        for d in datasets:
            mongo_service.save_dataset(
                filename=d.get("filename", "dataset.csv"),
                filepath=d.get("filepath", ""),
                total_records=d.get("total_records", 0),
                total_features=d.get("total_features", 0),
                features=d.get("features", []),
                summary={},
            )
        synced["datasets"] = len(datasets)

    if customers:
        synced["customers"] = mongo_service.save_customer_batch(customers)

    if runs:
        for r in runs:
            mongo_service.save_clustering_run(
                algorithm=r.get("algorithm", "kmeans"),
                n_clusters=r.get("n_clusters", 0),
                metrics={
                    "silhouette_score": r.get("silhouette_score"),
                    "davies_bouldin_score": r.get("davies_bouldin_score"),
                    "wcss": r.get("wcss"),
                    "noise_points": r.get("noise_points", 0),
                },
                profiles=[],
                hyperparameters=r.get("hyperparameters", {}),
            )
        synced["clustering_runs"] = len(runs)

    if predictions:
        for p in predictions:
            mongo_service.save_prediction(
                age=p.get("age"),
                gender=p.get("gender"),
                annual_income=p.get("annual_income"),
                spending_score=p.get("spending_score"),
                purchase_frequency=p.get("purchase_frequency"),
                predicted_cluster=p.get("predicted_cluster", 0),
                segment_label=p.get("segment_label", "Unknown"),
                algorithm_used=p.get("algorithm_used", "kmeans"),
                characteristics=p.get("characteristics", []),
            )
        synced["predictions"] = len(predictions)

    return {
        "success": True,
        "message": f"Successfully synchronized records from SQL into MongoDB!",
        "synced": synced,
    }


@router.get("/mongo/predictions", summary="Get recent predictions from MongoDB")
def get_mongo_predictions(limit: int = 50) -> List[Dict[str, Any]]:
    """Return predictions stored in MongoDB collection."""
    return mongo_service.get_recent_predictions(limit=limit)


@router.get("/mongo/customers", summary="Get customers from MongoDB")
def get_mongo_customers(limit: int = 50) -> List[Dict[str, Any]]:
    """Return customer documents stored in MongoDB collection."""
    return mongo_service.get_customers(limit=limit)



