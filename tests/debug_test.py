#!/usr/bin/env python
"""Debug test for permissions"""
import requests
import json

BASE_URL = 'http://localhost:8000'

print("=" * 60)
print("COMPREHENSIVE DEBUG TEST")
print("=" * 60)

# 1. Register fresh user
print("\n[1] REGISTERING NEW USER...")
params = {
    'slug': 'debug-org',
    'name': 'Debug Org',
    'admin_email': 'debug@debugorg.com',
    'admin_password': 'Password123!',
    'admin_first_name': 'Debug',
    'admin_last_name': 'Admin'
}

response = requests.post(f'{BASE_URL}/api/auth/register', params=params)
print(f"Registration Status: {response.status_code}")
data = response.json()
token = data.get('access_token')
user_role = data['admin'].get('role')
print(f"User Role in Response: {user_role}")
print(f"Token: {token[:30]}...")

# 2. Check current user
print("\n[2] CHECKING CURRENT USER...")
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(f'{BASE_URL}/api/debug/current-user', headers=headers)
print(f"Status: {response.status_code}")
user_data = response.json()
print(f"Response: {json.dumps(user_data, indent=2)}")

# 3. Check permissions for analytics
print("\n[3] CHECKING ANALYTICS PERMISSION...")
response = requests.get(
    f'{BASE_URL}/api/debug/check-permission?resource=analytics&action=read',
    headers=headers
)
print(f"Status: {response.status_code}")
perm_data = response.json()
print(f"Response: {json.dumps(perm_data, indent=2)}")

# 4. Try actual analytics endpoint
print("\n[4] TESTING ANALYTICS ENDPOINT...")
response = requests.get(f'{BASE_URL}/api/analytics/product-inventory', headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text[:200]}")

# 5. Check products permission
print("\n[5] CHECKING PRODUCTS PERMISSION...")
response = requests.get(
    f'{BASE_URL}/api/debug/check-permission?resource=product&action=read',
    headers=headers
)
print(f"Status: {response.status_code}")
perm_data = response.json()
print(f"Response: {json.dumps(perm_data, indent=2)}")

# 6. Try products endpoint
print("\n[6] TESTING PRODUCTS ENDPOINT...")
response = requests.get(f'{BASE_URL}/api/plm/products', headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text[:200]}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
