#!/usr/bin/env python3
"""Diagnostic script to find the special photo"""

import os
from pathlib import Path

IMAGES_DIR = r"C:\Users\RAZ\Desktop\Raz-Technologies\Presentation_application\Parents\Images"
SPECIAL_PHOTO_NAME = "Screenshot_20250714_010356_WhatsApp.jpg"

print("=" * 70)
print("IMAGE DIAGNOSTIC TOOL")
print("=" * 70)

# Check if directory exists
if not os.path.exists(IMAGES_DIR):
    print(f"ERROR: Directory does not exist: {IMAGES_DIR}")
    exit(1)

print(f"\nDirectory: {IMAGES_DIR}")
print(f"Looking for: {SPECIAL_PHOTO_NAME}")
print()

# List all files
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
all_files = []
image_files = []

for file in os.listdir(IMAGES_DIR):
    full_path = os.path.join(IMAGES_DIR, file)
    if os.path.isfile(full_path):
        all_files.append(file)
        ext = Path(file).suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            image_files.append(file)

print(f"Total files in directory: {len(all_files)}")
print(f"Image files found: {len(image_files)}")
print()

# Look for the special photo
print("Searching for special photo...")
print()

found = False
for img_file in image_files:
    if SPECIAL_PHOTO_NAME.lower() == img_file.lower():
        print(f"✓ EXACT MATCH FOUND (case-insensitive):")
        print(f"  Looking for: {SPECIAL_PHOTO_NAME}")
        print(f"  Found file:  {img_file}")
        found = True
        break

if not found:
    # Try partial match
    print("No exact match. Trying partial matches...")
    print()
    
    for img_file in image_files:
        if "screenshot" in img_file.lower() and "whatsapp" in img_file.lower():
            print(f"✓ POTENTIAL MATCH:")
            print(f"  {img_file}")

if not found:
    print("\nNo matches found. All image files:")
    print()
    for i, img_file in enumerate(image_files[:20], 1):  # Show first 20
        print(f"  {i}. {img_file}")
    if len(image_files) > 20:
        print(f"  ... and {len(image_files) - 20} more")

print()
print("=" * 70)
print("\nRECOMMENDATIONS:")
print()

if found:
    print("1. The file exists but may have different casing")
    print("2. Update SPECIAL_FAMILY_PHOTO in utils.py to match exactly")
else:
    print("1. Check if the filename is spelled correctly")
    print("2. Verify the file is in the correct directory")
    print("3. Check for hidden characters or extra spaces in filename")
    print("4. Update SPECIAL_FAMILY_PHOTO in utils.py with the actual filename")