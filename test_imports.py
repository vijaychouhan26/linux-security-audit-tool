#!/usr/bin/env python3
"""Test script to verify all imports work correctly."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("Testing imports...")

try:
    from src.utils.security import privilege_manager, SecurityError
    print("✓ Imported security module")
    
    from src.utils.file_handler import FileHandler
    print("✓ Imported file_handler module")
    
    from src.core.scanner import LynisScanner
    print("✓ Imported scanner module")
    
    from config import settings
    print("✓ Imported settings module")
    
    print("\n✅ All imports successful!")
    print(f"Project root: {project_root}")
    
except ImportError as e:
    print(f"\n❌ Import failed: {e}")
    print(f"Python path: {sys.path}")
    sys.exit(1)
