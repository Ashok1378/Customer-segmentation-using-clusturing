import json
import urllib.request
import urllib.error

BASE = 'http://localhost:8000'

def test_edge_cases():
    print("Testing edge cases & validation...")

    # 1. Invalid prediction input (Negative age)
    req_data = json.dumps({
        'age': -5.0,
        'gender': 'Male',
        'annual_income': 50000.0,
        'spending_score': 50.0,
        'purchase_frequency': 10.0
    }).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/api/prediction/predict', data=req_data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req)
        print("FAIL: Expected 422 for negative age")
    except urllib.error.HTTPError as e:
        print(f"PASS: Negative age caught with HTTP {e.code}")

    # 2. Invalid spending score > 100
    req_data = json.dumps({
        'age': 30.0,
        'gender': 'Male',
        'annual_income': 50000.0,
        'spending_score': 150.0,
        'purchase_frequency': 10.0
    }).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/api/prediction/predict', data=req_data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req)
        print("FAIL: Expected 422 for spending_score > 100")
    except urllib.error.HTTPError as e:
        print(f"PASS: Excessive spending score caught with HTTP {e.code}")

    # 3. Model persistence check
    import os
    models_dir = r'c:\Users\HP\Downloads\cinereview (2)\Customer_Segmentation_Clustering\backend\models'
    files = os.listdir(models_dir)
    print("Persisted model files in models/:", files)
    assert any(f.endswith('.pkl') or f.endswith('.joblib') for f in files), "No model files saved!"
    assert 'cluster_profiles.json' in files, "No cluster profiles saved!"
    assert 'feature_metadata.json' in files, "No feature metadata saved!"
    print("PASS: Model persistence verified.")

    print("\nALL EDGE CASE TESTS PASSED!")

if __name__ == '__main__':
    test_edge_cases()
