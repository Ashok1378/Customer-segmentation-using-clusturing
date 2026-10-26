"""
evaluation.py - Standalone metric calculation and model comparison helpers.
"""
from typing import List, Optional, Dict, Any

import numpy as np
from sklearn.metrics import silhouette_score, davies_bouldin_score

from app.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Individual metric helpers
# ---------------------------------------------------------------------------

def calculate_silhouette(X: np.ndarray, labels: np.ndarray) -> Optional[float]:
    """
    Safely compute the silhouette score.

    Returns None when:
      - Fewer than 2 distinct (non-noise) clusters exist.
      - The dataset has fewer than 2 samples.
      - Any other sklearn error occurs.
    """
    try:
        unique_labels = set(labels)
        # Exclude DBSCAN noise label (-1) for counting
        valid_labels = unique_labels - {-1}
        if len(valid_labels) < 2:
            logger.debug("Silhouette skipped: fewer than 2 valid clusters.")
            return None

        # For DBSCAN, only score non-noise points
        mask = labels != -1
        if mask.sum() < 2:
            return None

        score = silhouette_score(X[mask], labels[mask])
        return float(round(score, 6))
    except Exception as exc:
        logger.warning("Silhouette calculation failed: %s", exc)
        return None


def calculate_davies_bouldin(X: np.ndarray, labels: np.ndarray) -> Optional[float]:
    """
    Safely compute the Davies-Bouldin index.

    Returns None when fewer than 2 valid clusters exist or on any error.
    Lower is better; 0 is perfect.
    """
    try:
        unique_labels = set(labels)
        valid_labels = unique_labels - {-1}
        if len(valid_labels) < 2:
            logger.debug("Davies-Bouldin skipped: fewer than 2 valid clusters.")
            return None

        mask = labels != -1
        if mask.sum() < 2:
            return None

        score = davies_bouldin_score(X[mask], labels[mask])
        return float(round(score, 6))
    except Exception as exc:
        logger.warning("Davies-Bouldin calculation failed: %s", exc)
        return None


def calculate_wcss(
    X: np.ndarray, labels: np.ndarray, centers: np.ndarray
) -> Optional[float]:
    """
    Compute Within-Cluster Sum of Squares (inertia) given cluster centers.

    This mirrors KMeans ``inertia_`` but is computed manually so it can be
    reused for other algorithms if centers are available.

    Returns None on error.
    """
    try:
        wcss = 0.0
        for k in np.unique(labels):
            if k == -1:
                continue  # Skip noise
            cluster_points = X[labels == k]
            center = centers[k]
            wcss += float(np.sum((cluster_points - center) ** 2))
        return round(wcss, 4)
    except Exception as exc:
        logger.warning("WCSS calculation failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Optimal-k finders
# ---------------------------------------------------------------------------

def find_optimal_k_elbow(wcss_values: List[float], k_values: List[int]) -> int:
    """
    Find the elbow point in a WCSS curve using the second-derivative method.

    The second derivative measures the rate of change of the slope; the point
    with the highest second derivative is the sharpest bend (elbow).

    Falls back to the midpoint of k_values if the calculation fails.
    """
    if len(wcss_values) < 3 or len(k_values) < 3:
        return k_values[0] if k_values else 2

    try:
        wcss_arr = np.array(wcss_values, dtype=float)

        # First differences (slope)
        first_diff = np.diff(wcss_arr)
        # Second differences (curvature)
        second_diff = np.diff(first_diff)

        # The elbow is at the index with the maximum second derivative.
        # second_diff has length len(wcss) - 2; index 0 corresponds to k_values[1].
        elbow_idx = int(np.argmax(second_diff)) + 1  # +1 offset for alignment
        optimal_k = k_values[elbow_idx]
        logger.debug("Elbow method found optimal k=%s.", optimal_k)
        return int(optimal_k)
    except Exception as exc:
        logger.warning("Elbow detection failed: %s. Defaulting to k=%s.", exc, k_values[0])
        return int(k_values[0])


def find_optimal_k_silhouette(
    silhouette_scores: List[float], k_values: List[int]
) -> int:
    """
    Return the k value that yields the highest silhouette score.
    """
    if not silhouette_scores or not k_values:
        return 2

    try:
        best_idx = int(np.argmax(silhouette_scores))
        optimal_k = k_values[best_idx]
        logger.debug("Silhouette method found optimal k=%s.", optimal_k)
        return int(optimal_k)
    except Exception as exc:
        logger.warning("Silhouette optimal-k detection failed: %s.", exc)
        return int(k_values[0])


# ---------------------------------------------------------------------------
# Model comparison
# ---------------------------------------------------------------------------

def compare_models(models_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Given a list of training result dicts (one per algorithm), produce a
    comparison table sorted by silhouette score (descending, None last).

    Each input dict must contain at minimum:
        algorithm, n_clusters, silhouette_score, davies_bouldin_score, wcss, noise_points

    Returns the same list with an added ``rank`` field.
    """
    if not models_results:
        return []

    def sort_key(item: Dict) -> float:
        score = item.get("silhouette_score")
        return score if score is not None else -1.0

    sorted_results = sorted(models_results, key=sort_key, reverse=True)

    for rank, item in enumerate(sorted_results, start=1):
        item["rank"] = rank

    return sorted_results
