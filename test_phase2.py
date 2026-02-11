#!/usr/bin/env python3
"""Test Phase 2 installation and imports."""

import sys
import os
from pathlib import Path

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("="*60)
print("PHASE 2 - COMPREHENSIVE TEST")
print("="*60)

# Test 1: Check Python version
print("\n1. Python Version Check:")
print(f"   Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# Test 2: Check Flask installation
print("\n2. Flask Installation Check:")
try:
    import flask
    print(f"   ✓ Flask version: {flask.__version__}")
except ImportError:
    print("   ❌ Flask not installed")
    print("   Run: pip install Flask flask-cors")

# Test 3: Check project structure
print("\n3. Project Structure Check:")
required_dirs = ['src', 'src/api', 'src/services', 'src/core', 'src/utils', 'config']
for dir_path in required_dirs:
    if Path(dir_path).exists():
        print(f"   ✓ {dir_path}/")
    else:
        print(f"   ❌ {dir_path}/ - missing")

# Test 4: Check imports
print("\n4. Import Tests:")
imports_to_test = [
    ('flask.Flask', 'from flask import Flask'),
    ('flask_cors.CORS', 'from flask_cors import CORS'),
    ('config.settings', 'from config import settings'),
]

for import_name, import_stmt in imports_to_test:
    try:
        exec(import_stmt)
        print(f"   ✓ {import_name}")
    except ImportError as e:
        print(f"   ❌ {import_name} - {e}")

# Test 5: Check if Lynis is installed
print("\n5. Lynis Check:")
import subprocess
result = subprocess.run(['which', 'lynis'], capture_output=True, text=True)
if result.returncode == 0:
    print(f"   ✓ Lynis found: {result.stdout.strip()}")
else:
    print("   ⚠  Lynis not found in PATH")
    print("   Install: sudo apt install lynis")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)

# If all looks good, try to run the actual app
response = input("\nTry to run the API server? (y/n): ")
if response.lower() == 'y':
    print("\nStarting API server...")
    try:
        from src.api.app_fixed import app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Error: {e}")
