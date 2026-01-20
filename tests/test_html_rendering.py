import requests

BASE_URL = 'http://localhost:8000'
endpoints = ['/demo', '/', '/plm']

for endpoint in endpoints:
    response = requests.get(f'{BASE_URL}{endpoint}')
    content_type = response.headers.get('content-type', 'NOT SET')
    first_50_chars = response.text[:50].replace('\n', ' ')
    print(f"\nEndpoint: {endpoint}")
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {content_type}")
    print(f"Preview: {first_50_chars}...")
