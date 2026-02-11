#!/usr/bin/env python3
"""
Test the fixed API with proper error handling.
"""

import time
import subprocess
import json

def run_curl_command(cmd):
    """Run a curl command and return the parsed JSON."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"raw_output": result.stdout, "error": "Not JSON"}
        else:
            return {"error": f"Command failed: {result.stderr}"}
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out"}
    except Exception as e:
        return {"error": str(e)}

def main():
    base_url = "http://localhost:5000"
    
    print("Testing Fixed Linux Security Audit API")
    print("="*60)
    
    # Test 1: Basic endpoints
    print("\n1. Testing basic endpoints:")
    
    print("  GET /")
    response = run_curl_command(f"curl -s {base_url}/")
    print(f"    Status: {'OK' if 'service' in response else 'FAILED'}")
    
    print("  GET /health")
    response = run_curl_command(f"curl -s {base_url}/health")
    print(f"    Status: {'OK' if response.get('status') == 'healthy' else 'FAILED'}")
    
    # Test 2: System status (previously broken)
    print("\n2. Testing system status (previously broken):")
    response = run_curl_command(f"curl -s {base_url}/api/system/status")
    if 'error' not in response:
        print(f"    ✓ System status working!")
        print(f"    Python version: {response.get('system', {}).get('python_version', 'N/A')}")
        print(f"    Lynis installed: {response.get('service', {}).get('lynis_installed', 'N/A')}")
    else:
        print(f"    ✗ Still broken: {response.get('error')}")
    
    # Test 3: Start a scan
    print("\n3. Testing scan creation:")
    response = run_curl_command(f"curl -s -X POST {base_url}/api/scans")
    if 'scan_id' in response:
        scan_id = response['scan_id']
        print(f"    ✓ Scan started: {scan_id}")
        
        # Wait a moment
        time.sleep(2)
        
        # Test 4: Check scan status
        print(f"\n4. Checking scan status for {scan_id}:")
        response = run_curl_command(f"curl -s {base_url}/api/scans/{scan_id}")
        if 'scan_id' in response:
            print(f"    Scan status: {response.get('status', 'unknown')}")
            print(f"    Progress: {response.get('progress', 0)}%")
        else:
            print(f"    Failed to get status: {response}")
    else:
        print(f"    ✗ Failed to start scan: {response}")
    
    # Test 5: List all scans
    print("\n5. Listing all scans:")
    response = run_curl_command(f"curl -s {base_url}/api/scans")
    if 'active_jobs' in response:
        print(f"    Active jobs: {len(response.get('active_jobs', []))}")
        print(f"    History scans: {len(response.get('history', []))}")
    else:
        print(f"    Response: {response}")
    
    # Test 6: Get history
    print("\n6. Getting scan history:")
    response = run_curl_command(f"curl -s {base_url}/api/history")
    if 'scans' in response:
        print(f"    Total history entries: {response.get('total', 0)}")
    else:
        print(f"    Response: {response}")
    
    print("\n" + "="*60)
    print("Test Complete!")
    print("\nTo manually test:")
    print(f"  curl {base_url}/")
    print(f"  curl {base_url}/api/system/status")
    print(f"  curl -X POST {base_url}/api/scans")
    print(f"  curl {base_url}/api/scans")
    
    # Show current scans if any
    print("\nCurrent scan jobs:")
    response = run_curl_command(f"curl -s {base_url}/api/scans")
    if 'active_jobs' in response:
        for job in response['active_jobs']:
            print(f"  - {job['scan_id']}: {job['status']} ({job['progress']}%)")

if __name__ == "__main__":
    main()
