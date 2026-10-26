"""
config.py - Application configuration settings.
"""
import os
from pathlib import Path

# Compute backend directory: go up two levels from this file (app/ -> backend/)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_THIS_DIR)


class Settings:
    APP_NAME: str = "Customer Segmentation API"
    VERSION: str = "1.0.0"

    # Directory paths
    UPLOAD_DIR: str = os.path.join(_BACKEND_DIR, "uploads")
    MODELS_DIR: str = os.path.join(_BACKEND_DIR, "models")
    OUTPUTS_DIR: str = os.path.join(_BACKEND_DIR, "outputs")

    # File constraints
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB in bytes
    ALLOWED_EXTENSIONS: list = [".csv"]

    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Clustering defaults
    DEFAULT_K_RANGE: list = list(range(2, 11))
    DEFAULT_FEATURES: list = ["Age", "AnnualIncome", "SpendingScore", "PurchaseFrequency"]

    def __init__(self):
        # Ensure required directories exist
        for directory in [self.UPLOAD_DIR, self.MODELS_DIR, self.OUTPUTS_DIR]:
            os.makedirs(directory, exist_ok=True)


settings = Settings()

# Convenience module-level exports used by other modules
APP_TITLE = settings.APP_NAME
APP_DESCRIPTION = (
    "ML-powered customer segmentation using K-Means, Hierarchical Clustering, "
    "and DBSCAN. Provides EDA, elbow analysis, silhouette scores, and segment profiling."
)
APP_VERSION = settings.VERSION
CORS_ORIGINS = settings.CORS_ORIGINS

# Path constants
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
MODELS_DIR = Path(settings.MODELS_DIR)
OUTPUT_DIR = Path(settings.OUTPUTS_DIR)
CLUSTER_PROFILES_PATH = MODELS_DIR / "cluster_profiles.json"
