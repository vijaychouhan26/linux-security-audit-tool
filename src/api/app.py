"""
Flask API application for Linux Security Audit Tool.
JSON-only API, no HTML templates.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# CRITICAL: Add project root to Python path BEFORE any imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

print(f"[DEBUG] Project root: {project_root}")
print(f"[DEBUG] Current directory: {Path.cwd()}")

try:
    from flask import Flask, jsonify, request, send_file
    from flask_cors import CORS
    print("[DEBUG] ✓ Flask imports successful")
except ImportError as e:
    print(f"[ERROR] Flask import failed: {e}")
    print("[ERROR] Please install: pip install Flask flask-cors")
    sys.exit(1)

# Now try to import our config
try:
    from config import settings
    print("[DEBUG] ✓ Config import successful")
except ImportError as e:
    print(f"[ERROR] Config import failed: {e}")
    print("[ERROR] Make sure config/settings.py exists")
    sys.exit(1)

# Try to import our services (but don't fail if they don't work)
scan_service_available = False
try:
    from src.services.scan_service import scan_service
    scan_service_available = True
    print("[DEBUG] ✓ Scan service import successful")
except ImportError as e:
    print(f"[WARNING] Scan service import failed: {e}")
    print("[WARNING] Some endpoints will be disabled")

def create_app():
    """
    Create and configure the Flask application.
    """
    app = Flask(__name__)
    
    # Enable CORS for frontend development
    CORS(app)
    
    # Basic Flask configuration
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Not Found",
            "message": "The requested endpoint does not exist.",
            "timestamp": datetime.now().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal Server Error: {error}")
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred.",
            "timestamp": datetime.now().isoformat()
        }), 500
    
    # Basic endpoints (always available)
    @app.route('/')
    def index():
        return jsonify({
            "service": "Linux Security Audit Tool API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "GET /": "This information",
                "GET /health": "Health check",
                "GET /api": "API documentation",
                "POST /api/scans": "Start a new scan",
                "GET /api/scans": "List all scans",
                "GET /api/scans/<id>": "Get scan status",
                "GET /api/scans/<id>/results": "Get scan results",
                "GET /api/scans/<id>/raw": "Get raw output",
                "DELETE /api/scans/<id>": "Cancel a scan",
                "GET /api/history": "Get scan history",
                "GET /api/system/status": "Get system status"
            }
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "service": "linux-security-audit-tool",
            "timestamp": datetime.now().isoformat()
        })
    
    @app.route('/api')
    def api_docs():
        return jsonify({
            "api": "Linux Security Audit Tool API",
            "version": "v1",
            "status": "operational" if scan_service_available else "limited",
            "timestamp": datetime.now().isoformat()
        })
    
    # Only add scan endpoints if scan_service is available
    if scan_service_available:
        # Import routes
        try:
            from src.api.routes import register_routes
            register_routes(app)
            logger.info("Scan routes registered successfully")
        except ImportError as e:
            logger.error(f"Failed to import routes: {e}")
            
            # Add minimal scan endpoints as fallback
            @app.route('/api/scans', methods=['POST'])
            def start_scan_fallback():
                return jsonify({
                    "error": "Service Limited",
                    "message": "Scan service is not fully available",
                    "timestamp": datetime.now().isoformat()
                }), 503
    else:
        @app.route('/api/scans', methods=['POST', 'GET', 'DELETE'])
        @app.route('/api/scans/<path:subpath>', methods=['GET', 'DELETE'])
        @app.route('/api/history', methods=['GET'])
        @app.route('/api/system/status', methods=['GET'])
        def service_unavailable():
            return jsonify({
                "error": "Service Unavailable",
                "message": "Scan service is not available. Check server logs.",
                "timestamp": datetime.now().isoformat()
            }), 503
    
    logger.info("Flask application created successfully")
    return app


# Create app instance
app = create_app()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Linux Security Audit Tool API")
    print("="*60)
    print(f"Scan service: {'AVAILABLE' if scan_service_available else 'LIMITED'}")
    print(f"Host: 0.0.0.0")
    print(f"Port: 5000")
    print("="*60)
    print("\nStarting server...")
    
app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )


