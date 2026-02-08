#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify find_image_by_name() works correctly
"""

import utils
from pathlib import Path

# Configuration
IMAGES_DIR = r"C:\Users\RAZ\Desktop\Raz-Technologies\Presentation_application\Parents\Images"

def main():
    """Test the image finding function"""
    print("=" * 70)
    print("Testing find_image_by_name() function")
    print("=" * 70)

    # Setup logging
    logger = utils.setup_logging("test_find_image")

    # Get all images
    print(f"\n[*] Searching for images in: {IMAGES_DIR}")
    images = utils.find_files(IMAGES_DIR, utils.IMAGE_EXTENSIONS)
    print(f"[*] Found {len(images)} total images")

    # Test finding the special photo
    search_term = utils.SPECIAL_FAMILY_PHOTO
    print(f"\n[*] Searching for: {search_term}")

    result = utils.find_image_by_name(images, search_term, logger)

    if result:
        print(f"\n[+] SUCCESS: Found image!")
        print(f"    Path: {result}")
        print(f"    Filename: {Path(result).name}")
        print(f"    File exists: {Path(result).exists()}")
    else:
        print(f"\n[!] FAILED: Image not found!")
        print(f"    Check the log file for details")

    print("\n" + "=" * 70)

    return 0 if result else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
