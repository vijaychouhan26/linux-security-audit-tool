#!/usr/bin/env python3
"""
Check and install required dependencies for the Linux Security Audit Tool.
"""
import sys
import subprocess

def check_and_install():
    """Check if required packages are installed, install if missing."""
    required = {
        'flask': 'Flask>=2.3.0',
        'flask_cors': 'flask-cors>=4.0.0',
        'werkzeug': 'Werkzeug>=2.3.0',
        'reportlab': 'reportlab>=4.0.0'
    }
    
    missing = []
    
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✓ {module} is installed")
        except ImportError:
            print(f"✗ {module} is NOT installed")
            missing.append(package)
    
    if missing:
        print(f"\nInstalling missing packages: {', '.join(missing)}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--quiet'
            ] + missing)
            print("✓ All dependencies installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install dependencies: {e}")
            return False
    else:
        print("\n✓ All dependencies are already installed!")
        return True

if __name__ == '__main__':
    success = check_and_install()
    sys.exit(0 if success else 1)
