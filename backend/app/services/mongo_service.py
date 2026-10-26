"""
mongo_service.py - MongoDB connection and service layer using pymongo.
Supports local MongoDB (mongodb://localhost:27017) and MongoDB Atlas (mongodb+srv://...).
Provides CRUD operations, dual-write synchronization, and connection testing.
"""
import os
import socket
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.utils.logger import get_logger

logger = get_logger(__name__)
load_dotenv()


class MongoService:
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.connected = False
        self.uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("MONGO_DB_NAME", "customer_segmentation_db")
        self._try_initial_connect()

    def _try_initial_connect(self):
        """Attempts to connect to MongoDB on startup without crashing if unavailable."""
        try:
            self.connect(self.uri)
        except Exception as exc:
            logger.info("MongoDB initial connection deferred: %s", exc)

    def connect(self, uri: str, db_name: str = "customer_segmentation_db") -> Dict[str, Any]:
        """Connect to MongoDB with the given URI."""
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=2500)
            # Test ping
            client.admin.command("ping")
            self.client = client
            self.db = client[db_name]
            self.uri = uri
            self.db_name = db_name
            self.connected = True

            # Ensure indexes
            self.db.datasets.create_index("uploaded_at")
            self.db.customers.create_index("customer_ref")
            self.db.clustering_runs.create_index("created_at")
            self.db.predictions.create_index("created_at")

            logger.info("Successfully connected to MongoDB database '%s'.", db_name)
            return {
                "success": True,
                "connected": True,
                "uri": self._mask_uri(uri),
                "db_name": db_name,
                "message": f"Connected to MongoDB ({db_name}) successfully!",
            }
        except (ConnectionFailure, ServerSelectionTimeoutError) as err:
            self.connected = False
            logger.warning("MongoDB connection failed for %s: %s", self._mask_uri(uri), err)
            return {
                "success": False,
                "connected": False,
                "error": str(err),
                "message": "Could not connect to MongoDB. If using local MongoDB, ensure mongod service is running. If using Atlas, verify connection string and network access.",
            }
        except Exception as exc:
            self.connected = False
            return {
                "success": False,
                "connected": False,
                "error": str(exc),
                "message": f"MongoDB error: {exc}",
            }

    def _mask_uri(self, uri: str) -> str:
        """Mask password in URI for logging/display."""
        if "@" in uri:
            try:
                prefix = uri.split("@")[0]
                host = uri.split("@")[1]
                if ":" in prefix:
                    user = prefix.split(":")[0] + ":" + prefix.split(":")[1]
                    return f"{user}:***@{host}"
            except Exception:
                pass
        return uri

    def get_status(self) -> Dict[str, Any]:
        """Return MongoDB connection status and document counts."""
        if not self.connected or not self.client or self.db is None:
            return {
                "connected": False,
                "engine": "mongodb",
                "uri": self._mask_uri(self.uri),
                "db_name": self.db_name,
                "counts": {"datasets": 0, "customers": 0, "clustering_runs": 0, "predictions": 0},
                "collections": [],
            }

        try:
            counts = {
                "datasets": self.db.datasets.count_documents({}),
                "customers": self.db.customers.count_documents({}),
                "clustering_runs": self.db.clustering_runs.count_documents({}),
                "predictions": self.db.predictions.count_documents({}),
            }
            collections = self.db.list_collection_names()
            return {
                "connected": True,
                "engine": "mongodb",
                "uri": self._mask_uri(self.uri),
                "db_name": self.db_name,
                "counts": counts,
                "collections": collections,
            }
        except Exception as exc:
            self.connected = False
            return {
                "connected": False,
                "engine": "mongodb",
                "error": str(exc),
                "counts": {},
            }

    def save_dataset(self, filename: str, filepath: str, total_records: int, total_features: int, features: list, summary: dict) -> Optional[str]:
        """Save dataset document to MongoDB."""
        if not self.connected or self.db is None:
            return None
        try:
            doc = {
                "filename": filename,
                "filepath": filepath,
                "total_records": total_records,
                "total_features": total_features,
                "features": features,
                "summary": summary,
                "uploaded_at": datetime.utcnow(),
            }
            res = self.db.datasets.insert_one(doc)
            return str(res.inserted_id)
        except Exception as exc:
            logger.error("Failed to save dataset in MongoDB: %s", exc)
            return None

    def save_customer_batch(self, customers: List[Dict[str, Any]]) -> int:
        """Bulk insert customer records into MongoDB."""
        if not self.connected or self.db is None or not customers:
            return 0
        try:
            docs = []
            for c in customers:
                docs.append({
                    "customer_ref": c.get("customer_ref"),
                    "age": c.get("age"),
                    "gender": c.get("gender"),
                    "annual_income": c.get("annual_income"),
                    "spending_score": c.get("spending_score"),
                    "purchase_frequency": c.get("purchase_frequency"),
                    "created_at": datetime.utcnow(),
                })
            res = self.db.customers.insert_many(docs)
            return len(res.inserted_ids)
        except Exception as exc:
            logger.error("Failed to insert customer records in MongoDB: %s", exc)
            return 0

    def save_clustering_run(self, algorithm: str, n_clusters: int, metrics: dict, profiles: list, hyperparameters: dict = None) -> Optional[str]:
        """Save clustering experiment document in MongoDB."""
        if not self.connected or self.db is None:
            return None
        try:
            doc = {
                "algorithm": algorithm,
                "n_clusters": n_clusters,
                "silhouette_score": metrics.get("silhouette_score"),
                "davies_bouldin_score": metrics.get("davies_bouldin_score"),
                "wcss": metrics.get("wcss"),
                "noise_points": metrics.get("noise_points", 0),
                "profiles": profiles,
                "hyperparameters": hyperparameters or {},
                "created_at": datetime.utcnow(),
            }
            res = self.db.clustering_runs.insert_one(doc)
            return str(res.inserted_id)
        except Exception as exc:
            logger.error("Failed to save clustering run in MongoDB: %s", exc)
            return None

    def save_prediction(self, age: float, gender: str, annual_income: float, spending_score: float, purchase_frequency: float, predicted_cluster: int, segment_label: str, algorithm_used: str = "kmeans", characteristics: list = None) -> Optional[str]:
        """Save customer prediction document in MongoDB."""
        if not self.connected or self.db is None:
            return None
        try:
            doc = {
                "age": age,
                "gender": gender,
                "annual_income": annual_income,
                "spending_score": spending_score,
                "purchase_frequency": purchase_frequency,
                "predicted_cluster": predicted_cluster,
                "segment_label": segment_label,
                "algorithm_used": algorithm_used,
                "characteristics": characteristics or [],
                "created_at": datetime.utcnow(),
            }
            res = self.db.predictions.insert_one(doc)
            return str(res.inserted_id)
        except Exception as exc:
            logger.error("Failed to save prediction in MongoDB: %s", exc)
            return None

    def get_recent_predictions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent predictions from MongoDB."""
        if not self.connected or self.db is None:
            return []
        try:
            cursor = self.db.predictions.find().sort("created_at", -1).limit(limit)
            results = []
            for doc in cursor:
                doc["id"] = str(doc.pop("_id"))
                if isinstance(doc.get("created_at"), datetime):
                    doc["created_at"] = doc["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                results.append(doc)
            return results
        except Exception as exc:
            logger.error("Failed to fetch predictions from MongoDB: %s", exc)
            return []

    def get_customers(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch customers from MongoDB."""
        if not self.connected or self.db is None:
            return []
        try:
            cursor = self.db.customers.find().limit(limit)
            results = []
            for doc in cursor:
                doc["id"] = str(doc.pop("_id"))
                if isinstance(doc.get("created_at"), datetime):
                    doc["created_at"] = doc["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                results.append(doc)
            return results
        except Exception as exc:
            logger.error("Failed to fetch customers from MongoDB: %s", exc)
            return []

    def get_datasets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch datasets from MongoDB."""
        if not self.connected or self.db is None:
            return []
        try:
            cursor = self.db.datasets.find().sort("uploaded_at", -1).limit(limit)
            results = []
            for doc in cursor:
                doc["id"] = str(doc.pop("_id"))
                if isinstance(doc.get("uploaded_at"), datetime):
                    doc["uploaded_at"] = doc["uploaded_at"].strftime("%Y-%m-%d %H:%M:%S")
                results.append(doc)
            return results
        except Exception as exc:
            logger.error("Failed to fetch datasets from MongoDB: %s", exc)
            return []


mongo_service = MongoService()
