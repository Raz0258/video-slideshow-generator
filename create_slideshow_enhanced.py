#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anniversary Slideshow Generator - 50th Anniversary Edition
Creates professional video slideshow with Hebrew text overlays

REFACTORED VERSION - Main entry point
"""

import os
import sys
import argparse
import utils
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import utils
from slideshow_generator import SlideshowGenerator
from config import ProjectConfig


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Anniversary Slideshow Generator - Configurable Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config config/projects/parents_50th.yaml    # Generate from config
  %(prog)s --config my_project.yaml --preview            # Generate preview
  %(prog)s --config my_project.yaml --images 10          # Use only first 10 images
        """
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        metavar="FILE",
        default="config/projects/parents_50th.yaml",
        help="Path to YAML configuration file (default: config/projects/parents_50th.yaml)"
    )

    parser.add_argument(
        "--preview",
        action="store_true",
        help="Generate preview with fewer images for testing"
    )

    parser.add_argument(
        "--images",
        type=int,
        metavar="N",
        help="Use only first N images (for testing)"
    )

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()

    # Load configuration first to determine output directory
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"[!] Configuration file not found: {config_path}")
            print(f"    Please create a config file or use --config to specify an existing one")
            print(f"    See config/projects/template.yaml for an example")
            return 1

        print(f"[*] Loading config: {config_path.name}")
        project_config = ProjectConfig(str(config_path))

        # Get project info and output directory for logging
        project_name = project_config.get('project.name', 'Slideshow')
        paths = project_config.get_paths()
        output_file = paths.get('output_file')
        output_dir = str(Path(output_file).parent) if output_file else None

        # Setup logging with output directory
        logger = utils.setup_logging(project_name.replace(' ', '_'), output_dir)

        logger.info(f"Loading configuration from: {config_path}")

        # Validate configuration
        validation_errors = project_config.validate()
        if validation_errors:
            logger.error("Configuration validation failed:")
            print("[!] Configuration validation failed:")
            for error in validation_errors:
                logger.error(f"  - {error}")
                print(f"    - {error}")
            return 1

        logger.info(f"Project: {project_name}")

        utils.print_header(f"Slideshow Generator - {project_name}")
        logger.info("Starting slideshow generation")
        logger.info("=" * 60)

        # Validation
        if not utils.check_ffmpeg():
            logger.error("FFmpeg not found. Please install FFmpeg.")
            print("[!] FFmpeg not found. Please install FFmpeg.")
            print("    Download from: https://ffmpeg.org/download.html")
            return 1

        # Get remaining paths from config (output_file already extracted above)
        images_dir = paths.get('images_dir')
        audio_dir = paths.get('audio_dir')
        preview_file = paths.get('preview_file', output_file.replace('.mp4', '_preview.mp4'))

        if not utils.check_disk_space(output_file):
            logger.warning("Low disk space detected")
            print("[!] Warning: Low disk space detected")

        # Find audio file
        audio_files = utils.find_files(audio_dir, utils.AUDIO_EXTENSIONS)
        if not audio_files:
            logger.error(f"No audio files found in {audio_dir}")
            print(f"[!] No audio files found in {audio_dir}")
            return 1

        audio_file = audio_files[0]
        logger.info(f"Using audio: {Path(audio_file).name}")
        print(f"[*] Audio: {Path(audio_file).name}")

        # Find images
        images = utils.find_files(images_dir, utils.IMAGE_EXTENSIONS)
        if len(images) < 2:
            logger.error("Need at least 2 images")
            print("[!] Need at least 2 images to create slideshow")
            return 1

        logger.info(f"Found {len(images)} total images")
        print(f"[*] Found {len(images)} images")

        # Apply image limit if specified
        if args.images:
            images = images[:args.images]
            logger.info(f"Limited to first {args.images} images")
            print(f"[*] Using first {args.images} images")

        # Preview mode
        if args.preview:
            logger.info("Preview mode enabled")
            print("[*] Preview mode: using every 5th image")
            images = images[::5]
            output = preview_file
        else:
            output = output_file

        logger.info(f"Processing {len(images)} images")
        print(f"[*] Processing {len(images)} images")
        print()

        # Initialize generator with project config
        generator = SlideshowGenerator(project_config, logger)

        # Generate slideshow
        success = generator.generate(images, audio_file, output)
        
        if success:
            print()
            print("=" * 60)
            print(f"[✓] Slideshow created successfully!")
            print(f"[✓] Output: {output}")
            print("=" * 60)
        else:
            print()
            print("=" * 60)
            print("[✗] Slideshow generation failed!")
            print("    Check the log file for details")
            print("=" * 60)
        
        return 0 if success else 1
    
    except KeyboardInterrupt:
        logger.info("User interrupted")
        print("\n[!] Interrupted by user")
        return 130
    
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\n[!] Error: {e}")
        print("    Check the log file for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())