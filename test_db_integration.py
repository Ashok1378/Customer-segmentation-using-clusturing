import sys
import os

# Insert backend dir to path
backend_dir = r"c:\Users\HP\Downloads\cinereview (2)\Customer_Segmentation_Clustering\backend"
sys.path.insert(0, backend_dir)

import pandas as pd
from app.database import init_db, DEFAULT_DB_PATH
from app.services.db_service import db_service

def test_db():
    print("Testing Database Integration...")
    print(f"Target DB Path: {DEFAULT_DB_PATH}")

    # 1. Initialize tables
    init_db()
    assert os.path.exists(DEFAULT_DB_PATH), "Database file was not created!"
    print("✓ Database file created successfully.")

    # 2. Check status
    status = db_service.get_status()
    print("✓ DB Status:", status)
    assert status["connected"] is True

    # 3. Test saving sample dataset
    sample_csv = r"c:\Users\HP\Downloads\cinereview (2)\Customer_Segmentation_Clustering\data\sample_customer_data.csv"
    df = pd.read_csv(sample_csv)
    summary = {"total_records": len(df), "total_features": len(df.columns)}
    dataset_id = db_service.save_dataset("sample_customer_data.csv", sample_csv, df, summary)
    print(f"✓ Saved dataset to DB with ID: {dataset_id}")
    assert dataset_id is not None

    # 4. Test saving clustering run
    metrics = {"silhouette_score": 0.552, "davies_bouldin_score": 0.686, "wcss": 96.64, "noise_points": 0}
    profiles = [
        {"cluster_id": 0, "label": "High Value Customers", "size": 40, "avg_income": 109350, "avg_spending_score": 68.5},
        {"cluster_id": 1, "label": "Budget Customers", "size": 40, "avg_income": 27375, "avg_spending_score": 22.9}
    ]
    run_id = db_service.save_clustering_run("kmeans", 5, metrics, profiles, {"k": 5}, dataset_id=dataset_id)
    print(f"✓ Saved clustering run to DB with ID: {run_id}")
    assert run_id is not None

    # 5. Test saving prediction
    pred_id = db_service.save_prediction(
        age=32.0,
        gender="Female",
        annual_income=85000.0,
        spending_score=75.0,
        purchase_frequency=22.0,
        predicted_cluster=0,
        segment_label="High Value Customers",
        algorithm_used="kmeans",
        characteristics=["High income", "High spending"]
    )
    print(f"✓ Saved prediction to DB with ID: {pred_id}")
    assert pred_id is not None

    # 6. Verify queries
    recent_preds = db_service.get_recent_predictions(limit=5)
    print(f"✓ Fetched {len(recent_preds)} recent predictions from DB:")
    for p in recent_preds:
        print(f"   Prediction #{p['id']}: {p['gender']}, Age {p['age']}, Income ${p['annual_income']} -> Cluster {p['predicted_cluster']} ({p['segment_label']})")

    recent_runs = db_service.get_clustering_runs(limit=5)
    print(f"✓ Fetched {len(recent_runs)} recent clustering runs from DB:")
    for r in recent_runs:
        print(f"   Run #{r['id']}: {r['algorithm']} (k={r['n_clusters']}) - Silhouette: {r['silhouette_score']}")

    final_status = db_service.get_status()
    print("✓ Final DB Counts:", final_status["counts"])
    print("\nDATABASE INTEGRATION FULLY TESTED AND WORKING WITH ZERO ERRORS!")

if __name__ == "__main__":
    test_db()
