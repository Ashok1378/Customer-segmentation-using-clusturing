"""
db_service.py - Database service layer handling CRUD operations for datasets,
customer records, clustering experiments, and prediction history.
"""
import json
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models_db import (
    DatasetRecord,
    CustomerRecord,
    ClusteringRun,
    ClusterProfileRecord,
    PredictionRecord,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseService:
    @staticmethod
    def get_status() -> Dict[str, Any]:
        """Check database connectivity and return entity counts."""
        session = SessionLocal()
        try:
            total_datasets = session.query(DatasetRecord).count()
            total_customers = session.query(CustomerRecord).count()
            total_runs = session.query(ClusteringRun).count()
            total_predictions = session.query(PredictionRecord).count()
            return {
                "connected": True,
                "engine": str(engine.url.drivername),
                "database_url": str(engine.url),
                "counts": {
                    "datasets": total_datasets,
                    "customer_records": total_customers,
                    "clustering_runs": total_runs,
                    "predictions": total_predictions,
                },
            }
        except Exception as exc:
            logger.error("Database status check failed: %s", exc)
            return {
                "connected": False,
                "error": str(exc),
                "counts": {},
            }
        finally:
            session.close()

    @staticmethod
    def save_dataset(
        filename: str,
        filepath: str,
        df: pd.DataFrame,
        summary: Dict[str, Any],
    ) -> Optional[int]:
        """Store uploaded dataset metadata and first 500 rows into the database."""
        session = SessionLocal()
        try:
            dataset_rec = DatasetRecord(
                filename=filename,
                filepath=filepath,
                total_records=len(df),
                total_features=len(df.columns),
                features_json=json.dumps(df.columns.tolist()),
                summary_json=json.dumps(summary, default=str),
            )
            session.add(dataset_rec)
            session.flush()

            # Insert customer rows (up to 500 to maintain fast ingestion)
            batch = []
            id_col = next((c for c in df.columns if c.lower() in ["customerid", "customer_id", "id", "station_id"]), None)

            for idx, row in df.head(500).iterrows():
                row_dict = row.to_dict()
                cust = CustomerRecord(
                    dataset_id=dataset_rec.id,
                    customer_ref=str(row_dict.get(id_col, f"REC_{idx}")),
                    age=float(row_dict.get("Age")) if "Age" in row_dict and pd.notna(row_dict.get("Age")) else None,
                    gender=str(row_dict.get("Gender")) if "Gender" in row_dict and pd.notna(row_dict.get("Gender")) else None,
                    annual_income=float(row_dict.get("AnnualIncome")) if "AnnualIncome" in row_dict and pd.notna(row_dict.get("AnnualIncome")) else None,
                    spending_score=float(row_dict.get("SpendingScore")) if "SpendingScore" in row_dict and pd.notna(row_dict.get("SpendingScore")) else None,
                    purchase_frequency=float(row_dict.get("PurchaseFrequency")) if "PurchaseFrequency" in row_dict and pd.notna(row_dict.get("PurchaseFrequency")) else None,
                    raw_data_json=json.dumps(row_dict, default=str),
                )
                batch.append(cust)

            session.bulk_save_objects(batch)
            session.commit()
            logger.info("Saved dataset '%s' (ID: %d) and %d records to DB.", filename, dataset_rec.id, len(batch))
            return dataset_rec.id
        except Exception as exc:
            session.rollback()
            logger.error("Failed to save dataset to database: %s", exc)
            return None
        finally:
            session.close()

    @staticmethod
    def save_clustering_run(
        algorithm: str,
        n_clusters: int,
        metrics: Dict[str, Any],
        profiles: List[Dict[str, Any]],
        hyperparameters: Optional[Dict[str, Any]] = None,
        dataset_id: Optional[int] = None,
    ) -> Optional[int]:
        """Record a completed clustering model run and its generated personas."""
        session = SessionLocal()
        try:
            run = ClusteringRun(
                dataset_id=dataset_id,
                algorithm=algorithm,
                n_clusters=n_clusters,
                silhouette_score=metrics.get("silhouette_score"),
                davies_bouldin_score=metrics.get("davies_bouldin_score"),
                wcss=metrics.get("wcss"),
                noise_points=metrics.get("noise_points", 0),
                hyperparameters_json=json.dumps(hyperparameters or {}),
            )
            session.add(run)
            session.flush()

            for p in profiles:
                prof_rec = ClusterProfileRecord(
                    run_id=run.id,
                    cluster_id=int(p.get("cluster_id", 0)),
                    label=str(p.get("label", f"Segment {p.get('cluster_id')}")),
                    size=int(p.get("size", 0)),
                    avg_age=p.get("avg_age"),
                    avg_income=p.get("avg_income"),
                    avg_spending_score=p.get("avg_spending_score"),
                    avg_purchase_frequency=p.get("avg_purchase_frequency"),
                    characteristics_json=json.dumps(p.get("characteristics", [])),
                    feature_averages_json=json.dumps(p.get("feature_averages", {})),
                )
                session.add(prof_rec)

            session.commit()
            logger.info("Saved clustering run ID %d (%s) with %d profiles to DB.", run.id, algorithm, len(profiles))
            return run.id
        except Exception as exc:
            session.rollback()
            logger.error("Failed to save clustering run to database: %s", exc)
            return None
        finally:
            session.close()

    @staticmethod
    def save_prediction(
        age: Optional[float],
        gender: Optional[str],
        annual_income: Optional[float],
        spending_score: Optional[float],
        purchase_frequency: Optional[float],
        predicted_cluster: int,
        segment_label: str,
        algorithm_used: str = "kmeans",
        characteristics: Optional[List[str]] = None,
    ) -> Optional[int]:
        """Persist a single customer inference query and predicted persona."""
        session = SessionLocal()
        try:
            pred = PredictionRecord(
                age=age,
                gender=gender,
                annual_income=annual_income,
                spending_score=spending_score,
                purchase_frequency=purchase_frequency,
                predicted_cluster=predicted_cluster,
                segment_label=segment_label,
                algorithm_used=algorithm_used,
                characteristics_json=json.dumps(characteristics or []),
            )
            session.add(pred)
            session.commit()
            logger.info("Saved prediction ID %d (Cluster %d: '%s') to DB.", pred.id, predicted_cluster, segment_label)
            return pred.id
        except Exception as exc:
            session.rollback()
            logger.error("Failed to save prediction to database: %s", exc)
            return None
        finally:
            session.close()

    @staticmethod
    def get_recent_predictions(limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch the most recent predictions ordered by created_at desc."""
        session = SessionLocal()
        try:
            records = (
                session.query(PredictionRecord)
                .order_by(PredictionRecord.created_at.desc())
                .limit(limit)
                .all()
            )
            results = []
            for r in records:
                results.append({
                    "id": r.id,
                    "age": r.age,
                    "gender": r.gender,
                    "annual_income": r.annual_income,
                    "spending_score": r.spending_score,
                    "purchase_frequency": r.purchase_frequency,
                    "predicted_cluster": r.predicted_cluster,
                    "segment_label": r.segment_label,
                    "algorithm_used": r.algorithm_used,
                    "characteristics": json.loads(r.characteristics_json or "[]"),
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
                })
            return results
        finally:
            session.close()

    @staticmethod
    def get_clustering_runs(limit: int = 15) -> List[Dict[str, Any]]:
        """Fetch history of clustering experiments."""
        session = SessionLocal()
        try:
            runs = (
                session.query(ClusteringRun)
                .order_by(ClusteringRun.created_at.desc())
                .limit(limit)
                .all()
            )
            results = []
            for r in runs:
                results.append({
                    "id": r.id,
                    "algorithm": r.algorithm,
                    "n_clusters": r.n_clusters,
                    "silhouette_score": r.silhouette_score,
                    "davies_bouldin_score": r.davies_bouldin_score,
                    "wcss": r.wcss,
                    "noise_points": r.noise_points,
                    "hyperparameters": json.loads(r.hyperparameters_json or "{}"),
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
                    "profiles_count": len(r.profiles),
                })
            return results
        finally:
            session.close()

    @staticmethod
    def get_datasets(limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch uploaded datasets history."""
        session = SessionLocal()
        try:
            datasets = (
                session.query(DatasetRecord)
                .order_by(DatasetRecord.uploaded_at.desc())
                .limit(limit)
                .all()
            )
            results = []
            for d in datasets:
                results.append({
                    "id": d.id,
                    "filename": d.filename,
                    "total_records": d.total_records,
                    "total_features": d.total_features,
                    "uploaded_at": d.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if d.uploaded_at else None,
                })
            return results
        finally:
            session.close()

    @staticmethod
    def get_customer_records(dataset_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch customer records from the database."""
        session = SessionLocal()
        try:
            query = session.query(CustomerRecord)
            if dataset_id:
                query = query.filter(CustomerRecord.dataset_id == dataset_id)
            records = query.order_by(CustomerRecord.id.asc()).limit(limit).all()
            results = []
            for c in records:
                results.append({
                    "id": c.id,
                    "dataset_id": c.dataset_id,
                    "customer_ref": c.customer_ref,
                    "age": c.age,
                    "gender": c.gender,
                    "annual_income": c.annual_income,
                    "spending_score": c.spending_score,
                    "purchase_frequency": c.purchase_frequency,
                    "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else None,
                })
            return results
        finally:
            session.close()


db_service = DatabaseService()
