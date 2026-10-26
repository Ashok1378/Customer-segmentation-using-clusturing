"""
schemas.py - Pydantic request/response models for the Customer Segmentation API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# Dataset schemas
# ---------------------------------------------------------------------------

class DatasetSummary(BaseModel):
    model_config = {"extra": "allow"}
    total_records: int
    total_features: int
    missing_values: Dict[str, int]
    duplicate_records: int
    numerical_features: List[str]
    categorical_features: List[str]
    feature_stats: Dict[str, Any]
    sample_data: List[Dict[str, Any]]



# ---------------------------------------------------------------------------
# Preprocessing schemas
# ---------------------------------------------------------------------------

class PreprocessRequest(BaseModel):
    features: List[str] = ["Age", "AnnualIncome", "SpendingScore", "PurchaseFrequency"]
    handle_missing: str = "impute"
    remove_duplicates: bool = True


class PreprocessResponse(BaseModel):
    success: bool
    message: str
    original_records: int
    processed_records: int
    removed_duplicates: int
    imputed_values: Dict[str, int]
    features_used: List[str]
    warnings: List[str]


# ---------------------------------------------------------------------------
# Clustering analysis schemas
# ---------------------------------------------------------------------------

class ClusteringAnalysisRequest(BaseModel):
    k_range: Optional[List[int]] = None
    k_min: Optional[int] = 2
    k_max: Optional[int] = 10


class ClusteringAnalysisResponse(BaseModel):
    wcss_values: List[float]
    silhouette_scores: List[float]
    k_values: List[int]
    optimal_k_elbow: int
    optimal_k_silhouette: int
    recommended_k: int


# ---------------------------------------------------------------------------
# Clustering training schemas
# ---------------------------------------------------------------------------

class ClusteringTrainRequest(BaseModel):
    algorithm: str = "kmeans"
    k: Optional[int] = 3
    n_clusters: Optional[int] = None
    eps: float = 0.5
    min_samples: int = 5
    linkage: str = "ward"


class ClusterInfo(BaseModel):
    cluster_id: int
    size: int
    label: str
    avg_age: float
    avg_income: float
    avg_spending_score: float
    avg_purchase_frequency: float
    characteristics: List[str]


class ClusteringTrainResponse(BaseModel):
    success: bool
    algorithm: str
    n_clusters: int
    silhouette_score: Optional[float] = None
    davies_bouldin_score: Optional[float] = None
    wcss: Optional[float] = None
    noise_points: Optional[int] = None
    cluster_profiles: List[ClusterInfo]
    message: str


# ---------------------------------------------------------------------------
# Model comparison schemas
# ---------------------------------------------------------------------------

class ModelComparisonItem(BaseModel):
    algorithm: str
    n_clusters: int
    silhouette_score: Optional[float] = None
    davies_bouldin_score: Optional[float] = None
    wcss: Optional[float] = None
    noise_points: Optional[int] = None


# ---------------------------------------------------------------------------
# Prediction schemas
# ---------------------------------------------------------------------------

class PredictionRequest(BaseModel):
    age: float = Field(..., ge=0, le=120)
    gender: str = "Male"
    annual_income: float = Field(..., ge=0)
    spending_score: float = Field(..., ge=0, le=100)
    purchase_frequency: float = Field(..., ge=0)


class PredictionResponse(BaseModel):
    success: bool
    cluster_id: int
    segment_label: str
    segment_profile: Dict[str, Any]
    characteristics: List[str]
    message: str
