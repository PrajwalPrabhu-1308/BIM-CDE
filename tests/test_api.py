#!/usr/bin/env python
"""
Test script for CDE SaaS API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    """Test registration endpoint"""
    print("\n=== Testing Registration ===")
    params = {
        'slug': 'test-org',
        'name': 'Test Organization',
        'admin_email': 'admin@test.com',
        'admin_password': 'Password123!',
        'admin_first_name': 'Admin',
        'admin_last_name': 'User'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", params=params)
        print(f"Status Code: {response.status_code}")
        print(f"Raw Response: {response.text}")
        try:
            print(f"JSON Response: {json.dumps(response.json(), indent=2)}")
            return response.json()
        except:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_login():
    """Test login endpoint"""
    print("\n=== Testing Login ===")
    params = {
        'email': 'admin@test.com',
        'password': 'Password123!'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", params=params)
        print(f"Status Code: {response.status_code}")
        print(f"Raw Response: {response.text}")
        try:
            result = response.json()
            print(f"JSON Response: {json.dumps(result, indent=2)}")
            return result
        except:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_get_products(token):
    """Test getting products with auth"""
    print("\n=== Testing Get Products ===")
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/plm/products", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully retrieved {len(result)} products")
            if result:
                print(f"First product: {json.dumps(result[0], indent=2, default=str)}")
        else:
            print(f"Raw Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_analytics(token):
    """Test analytics endpoints"""
    print("\n=== Testing Analytics Endpoints ===")
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    endpoints = [
        "/api/analytics/product-inventory",
        "/api/analytics/shipment-overview",
        "/api/analytics/recent-inventory-activity?limit=20"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            print(f"{endpoint}: {response.status_code}")
            if response.status_code == 403:
                print(f"  → Requires additional permissions")
            elif response.status_code == 200:
                print(f"  → ✅ Success")
        except Exception as e:
            print(f"{endpoint}: Error - {e}")

def main():
    print("Starting CDE API Tests...")
    
    # Test registration
    reg_result = test_register()
    
    # Test login
    login_result = test_login()
    
    # If login successful, test protected endpoints
    if login_result and 'access_token' in login_result:
        token = login_result['access_token']
        print(f"\nGot token: {token[:20]}...")
        test_get_products(token)
        test_analytics(token)
    else:
        print("\nLogin failed, skipping protected endpoints")

if __name__ == "__main__":
    main()
