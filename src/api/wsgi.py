"""
WSGI entry point for production deployment.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.app import app

if __name__ == "__main__":
    # For development
    app.run(host='0.0.0.0', port=5000, debug=True)
