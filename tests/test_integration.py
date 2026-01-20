"""
CDE MVP - Integration Test Script
Demonstrates complete PLM and Logistics workflows
"""

import requests
import json
from datetime import date, datetime

API_BASE = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_response(response, show_full=False):
    if response.status_code in [200, 201]:
        print(f"✓ Success ({response.status_code})")
        if show_full:
            print(json.dumps(response.json(), indent=2, default=str))
        else:
            data = response.json()
            if isinstance(data, list):
                print(f"  Returned {len(data)} items")
                if data:
                    print(f"  First item: {data[0]}")
            else:
                print(f"  {data}")
    else:
        print(f"✗ Error ({response.status_code})")
        print(f"  {response.text}")

def test_health():
    print_section("1. Health Check")
    response = requests.get(f"{API_BASE}/health")
    print_response(response, show_full=True)

def test_plm_workflow():
    print_section("2. PLM Workflow - Create Product with BOM")
    
    # Create parent product
    print("Creating parent product...")
    product_data = {
        "product_code": "ASSEMBLY-001",
        "name": "Test Assembly",
        "description": "Complete assembly for testing",
        "status": "development"
    }
    response = requests.post(f"{API_BASE}/api/plm/products", json=product_data)
    print_response(response)
    parent_product = response.json()
    parent_id = parent_product['id']
    
    # Create child products
    print("\nCreating component products...")
    components = []
    for i, (code, name) in enumerate([
        ("COMP-A", "Component A"),
        ("COMP-B", "Component B"),
        ("COMP-C", "Component C")
    ], 1):
        comp_data = {
            "product_code": code,
            "name": name,
            "description": f"Test component {i}",
            "status": "active"
        }
        response = requests.post(f"{API_BASE}/api/plm/products", json=comp_data)
        print_response(response)
        components.append(response.json())
    
    # Create revision
    print("\nCreating revision...")
    revision_data = {
        "product_id": parent_id,
        "revision_number": "A",
        "description": "Initial release"
    }
    response = requests.post(f"{API_BASE}/api/plm/revisions", json=revision_data)
    print_response(response)
    revision = response.json()
    revision_id = revision['id']
    
    # Add BOM items
    print("\nAdding BOM items...")
    for i, comp in enumerate(components, 1):
        bom_data = {
            "child_product_id": comp['id'],
            "quantity": i * 2,
            "unit": "EA",
            "position_number": i * 10
        }
        response = requests.post(
            f"{API_BASE}/api/plm/revisions/{revision_id}/bom",
            json=bom_data
        )
        print_response(response)
    
    # Get BOM
    print("\nRetrieving BOM...")
    response = requests.get(f"{API_BASE}/api/plm/revisions/{revision_id}/bom")
    print_response(response, show_full=True)
    
    # Release revision
    print("\nReleasing revision...")
    response = requests.post(f"{API_BASE}/api/plm/revisions/{revision_id}/release")
    print_response(response)
    
    return parent_product, components, revision

def test_inventory_workflow(products):
    print_section("3. Inventory Workflow - Receipt and Transfers")
    
    locations = ["WH-01", "WH-02"]
    
    # Receipt transactions
    print("Creating receipt transactions...")
    for product in products:
        for location in locations:
            txn_data = {
                "product_id": product['id'],
                "location_code": location,
                "transaction_type": "receipt",
                "quantity": 100 if location == "WH-01" else 50,
                "unit": "EA",
                "notes": f"Initial stock for {product['product_code']} at {location}"
            }
            response = requests.post(
                f"{API_BASE}/api/logistics/inventory/transactions",
                json=txn_data
            )
            print_response(response)
    
    # Transfer between locations
    print("\nCreating transfer...")
    product = products[0]
    
    # Transfer out
    txn_out = {
        "product_id": product['id'],
        "location_code": "WH-01",
        "transaction_type": "transfer_out",
        "quantity": 25,
        "unit": "EA",
        "notes": "Transfer to WH-02"
    }
    response = requests.post(
        f"{API_BASE}/api/logistics/inventory/transactions",
        json=txn_out
    )
    print_response(response)
    
    # Transfer in
    txn_in = {
        "product_id": product['id'],
        "location_code": "WH-02",
        "transaction_type": "transfer_in",
        "quantity": 25,
        "unit": "EA",
        "notes": "Transfer from WH-01"
    }
    response = requests.post(
        f"{API_BASE}/api/logistics/inventory/transactions",
        json=txn_in
    )
    print_response(response)
    
    # Check balances
    print("\nChecking inventory balances...")
    response = requests.get(f"{API_BASE}/api/logistics/inventory/balances")
    print_response(response, show_full=True)

