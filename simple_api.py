#!/usr/bin/env python3
"""
Simple working Flask API for testing.
"""

from flask import Flask, jsonify
from flask_cors import CORS

# Create Flask app
app = Flask(__name__)
CORS(app)

# Basic endpoints
@app.route('/')
def home():
    return jsonify({
        "service": "Linux Security Audit Tool API",
        "version": "1.0.0",
        "status": "running"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/scans', methods=['GET'])
def list_scans():
    return jsonify({
        "scans": [],
        "message": "API is working",
        "endpoint": "GET /api/scans"
    })

@app.route('/api/scans', methods=['POST'])
def start_scan():
    import uuid
    return jsonify({
        "message": "Scan started (simulated)",
        "scan_id": f"scan_{uuid.uuid4().hex[:8]}",
        "status_endpoint": "/api/scans/{scan_id}",
        "estimated_time": "2-10 minutes"
    }), 202

@app.route('/api/scans/<scan_id>', methods=['GET'])
def get_scan_status(scan_id):
    return jsonify({
        "scan_id": scan_id,
        "status": "completed",
        "progress": 100,
        "current_phase": "Scan completed",
        "message": "This is a simulated response"
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Linux Security Audit Tool - SIMPLE API")
    print("="*60)
    print("Server running on: http://0.0.0.0:5000")
    print("\nTest endpoints:")
    print("  curl http://localhost:5000/")
    print("  curl http://localhost:5000/health")
    print("  curl http://localhost:5000/api/scans")
    print("  curl -X POST http://localhost:5000/api/scans")
    print("  curl http://localhost:5000/api/scans/test_123")
    print("\nPress Ctrl+C to stop")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
