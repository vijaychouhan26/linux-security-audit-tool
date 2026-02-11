#!/usr/bin/env python3
"""
Runner script for the API server.
Use this to start the Flask API.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.api.app import app
from config import settings

if __name__ == "__main__":
    print("=" * 60)
    print("Linux Security Audit Tool - API Server")
    print("=" * 60)
    print(f"Host: {settings.API_HOST}")
    print(f"Port: {settings.API_PORT}")
    print(f"Debug mode: {settings.API_DEBUG}")
    print(f"Threaded: {settings.API_THREADED}")
    print(f"Scans directory: {settings.SCANS_DIR}")
    print("=" * 60)
    print("\nStarting API server...")
    print(f"API Documentation: http://{settings.API_HOST}:{settings.API_PORT}/api")
    print(f"Health check: http://{settings.API_HOST}:{settings.API_PORT}/health")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        app.run(
            host=settings.API_HOST,
            port=settings.API_PORT,
            debug=settings.API_DEBUG,
            threaded=settings.API_THREADED
        )
    except KeyboardInterrupt:
        print("\n\nAPI server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError starting API server: {e}")
        sys.exit(1)

