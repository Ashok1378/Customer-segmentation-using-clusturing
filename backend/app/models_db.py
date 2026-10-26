"""
models_db.py - SQLAlchemy ORM models for database persistence.
Tables:
  - datasets: uploaded datasets and file metadata
  - customer_records: individual customer rows from datasets
  - clustering_runs: training runs with algorithms, parameters, and evaluation metrics
  - cluster_profiles: customer persona profiles per cluster
  - prediction_records: individual customer prediction history
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class DatasetRecord(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    total_records = Column(Integer, default=0)
    total_features = Column(Integer, default=0)
    features_json = Column(Text, nullable=True)  # JSON list of column names
    summary_json = Column(Text, nullable=True)   # JSON string of summary
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    customers = relationship("CustomerRecord", back_populates="dataset", cascade="all, delete-orphan")
    runs = relationship("ClusteringRun", back_populates="dataset")


class CustomerRecord(Base):
    __tablename__ = "customer_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    customer_ref = Column(String(100), nullable=True)  # e.g., CustomerID or index
    age = Column(Float, nullable=True)
    gender = Column(String(50), nullable=True)
    annual_income = Column(Float, nullable=True)
    spending_score = Column(Float, nullable=True)
    purchase_frequency = Column(Float, nullable=True)
    raw_data_json = Column(Text, nullable=True)  # Full row dictionary as JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("DatasetRecord", back_populates="customers")


class ClusteringRun(Base):
    __tablename__ = "clustering_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    algorithm = Column(String(50), nullable=False)  # kmeans, hierarchical, dbscan
    n_clusters = Column(Integer, default=0)
    silhouette_score = Column(Float, nullable=True)
    davies_bouldin_score = Column(Float, nullable=True)
    wcss = Column(Float, nullable=True)
    noise_points = Column(Integer, default=0)
    hyperparameters_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("DatasetRecord", back_populates="runs")
    profiles = relationship("ClusterProfileRecord", back_populates="run", cascade="all, delete-orphan")


class ClusterProfileRecord(Base):
    __tablename__ = "cluster_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("clustering_runs.id"), nullable=False)
    cluster_id = Column(Integer, nullable=False)
    label = Column(String(150), nullable=False)
    size = Column(Integer, default=0)
    avg_age = Column(Float, nullable=True)
    avg_income = Column(Float, nullable=True)
    avg_spending_score = Column(Float, nullable=True)
    avg_purchase_frequency = Column(Float, nullable=True)
    characteristics_json = Column(Text, nullable=True)
    feature_averages_json = Column(Text, nullable=True)

    run = relationship("ClusteringRun", back_populates="profiles")


class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    age = Column(Float, nullable=True)
    gender = Column(String(50), nullable=True)
    annual_income = Column(Float, nullable=True)
    spending_score = Column(Float, nullable=True)
    purchase_frequency = Column(Float, nullable=True)
    predicted_cluster = Column(Integer, nullable=False)
    segment_label = Column(String(150), nullable=False)
    algorithm_used = Column(String(50), default="kmeans")
    characteristics_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
