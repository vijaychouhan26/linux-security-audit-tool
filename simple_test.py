import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("Testing imports...")
try:
    from flask import Flask
    print("✓ Flask imported")
    
    from flask_cors import CORS
    print("✓ flask-cors imported")
    
    # Test our config
    from config import settings
    print("✓ Config imported")
    
    print("\n✅ All imports successful!")
    
    # Try to run a simple server
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/')
    def hello():
        return {"message": "API is working!"}
    
    print("\nStarting test server on http://localhost:5001")
    print("Press Ctrl+C to stop")
    
    app.run(port=5001, debug=False)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nInstall missing packages:")
    print("  pip install Flask flask-cors")
