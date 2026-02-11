#!/usr/bin/env python3
"""
Frontend dashboard server.
Serves the HTML/CSS/JS and proxies API requests to the audit API.
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, send_from_directory, jsonify, request
from flask_cors import CORS
import requests
import logging

# Get the project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# Configuration
AUDIT_API_URL = "http://localhost:5000"  # Your Phase 2 API
PORT = 8080  # Frontend runs on port 8080
DEBUG = True

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def proxy_to_backend(endpoint, method='GET', data=None):
    """Proxy request to the backend API."""
    url = f"{AUDIT_API_URL}{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, params=request.args, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=data or request.get_json(), timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, timeout=30)
        else:
            return jsonify({"error": f"Method {method} not supported"}), 405
        
        # Return the backend response
        return response.content, response.status_code, response.headers.items()
    
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to backend API at {AUDIT_API_URL}")
        return jsonify({
            "error": "Backend API unavailable",
            "message": f"Cannot connect to {AUDIT_API_URL}. Make sure the audit API is running."
        }), 503
    except requests.exceptions.Timeout:
        logger.error(f"Request to {url} timed out")
        return jsonify({"error": "Backend request timeout"}), 504
    except Exception as e:
        logger.error(f"Error proxying to backend: {e}")
        return jsonify({"error": "Internal proxy error", "message": str(e)}), 500

@app.route('/')
def index():
    """Serve the main dashboard page."""
    return render_template('index.html')

@app.route('/scan/<scan_id>')
def scan_details(scan_id):
    """Serve the scan details page."""
    return render_template('scan_details.html', scan_id=scan_id)

# API Proxy endpoints
@app.route('/api/<path:endpoint>', methods=['GET', 'POST', 'DELETE'])
def api_proxy(endpoint):
    """Proxy API requests to the backend."""
    return proxy_to_backend(f"/api/{endpoint}", request.method)

@app.route('/health')
def health_proxy():
    """Proxy health check."""
    return proxy_to_backend("/health")

# Static file serving
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/assets/<path:filename>')
def asset_files(filename):
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Linux Security Audit Tool - DASHBOARD")
    print("="*60)
    print(f"Frontend: http://localhost:{PORT}")
    print(f"Backend API: {AUDIT_API_URL}")
    print("="*60)
    print("\nFeatures:")
    print("  • Dark mode SOC-style dashboard")
    print("  • Real-time scan monitoring")
    print("  • Interactive scan history")
    print("  • Detailed scan results")
    print("  • Persistent state (no reset on refresh)")
    print("\nPress Ctrl+C to stop")
    print("="*60)
    
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
