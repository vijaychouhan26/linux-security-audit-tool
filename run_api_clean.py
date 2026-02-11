#!/usr/bin/env python3
"""
Clean API runner with absolute imports.
"""

import os
import sys
from pathlib import Path

# Get absolute path to project root
PROJECT_ROOT = Path(__file__).parent.absolute()
print(f"Project root: {PROJECT_ROOT}")

# Add to Python path
sys.path.insert(0, str(PROJECT_ROOT))

# Check and install missing packages
try:
    import flask
    print(f"Flask version: {flask.__version__}")
except ImportError:
    print("Installing Flask...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Flask", "flask-cors"])

# Now import
from flask import Flask, jsonify
from flask_cors import CORS

# Create app
app = Flask(__name__)
CORS(app)

# Basic endpoints
@app.route('/')
def home():
    return jsonify({
        "service": "Linux Security Audit Tool",
        "status": "running",
        "endpoints": ["/health", "/api/scans"]
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/scans', methods=['GET'])
def list_scans():
    return jsonify({"scans": [], "message": "API is working"})

@app.route('/api/scans', methods=['POST'])
def start_scan():
    return jsonify({
        "message": "Scan started (simulated)",
        "scan_id": "test_123",
        "status_endpoint": "/api/scans/test_123"
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Linux Security Audit Tool - CLEAN API SERVER")
    print("="*60)
    print("Server running on: http://0.0.0.0:5000")
    print("Press Ctrl+C to stop")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
