import urllib.request
import json

BASE = 'http://localhost:8000'

def test_ev_pipeline():
    print("Testing full ML pipeline with EV_Charging_Dataset_1000_Rows.csv...")

    # 1. Upload
    filepath = r'c:\Users\HP\Downloads\EV_Charging_Dataset_1000_Rows.csv'
    boundary = '----WebKitFormBoundaryEVTest123'
    with open(filepath, 'rb') as f:
        content = f.read()

    delimiter = f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="EV_Charging_Dataset_1000_Rows.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode('utf-8')
    footer = f'\r\n--{boundary}--\r\n'.encode('utf-8')
    body = delimiter + content + footer

    req = urllib.request.Request(f'{BASE}/api/dataset/upload', data=body, headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    })
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
        print('1. Uploaded:', res['filename'], '| Records:', res['total_records'])
        num_features = res['numerical_features']
        print('   Numerical features:', num_features)

    # 2. Preprocess
    req_data = json.dumps({'features': num_features, 'remove_duplicates': True}).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/api/preprocess', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
        print('2. Preprocessed records:', res['processed_records'], '| Features:', res['features_used'])

    # 3. Analyze Elbow & Silhouette
    req_data = json.dumps({'k_range': [2, 3, 4, 5, 6]}).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/api/clustering/analyze', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
        print('3. Optimal Elbow K:', res['optimal_k_elbow'], '| Optimal Silhouette K:', res['optimal_k_silhouette'])

    # 4. Train KMeans
    req_data = json.dumps({'algorithm': 'kmeans', 'k': 4}).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/api/clustering/train', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
        print('4. KMeans trained: Clusters =', res['metrics']['n_clusters'], '| Silhouette =', res['metrics']['silhouette_score'], '| DB =', res['metrics']['davies_bouldin_score'])
        print('   Profiles created:', len(res['profiles']))
        for p in res['profiles']:
            print(f"   Cluster {p['cluster_id']}: '{p['label']}' (Size: {p['size']})")

    # 5. PCA
    with urllib.request.urlopen(f'{BASE}/api/clustering/pca') as r:
        res = json.loads(r.read().decode('utf-8'))
        print('5. PCA points:', len(res['pca_data']))

    print("\nSUCCESS: EV Charging dataset runs through the full ML pipeline with ZERO ERRORS!")

if __name__ == '__main__':
    test_ev_pipeline()
