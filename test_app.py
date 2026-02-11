#!/usr/bin/env python3
"""Minimal Flask app to test installation."""

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    return jsonify({"message": "Linux Security Audit Tool API", "status": "running"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "audit-tool"})

@app.route('/api/scans', methods=['GET'])
def list_scans():
    return jsonify({"scans": [], "message": "API is working"})

if __name__ == '__main__':
    print("Starting test API server on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