def test_shipment_workflow(products):
    print_section("4. Shipment Workflow - Complete Lifecycle")
    
    # Create shipment
    print("Creating shipment...")
    shipment_data = {
        "shipment_number": f"SHIP-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "from_location": "WH-01",
        "to_location": "CUSTOMER-001",
        "destination_address": "123 Customer Street, City, Country",
        "carrier": "DHL",
        "planned_ship_date": date.today().isoformat(),
        "notes": "Test shipment",
        "lines": [
            {
                "product_id": products[0]['id'],
                "quantity_planned": 10,
                "unit": "EA"
            },
            {
                "product_id": products[1]['id'],
                "quantity_planned": 5,
                "unit": "EA"
            }
        ]
    }
    response = requests.post(
        f"{API_BASE}/api/logistics/shipments",
        json=shipment_data
    )
    print_response(response, show_full=True)
    shipment = response.json()
    shipment_id = shipment['id']
    
    # Confirm shipment (reserves inventory)
    print("\nConfirming shipment (reserves inventory)...")
    response = requests.post(f"{API_BASE}/api/logistics/shipments/{shipment_id}/confirm")
    print_response(response)
    
    # Check inventory after confirmation
    print("\nChecking inventory after confirmation (should see reserved quantities)...")
    response = requests.get(
        f"{API_BASE}/api/logistics/inventory/balances/{products[0]['id']}/WH-01"
    )
    print_response(response, show_full=True)
    
    # Pick shipment
    print("\nPicking shipment...")
    line_ids = [line['id'] for line in shipment['lines']]
    pick_data = {
        "line_quantities": {
            str(line_ids[0]): 10,
            str(line_ids[1]): 5
        }
    }
    response = requests.post(
        f"{API_BASE}/api/logistics/shipments/{shipment_id}/pick",
        json=pick_data
    )
    print_response(response)
    
    # Pack shipment
    print("\nPacking shipment...")
    pack_data = {
        "line_quantities": {
            str(line_ids[0]): 10,
            str(line_ids[1]): 5
        }
    }
    response = requests.post(
        f"{API_BASE}/api/logistics/shipments/{shipment_id}/pack",
        json=pack_data
    )
    print_response(response)
    
    # Ship (issues inventory and releases reservations)
    print("\nShipping (issues inventory, releases reservations)...")
    ship_data = {
        "actual_ship_date": date.today().isoformat(),
        "tracking_number": "1Z999AA10123456789"
    }
    response = requests.post(
        f"{API_BASE}/api/logistics/shipments/{shipment_id}/ship",
        json=ship_data
    )
    print_response(response)
    
    # Check final inventory
    print("\nChecking final inventory (should show issued quantities)...")
    response = requests.get(
        f"{API_BASE}/api/logistics/inventory/balances/{products[0]['id']}/WH-01"
    )
    print_response(response, show_full=True)
    
    return shipment

def test_analytics():
    print_section("5. Analytics - Cross-Domain Insights")
    
    # Product inventory summary
    print("Product Inventory Summary...")
    response = requests.get(f"{API_BASE}/api/analytics/product-inventory")
    print_response(response, show_full=True)
    
    # Recent inventory activity
    print("\nRecent Inventory Activity (last 20)...")
    response = requests.get(f"{API_BASE}/api/analytics/recent-inventory-activity?limit=20")
    data = response.json()
    print(f"✓ Retrieved {len(data)} transactions")
    if data:
        print("\nLast 5 transactions:")
        for txn in data[:5]:
            print(f"  {txn['created_at']}: {txn['product_code']} @ {txn['location_code']} - "
                  f"{txn['transaction_type']} {txn['quantity']} (balance: {txn['balance_after']})")
    
    # Shipment overview
    print("\nShipment Overview...")
    response = requests.get(f"{API_BASE}/api/analytics/shipment-overview")
    data = response.json()
    print(f"✓ Retrieved {len(data)} shipments")
    if data:
        print("\nShipment details:")
        for ship in data[:5]:
            print(f"  {ship['shipment_number']}: {ship['status']} - "
                  f"{ship['from_location']} → {ship['to_location']} "
                  f"({ship['line_count']} lines)")
    
    # Product change history
    print("\nProduct Change History...")
    response = requests.get(f"{API_BASE}/api/analytics/product-change-history?limit=10")
    data = response.json()
    print(f"✓ Retrieved {len(data)} events")
    if data:
        print("\nRecent changes:")
        for event in data[:5]:
            print(f"  {event['created_at']}: {event['product_code']} - {event['event_type']}")

def run_all_tests():
    """Run complete integration test suite"""
    print("\n" + "="*60)
    print("  CDE MVP - Integration Test Suite")
    print("  Testing PLM + Logistics + Analytics")
    print("="*60)
    
    try:
        # Test health
        test_health()
        
        # Test PLM
        parent_product, components, revision = test_plm_workflow()
        
        # Test Inventory
        test_inventory_workflow(components)
        
        # Test Shipment
        test_shipment_workflow(components)
        
        # Test Analytics
        test_analytics()
        
        print_section("Test Suite Complete")
        print("✓ All workflows executed successfully!")
        print("\nNext Steps:")
        print("1. Open http://localhost:8000/docs for API documentation")
        print("2. Open index.html for the web UI")
        print("3. Check database tables to see state + event data")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
