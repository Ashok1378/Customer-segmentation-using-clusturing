"""
clustering.py - KMeans, Hierarchical and DBSCAN training with PCA visualisation.
"""
import os
from typing import Dict, List, Any, Optional

import numpy as np
import joblib
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.decomposition import PCA

from app.config import settings
from app.utils.logger import get_logger
from app.services.evaluation import (
    calculate_silhouette,
    calculate_davies_bouldin,
    calculate_wcss,
    find_optimal_k_elbow,
    find_optimal_k_silhouette,
)

logger = get_logger(__name__)


class ClusteringService:
    """
    Wraps sklearn clustering algorithms and provides analysis utilities.
    """

    # -----------------------------------------------------------------------
    # Optimal-k analysis
    # -----------------------------------------------------------------------

    def analyze_optimal_k(
        self, X: np.ndarray, k_range: List[int]
    ) -> Dict[str, Any]:
        """
        Run the elbow method (WCSS) and silhouette analysis over *k_range*.

        Returns a dict with:
            wcss_values, silhouette_scores, k_values,
            optimal_k_elbow, optimal_k_silhouette, recommended_k
        """
        valid_k = [k for k in k_range if 2 <= k < len(X)]
        if not valid_k:
            raise ValueError(
                f"No valid k values in range {k_range} for dataset with {len(X)} samples."
            )

        wcss_values: List[float] = []
        silhouette_scores: List[float] = []

        logger.info("Analyzing optimal k over range %s ...", valid_k)

        for k in valid_k:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            km.fit(X)
            wcss_values.append(float(round(km.inertia_, 4)))

            sil = calculate_silhouette(X, km.labels_)
            silhouette_scores.append(float(sil) if sil is not None else 0.0)

            logger.debug("k=%d  WCSS=%.2f  Silhouette=%.4f", k, km.inertia_, silhouette_scores[-1])

        optimal_k_elbow = find_optimal_k_elbow(wcss_values, valid_k)
        optimal_k_silhouette = find_optimal_k_silhouette(silhouette_scores, valid_k)

        # Recommended k: prefer silhouette result; fall back to elbow
        recommended_k = optimal_k_silhouette if optimal_k_silhouette else optimal_k_elbow

        return {
            "wcss_values": wcss_values,
            "silhouette_scores": silhouette_scores,
            "k_values": valid_k,
            "optimal_k_elbow": optimal_k_elbow,
            "optimal_k_silhouette": optimal_k_silhouette,
            "recommended_k": recommended_k,
        }

    # -----------------------------------------------------------------------
    # Training methods
    # -----------------------------------------------------------------------

    def train_kmeans(self, X: np.ndarray, k: int) -> Dict[str, Any]:
        """
        Train a KMeans model with *k* clusters.

        Returns dict with:
            labels, centers, wcss, silhouette_score, davies_bouldin_score,
            n_clusters, algorithm
        """
        if k >= len(X):
            raise ValueError(
                f"k ({k}) must be less than the number of samples ({len(X)})."
            )

        logger.info("Training KMeans with k=%d ...", k)
        km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        km.fit(X)

        labels: np.ndarray = km.labels_
        centers: np.ndarray = km.cluster_centers_

        sil = calculate_silhouette(X, labels)
        db = calculate_davies_bouldin(X, labels)
        wcss = calculate_wcss(X, labels, centers)

        self.save_model(km, "kmeans")

        return {
            "algorithm": "kmeans",
            "labels": labels,
            "centers": centers,
            "n_clusters": k,
            "wcss": wcss,
            "silhouette_score": sil,
            "davies_bouldin_score": db,
            "noise_points": None,
        }

    def train_hierarchical(
        self, X: np.ndarray, k: int, linkage: str = "ward"
    ) -> Dict[str, Any]:
        """
        Train an AgglomerativeClustering model.

        Returns dict with:
            labels, n_clusters, silhouette_score, davies_bouldin_score, algorithm
        """
        if k >= len(X):
            raise ValueError(
                f"k ({k}) must be less than the number of samples ({len(X)})."
            )

        logger.info("Training Hierarchical clustering with k=%d, linkage=%s ...", k, linkage)
        model = AgglomerativeClustering(n_clusters=k, linkage=linkage)
        labels: np.ndarray = model.fit_predict(X)

        sil = calculate_silhouette(X, labels)
        db = calculate_davies_bouldin(X, labels)

        self.save_model(model, "hierarchical")

        return {
            "algorithm": "hierarchical",
            "labels": labels,
            "centers": None,
            "n_clusters": k,
            "wcss": None,
            "silhouette_score": sil,
            "davies_bouldin_score": db,
            "noise_points": None,
        }

    def train_dbscan(
        self, X: np.ndarray, eps: float = 0.5, min_samples: int = 5
    ) -> Dict[str, Any]:
        """
        Train a DBSCAN model.

        Noise points receive label -1.  Silhouette and Davies-Bouldin are
        only computed when at least 2 non-noise clusters are found.

        Returns dict with:
            labels, n_clusters, n_noise, silhouette_score,
            davies_bouldin_score, algorithm
        """
        logger.info("Training DBSCAN with eps=%.3f, min_samples=%d ...", eps, min_samples)
        model = DBSCAN(eps=eps, min_samples=min_samples)
        labels: np.ndarray = model.fit_predict(X)

        unique_labels = set(labels)
        n_noise = int(np.sum(labels == -1))
        n_clusters = len(unique_labels - {-1})

        logger.info("DBSCAN: %d clusters, %d noise points.", n_clusters, n_noise)

        sil = calculate_silhouette(X, labels)
        db = calculate_davies_bouldin(X, labels)

        self.save_model(model, "dbscan")

        return {
            "algorithm": "dbscan",
            "labels": labels,
            "centers": None,
            "n_clusters": n_clusters,
            "wcss": None,
            "silhouette_score": sil,
            "davies_bouldin_score": db,
            "noise_points": n_noise,
        }

    # -----------------------------------------------------------------------
    # PCA visualisation
    # -----------------------------------------------------------------------

    def get_pca_coordinates(
        self, X: np.ndarray, labels: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Project *X* to 2D via PCA and pair each point with its cluster label.

        Returns a list of dicts: [{x: float, y: float, cluster: int}, ...]
        """
        n_components = min(2, X.shape[1], X.shape[0])
        pca = PCA(n_components=n_components, random_state=42)
        coords = pca.fit_transform(X)

        result: List[Dict[str, Any]] = []
        for i, (coord, label) in enumerate(zip(coords, labels)):
            point: Dict[str, Any] = {
                "x": float(round(coord[0], 6)),
                "y": float(round(coord[1], 6)) if n_components > 1 else 0.0,
                "cluster": int(label),
            }
            result.append(point)

        logger.debug("PCA produced %d 2-D points.", len(result))
        return result

    # -----------------------------------------------------------------------
    # Model persistence
    # -----------------------------------------------------------------------

    def save_model(self, model: Any, algorithm: str) -> None:
        """Save a fitted sklearn model to backend/models/<algorithm>_model.pkl."""
        os.makedirs(settings.MODELS_DIR, exist_ok=True)
        path = os.path.join(settings.MODELS_DIR, f"{algorithm}_model.pkl")
        joblib.dump(model, path)
        logger.info("Model '%s' saved to %s.", algorithm, path)

    def load_model(self, algorithm: str) -> Any:
        """Load a fitted sklearn model from backend/models/<algorithm>_model.pkl."""
        path = os.path.join(settings.MODELS_DIR, f"{algorithm}_model.pkl")
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"No saved model found for algorithm '{algorithm}' at {path}. "
                "Please train the model first."
            )
        model = joblib.load(path)
        logger.info("Model '%s' loaded from %s.", algorithm, path)
        return model
