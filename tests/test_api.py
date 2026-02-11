
## Step 10: Create Basic API Tests

Create `tests/test_api.py`:

```python
"""
Basic API tests for Phase 2.
"""

import pytest
import json
import time
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.app import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'


def test_api_docs_endpoint(client):
    """Test API documentation endpoint."""
    response = client.get('/api')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'endpoints' in data
    assert 'POST /api/scans' in data['endpoints']


def test_list_scans_empty(client):
    """Test listing scans when none exist."""
    response = client.get('/api/scans')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'jobs' in data
    assert 'total' in data


def test_system_status(client):
    """Test system status endpoint."""
    response = client.get('/api/system/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'system' in data
    assert 'service' in data
    assert 'storage' in data


def test_history_endpoint(client):
    """Test scan history endpoint."""
    response = client.get('/api/history')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'scans' in data
    assert 'total' in data


def test_404_endpoint(client):
    """Test non-existent endpoint."""
    response = client.get('/api/nonexistent')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Not Found' in data['error']


if __name__ == '__main__':
    # Quick manual test
    import requests
    
    print("Testing API endpoints...")
    
    # Start the app in background thread for testing
    from threading import Thread
    from src.api.app import app
    
    thread = Thread(target=lambda: app.run(
        host='127.0.0.1',
        port=5001,  # Different port to avoid conflicts
        debug=False,
        use_reloader=False
    ), daemon=True)
    
    thread.start()
    time.sleep(2)  # Give app time to start
    
    try:
        base_url = "http://127.0.0.1:5001"
        
        # Test health
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test API docs
        response = requests.get(f"{base_url}/api")
        print(f"\nAPI docs: {response.status_code}")
        
        # Test system status
        response = requests.get(f"{base_url}/api/system/status")
        print(f"\nSystem status: {response.status_code}")
        
        print("\n✅ Basic API tests passed!")
        
    except Exception as e:
        print(f"\n❌ API test failed: {e}")
    
    # Thread will be killed when main exits
