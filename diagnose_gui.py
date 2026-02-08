#!/usr/bin/env python3
"""
Diagnostic script for GUI issues
"""
import sys
import os
from pathlib import Path

print("=" * 60)
print("GUI DIAGNOSTIC TOOL")
print("=" * 60)
print()

# Check Python version
print(f"[OK] Python version: {sys.version}")
print()

# Check working directory
print(f"[OK] Current directory: {os.getcwd()}")
print()

# Check required modules
print("Checking required modules:")
modules_to_check = [
    ('yaml', 'PyYAML'),
    ('flask', 'Flask'),
    ('flask_cors', 'flask-cors'),
]

all_modules_ok = True
for module_name, package_name in modules_to_check:
    try:
        __import__(module_name)
        print(f"  [OK] {package_name} - OK")
    except ImportError as e:
        print(f"  [FAIL] {package_name} - MISSING: {e}")
        all_modules_ok = False

print()

# Check if config module can be imported
print("Checking project modules:")
try:
    from config import ProjectConfig
    print("  [OK] config.ProjectConfig - OK")
except ImportError as e:
    print(f"  [FAIL] config.ProjectConfig - FAILED: {e}")
    all_modules_ok = False

print()

# Check key files
print("Checking key files:")
files_to_check = [
    'create_slideshow_enhanced.py',
    'config/__init__.py',
    'config/project_config.py',
    'web_gui/server.py',
    'web_gui/index.html',
]

all_files_ok = True
for file_path in files_to_check:
    if Path(file_path).exists():
        print(f"  [OK] {file_path} - EXISTS")
    else:
        print(f"  [FAIL] {file_path} - MISSING")
        all_files_ok = False

print()

# Check key directories
print("Checking key directories:")
dirs_to_check = [
    'Images',
    'Audio',
    'web_gui',
    'config/projects',
]

for dir_path in dirs_to_check:
    dir_obj = Path(dir_path)
    if dir_obj.exists():
        if dir_path in ['Images', 'Audio']:
            count = len(list(dir_obj.iterdir()))
            print(f"  [OK] {dir_path} - EXISTS ({count} files)")
        else:
            print(f"  [OK] {dir_path} - EXISTS")
    else:
        print(f"  [WARN] {dir_path} - MISSING (may cause issues)")

print()

# Try loading a test config
print("Testing config loading:")
test_config = Path('config/projects/parents_50th.yaml')
if test_config.exists():
    try:
        from config import ProjectConfig
        pc = ProjectConfig(str(test_config))
        project_name = pc.get('project.name', 'Unknown')
        print(f"  [OK] Successfully loaded {test_config.name}")
        print(f"    Project name: {project_name}")
    except Exception as e:
        print(f"  [FAIL] Failed to load config: {e}")
        all_modules_ok = False
else:
    print(f"  [WARN] Test config not found: {test_config}")

print()

# Check Flask server
print("Checking Flask server:")
server_script = Path('web_gui/server.py')
if server_script.exists():
    print(f"  [OK] Server script exists")
    print(f"  [INFO] To start server, run: python web_gui\\server.py")
    print(f"  [INFO] Or use: web_gui\\START_SERVER.bat")
else:
    print(f"  [FAIL] Server script not found")

print()

# Final summary
print("=" * 60)
if all_modules_ok and all_files_ok:
    print("[OK] ALL CHECKS PASSED")
    print()
    print("To use the GUI:")
    print("1. Open a terminal and run: web_gui\\START_SERVER.bat")
    print("2. Open web_gui\\index.html in your browser")
    print("3. Create your configuration and generate the video")
else:
    print("[FAIL] SOME CHECKS FAILED")
    print()
    print("Please fix the issues above before using the GUI")
print("=" * 60)
