#!/usr/bin/env python3
"""
Test the complete API.
"""

import requests
import time
import json

BASE_URL = "http://localhost:5000"

def test_endpoint(method, endpoint, data=None):
    """Test an API endpoint."""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data)
        elif method == "DELETE":
            response = requests.delete(f"{BASE_URL}{endpoint}")
        
        print(f"{method} {endpoint}: {response.status_code}")
        if response.status_code != 200:
            print(f"  Response: {response.text[:200]}")
        return response.json() if response.content else None
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("Testing Linux Security Audit API")
    print("="*60)
    
    # Test basic endpoints
    print("\n1. Basic endpoints:")
    test_endpoint("GET", "/")
    test_endpoint("GET", "/health")
    test_endpoint("GET", "/api")
    
    # Test system status
    print("\n2. System status:")
    status = test_endpoint("GET", "/api/system/status")
    if status:
        print(f"  Lynis installed: {status.get('service', {}).get('lynis_installed', False)}")
    
    # Test scan endpoints
    print("\n3. Scan management:")
    
    # Start a scan
    scan_data = test_endpoint("POST", "/api/scans")
    if scan_data and 'scan_id' in scan_data:
        scan_id = scan_data['scan_id']
        print(f"  Started scan: {scan_id}")
        
        # Check scan status
        time.sleep(2)
        status = test_endpoint("GET", f"/api/scans/{scan_id}")
        if status:
            print(f"  Scan status: {status.get('status')}")
        
        # Try to get results (might not be ready)
        results = test_endpoint("GET", f"/api/scans/{scan_id}/results")
        if results and 'error' not in results:
            print(f"  Results available")
    else:
        print("  Failed to start scan")
    
    # List all scans
    print("\n4. List all scans:")
    scans = test_endpoint("GET", "/api/scans")
    if scans:
        print(f"  Active jobs: {len(scans.get('active_jobs', []))}")
        print(f"  History: {len(scans.get('history', []))}")
    
    # Get history
    print("\n5. Scan history:")
    history = test_endpoint("GET", "/api/history")
    if history:
        print(f"  Total scans in history: {history.get('total', 0)}")
    
    print("\n" + "="*60)
    print("Test complete!")
    print("\nManual tests to try:")
    print(f"  curl -X POST {BASE_URL}/api/scans")
    print(f"  curl {BASE_URL}/api/scans")
    print(f"  curl {BASE_URL}/api/scans/YOUR_SCAN_ID")
    print(f"  curl {BASE_URL}/api/scans/YOUR_SCAN_ID/results")

if __name__ == "__main__":
    main()
