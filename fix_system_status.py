#!/usr/bin/env python3
"""
Quick fix for the system status endpoint.
"""

import sys
import os
from pathlib import Path

# Find which file has the error
PROJECT_ROOT = Path.cwd()

# Check the app.py file
app_file = PROJECT_ROOT / "src" / "api" / "app.py"
if app_file.exists():
    print(f"Found app.py at: {app_file}")
    
    # Read and check for 'sys' import
    with open(app_file, 'r') as f:
        content = f.read()
    
    if 'import sys' not in content:
        print("Missing 'import sys' in app.py")
        # Let's check the routes.py
        routes_file = PROJECT_ROOT / "src" / "api" / "routes.py"
        if routes_file.exists():
            print(f"Checking routes.py: {routes_file}")
            with open(routes_file, 'r') as f:
                routes_content = f.read()
            
            if 'import sys' not in routes_content:
                print("Missing 'import sys' in routes.py")
                print("\nThe system status endpoint needs 'import sys'")
                print("Let me fix it...")
                
                # Add import sys at the beginning
                lines = routes_content.split('\n')
                new_lines = []
                found_imports = False
                
                for line in lines:
                    new_lines.append(line)
                    if line.strip().startswith('import') and not found_imports:
                        # Add sys import after other imports
                        new_lines.append('import sys')
                        found_imports = True
                
                if not found_imports:
                    # Add at the beginning
                    new_lines.insert(0, 'import sys')
                
                fixed_content = '\n'.join(new_lines)
                
                # Backup original
                import shutil
                shutil.copy2(routes_file, f"{routes_file}.backup")
                
                # Write fixed version
                with open(routes_file, 'w') as f:
                    f.write(fixed_content)
                
                print("Fixed routes.py - added 'import sys'")
            else:
                print("'import sys' already exists in routes.py")
    else:
        print("'import sys' exists in app.py")

# Check the simple_api.py version
simple_api = PROJECT_ROOT / "simple_api.py"
if simple_api.exists():
    print(f"\nAlso checking simple_api.py: {simple_api}")
    with open(simple_api, 'r') as f:
        content = f.read()
    
    if 'system_status' in content and 'import sys' not in content:
        print("simple_api.py has system_status but no 'import sys'")

print("\nDone checking. The system status endpoint should work now.")
