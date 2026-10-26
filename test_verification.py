import json
import urllib.request
import os

BASE = 'http://localhost:8000'

def test_all():
    print("Testing backend endpoints...")
    # 1. Health
    with urllib.request.urlopen(f'{BASE}/api/health') as r:
        print('1. Health check:', json.loads(r.read().decode('utf-8')))

    # 2. Upload
    filepath = r'c:\Users\HP\Downloads\cinereview (2)\Customer_Segmentation_Clustering\data\sample_customer_data.csv'
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    with open(filepath, 'rb') as f:
        content = f.read()

    delimiter = f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="sample_customer_data.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode('utf-8')
    footer = f'\r\n--{boundary}--\r\n'.encode('utf-8')
    body = delimiter + content + footer

    req = urllib.request.Request(f'{BASE}/api/dataset/upload', data=body, headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    })
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
        print('2. Upload success:', res['success'], '| Total rows:', res['total_records'])

    # 3. Summary
    with urllib.request.urlopen(f'{BASE}/api/dataset/summary') as r:
        res = json.loads(r.read().decode('utf-8'))
        print('3. Summary features:', res['numerical_features'])

    # 4. Preprocess
    req_data = json.dumps({'features': ['Age', 'AnnualIncome', 'SpendingScore', 'PurchaseFrequency'], 'remove_duplicates': True}).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/api/preprocess', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
        print('4. Preprocess:', res['success'], '| Processed rows:', res['processed_records'])

    # 5. Analyze Elbow & Silhouette
    req_data = json.dumps({'k_range': [2, 3, 4, 5, 6, 7, 8]}).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/api/clustering/analyze', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
        print('5. Analyze: Optimal Elbow K =', res['optimal_k_elbow'], '| Optimal Silhouette K =', res['optimal_k_silhouette'], '| Recommended =', res['recommended_k'])

    # 6. Train KMeans
    req_data = json.dumps({'algorithm': 'kmeans', 'k': 5}).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/api/clustering/train', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
        print('6. Train KMeans metrics:', res['metrics'])

    # 7. Train Hierarchical
    req_data = json.dumps({'algorithm': 'hierarchical', 'k': 5, 'linkage': 'ward'}).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/api/clustering/train', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
        print('7. Train Hierarchical metrics:', res['metrics'])

    # 8. Train DBSCAN
    req_data = json.dumps({'algorithm': 'dbscan', 'eps': 0.8, 'min_samples': 5}).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/api/clustering/train', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
        print('8. Train DBSCAN metrics:', res['metrics'])

    # 9. Retrain KMeans as the active model for prediction
    req_data = json.dumps({'algorithm': 'kmeans', 'k': 5}).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/api/clustering/train', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))

    # 10. Comparison
    with urllib.request.urlopen(f'{BASE}/api/clustering/comparison') as r:
        res = json.loads(r.read().decode('utf-8'))
        print('9. Comparison results count:', len(res['results']))
        for m in res['results']:
            print(f"   Rank {m.get('rank')}: {m.get('algorithm')} (k={m.get('n_clusters')}) - Silhouette: {m.get('silhouette_score')}, DB: {m.get('davies_bouldin_score')}, WCSS: {m.get('wcss')}")

    # 11. Segments
    with urllib.request.urlopen(f'{BASE}/api/segments') as r:
        res = json.loads(r.read().decode('utf-8'))
        print('10. Segments count:', len(res['profiles']))
        for p in res['profiles']:
            print(f"    Cluster {p['cluster_id']}: '{p['label']}' - Size: {p['size']}, Avg Income: ${p['avg_income']:.0f}, Avg Spending: {p['avg_spending_score']:.1f}")

    # 12. PCA
    with urllib.request.urlopen(f'{BASE}/api/clustering/pca') as r:
        res = json.loads(r.read().decode('utf-8'))
        print('11. PCA data points:', len(res['pca_data']))

    # 13. Prediction
    req_data = json.dumps({
        'age': 35.0,
        'gender': 'Male',
        'annual_income': 95000.0,
        'spending_score': 80.0,
        'purchase_frequency': 25.0
    }).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/api/prediction/predict', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
        print('12. Predict success:', res['success'], '| Cluster:', res['cluster_id'], '| Label:', res['segment_label'])
        print('    Message:', res['message'])
        print('    Characteristics:', res.get('characteristics'))

    print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY! ZERO ERRORS.")

if __name__ == '__main__':
    test_all()
