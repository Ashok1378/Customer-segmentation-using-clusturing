import urllib.request
import json

BASE = 'http://localhost:8000'
filepath = r'c:\Users\HP\Downloads\EV_Charging_Dataset_1000_Rows.csv'
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
with open(filepath, 'rb') as f:
    content = f.read()

delimiter = f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="EV_Charging_Dataset_1000_Rows.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode('utf-8')
footer = f'\r\n--{boundary}--\r\n'.encode('utf-8')
body = delimiter + content + footer

req = urllib.request.Request(f'{BASE}/api/dataset/upload', data=body, headers={
    'Content-Type': f'multipart/form-data; boundary={boundary}'
})
try:
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode('utf-8'))
        print('Upload response success:', res.get('success'))
        print('Numerical features:', res.get('numerical_features'))
        print('Categorical features:', res.get('categorical_features'))
        print('Total records:', res.get('total_records'))
except Exception as e:
    print('Upload error:', e)
