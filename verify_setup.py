#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify test project setup"""

import sys
from pathlib import Path
from config import ProjectConfig

config_file = sys.argv[1] if len(sys.argv) > 1 else "config/projects/test_project.yaml"

print(f"Verifying configuration: {config_file}\n")

# Load config
try:
    pc = ProjectConfig(config_file)
    print("[OK] Configuration loaded successfully")
except Exception as e:
    print(f"[FAIL] Failed to load configuration: {e}")
    sys.exit(1)

# Validate
errors = pc.validate()
if errors:
    print(f"\n[FAIL] Validation failed with {len(errors)} error(s):")
    for i, error in enumerate(errors, 1):
        print(f"  {i}. {error}")
    sys.exit(1)
else:
    print("[OK] Configuration is valid")

# Check files
paths = pc.get_paths()
images_dir = Path(paths['images_dir'])
audio_dir = Path(paths['audio_dir'])

print(f"\nDirectories:")
print(f"  Images: {images_dir}")
print(f"  Audio: {audio_dir}")

if images_dir.exists():
    image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpeg"))
    print(f"\n[OK] Found {len(image_files)} image(s)")
    if len(image_files) < 2:
        print("  [WARN] Warning: Need at least 2 images")
else:
    print(f"\n[FAIL] Images directory not found")

if audio_dir.exists():
    audio_files = list(audio_dir.glob("*.mp3")) + list(audio_dir.glob("*.wav"))
    print(f"[OK] Found {len(audio_files)} audio file(s)")
    if len(audio_files) == 0:
        print("  [FAIL] Error: No audio files found")
else:
    print(f"[FAIL] Audio directory not found")

print("\n" + "="*60)
print("Setup verification complete!")
print("="*60)
