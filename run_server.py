#!/usr/bin/env python3
"""
Runner script that properly sets up Python path.
"""

import os
import sys
from pathlib import Path

# Get the absolute path to the project root
PROJECT_ROOT = Path(__file__).parent.absolute()
print(f"Project root: {PROJECT_ROOT}")

# Add project root to Python path
sys.path.insert(0, str(PROJECT_ROOT))

# Check if we're in a virtual environment
print(f"Python executable: {sys.executable}")
print(f"Python path:")
for p in sys.path[:3]:
    print(f"  {p}")

# Check Flask installation
try:
    import flask
    print(f"Flask version: {flask.__version__}")
except ImportError as e:
    print(f"Error: Flask not installed. Run: pip install Flask flask-cors")
    sys.exit(1)

# Now import and run our app
try:
    # First, let's test if we can import config
    try:
        from config import settings
        print("✓ Config imported successfully")
    except ImportError as e:
        print(f"Warning: Could not import config: {e}")
        print("Creating minimal config...")
        
        # Create a minimal config module
        import types
        settings = types.SimpleNamespace()
        settings.API_HOST = "0.0.0.0"
        settings.API_PORT = 5000
        settings.API_DEBUG = True
        settings.SCANS_DIR = PROJECT_ROOT / "scans"
        settings.LOGS_DIR = PROJECT_ROOT / "logs"
    
    # Try to import the main app
    from src.api.app import create_app
    print("✓ Main app imported successfully")
    
    # Create and run the app
    app = create_app()
    
    print("\n" + "="*60)
    print("Linux Security Audit Tool - PRODUCTION API")
    print("="*60)
    print(f"Host: {settings.API_HOST}")
    print(f"Port: {settings.API_PORT}")
    print(f"Debug: {settings.API_DEBUG}")
    print("="*60)
    print("\nAvailable endpoints:")
    print("  GET  /              - Service info")
    print("  GET  /health        - Health check")
    print("  GET  /api           - API documentation")
    print("  POST /api/scans     - Start a new scan")
    print("  GET  /api/scans     - List all scans")
    print("  GET  /api/scans/:id - Get scan status")
    print("\nStarting server...")
    print("="*60)
    
    app.run(
        host=settings.API_HOST,
        port=settings.API_PORT,
        debug=settings.API_DEBUG,
        threaded=True
    )
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\nTroubleshooting steps:")
    print("1. Make sure all __init__.py files exist:")
    print("   touch src/__init__.py src/api/__init__.py src/services/__init__.py")
    print("   touch src/core/__init__.py src/utils/__init__.py config/__init__.py")
    print("2. Check if modules exist:")
    print(f"   ls -la {PROJECT_ROOT}/src/api/")
    print(f"   ls -la {PROJECT_ROOT}/config/")
    print("3. Install dependencies:")
    print("   pip install Flask flask-cors")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
