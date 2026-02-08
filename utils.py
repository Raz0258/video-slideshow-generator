# -*- coding: utf-8 -*-
"""
Utility Module for Slideshow Generator
Handles logging, file operations, and helper functions
"""

import os
import sys
import logging
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional
from dataclasses import dataclass, asdict

# Configuration
LOG_DIR = r"C:\Users\RAZ\Desktop\Raz-Technologies\Presentation_application\Parents\Logs"
MAX_LOG_FILES = 20
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.wav', '.aac'}

# Anniversary-specific configuration
SPECIAL_FAMILY_PHOTO = "Screenshot_20250714_010356_WhatsApp.jpg"

@dataclass
class ImageMetadata:
    """Metadata for an image in the slideshow"""
    path: str
    index: int
    width: int
    height: int
    is_portrait: bool
    duration: float
    use_ken_burns: bool
    ken_burns_type: Optional[str] = None
    transition_type: Optional[str] = None


@dataclass
class VideoConfig:
    """Configuration for video generation"""
    images_dir: str
    audio_dir: str
    output_file: str
    resolution: Tuple[int, int]
    fps: int
    crf: int
    preset: str
    transition_duration: float
    audio_fade_in: float
    audio_fade_out: float

def get_hebrew_font_path(logger: Optional[logging.Logger] = None) -> str:
    """
    Get path to Hebrew-compatible font with fallback options

    Args:
        logger: Logger instance

    Returns:
        FFmpeg-formatted font path
    """
    # Fonts with excellent Hebrew support, in order of preference
    fonts_to_try = [
        ("Arial", r"C:\Windows\Fonts\arial.ttf"),
        ("Calibri", r"C:\Windows\Fonts\calibri.ttf"),
        ("Tahoma", r"C:\Windows\Fonts\tahoma.ttf"),
        ("David", r"C:\Windows\Fonts\david.ttf"),
        ("Miriam", r"C:\Windows\Fonts\miriam.ttf"),
    ]

    for font_name, font_file in fonts_to_try:
        if os.path.exists(font_file):
            # Convert to FFmpeg format: forward slashes, escaped colons
            ffmpeg_path = font_file.replace("\\", "/").replace(":", "\\:")
            if logger:
                logger.info(f"Using Hebrew font: {font_name}")
            return ffmpeg_path

    if logger:
        logger.warning("No Hebrew fonts found, using system default")
    return ""

def setup_logging(log_name: str = "slideshow", output_dir: Optional[str] = None) -> logging.Logger:
    """
    Setup logging with timestamped file and console output

    Args:
        log_name: Base name for the logger (typically project name)
        output_dir: Directory where output video will be saved. If provided, logs will be saved there.
                   If None, falls back to default LOG_DIR.

    Returns:
        Configured logger instance
    """
    # Determine log directory
    if output_dir:
        log_dir = Path(output_dir)
    else:
        log_dir = Path(LOG_DIR)

    log_dir.mkdir(parents=True, exist_ok=True)

    # Only rotate logs if using default LOG_DIR (not when saving next to video)
    if not output_dir:
        _rotate_logs(log_dir)

    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{log_name}_{timestamp}.log"

    # Configure logger
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers
    logger.handlers.clear()

    # File handler (DEBUG level)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(name)s.%(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)

    # Console handler (INFO level)
    # Configure stdout with UTF-8 encoding on Windows
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('[%(levelname)s] %(message)s')
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized: {log_file}")

    return logger


def _rotate_logs(log_dir: Path) -> None:
    """Delete oldest log files if exceeding MAX_LOG_FILES"""
    log_files = sorted(log_dir.glob("*.log"), key=lambda f: f.stat().st_mtime)

    if len(log_files) > MAX_LOG_FILES:
        files_to_delete = log_files[:len(log_files) - MAX_LOG_FILES]
        for log_file in files_to_delete:
            log_file.unlink()


def check_ffmpeg() -> bool:
    """
    Check if FFmpeg is installed and accessible

    Returns:
        True if FFmpeg is available, False otherwise
    """
    try:
        subprocess.run(['ffmpeg', '-version'],
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_disk_space(output_path: str, required_mb: int = 100) -> bool:
    """
    Check if sufficient disk space is available

    Args:
        output_path: Path where output will be saved
        required_mb: Required space in megabytes

    Returns:
        True if sufficient space available
    """
    try:
        output_dir = Path(output_path).parent
        stat = os.statvfs(output_dir) if hasattr(os, 'statvfs') else None

        if stat:
            available_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
            return available_mb > required_mb

        # Windows fallback
        import shutil
        total, used, free = shutil.disk_usage(output_dir)
        available_mb = free / (1024 * 1024)
        return available_mb > required_mb

    except Exception:
        return True  # Assume sufficient space if check fails


def find_files(directory: str, extensions: set) -> List[str]:
    """
    Find all files with specified extensions in directory

    Args:
        directory: Directory to search
        extensions: Set of file extensions to match

    Returns:
        Sorted list of file paths
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    files = [str(f) for f in dir_path.iterdir()
             if f.is_file() and f.suffix.lower() in extensions]

    return sorted(files)


def get_image_dimensions(image_path: str, logger: Optional[logging.Logger] = None) -> Tuple[int, int]:
    """
    Get image dimensions using ffprobe

    Args:
        image_path: Path to image file
        logger: Optional logger instance

    Returns:
        Tuple of (width, height)
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'json',
        image_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        width = data['streams'][0]['width']
        height = data['streams'][0]['height']

        if logger:
            logger.debug(f"Image dimensions for {Path(image_path).name}: {width}x{height}")

        return (width, height)
    except Exception as e:
        if logger:
            logger.warning(f"Failed to get dimensions for {image_path}: {e}")
        return (1920, 1080)  # Default


def get_audio_duration(audio_path: str, logger: Optional[logging.Logger] = None) -> float:
    """
    Get audio file duration in seconds

    Args:
        audio_path: Path to audio file
        logger: Optional logger instance

    Returns:
        Duration in seconds
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        audio_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        duration = float(data['format']['duration'])

        if logger:
            logger.info(f"Audio duration: {duration:.2f}s ({duration/60:.2f} minutes)")

        return duration
    except Exception as e:
        if logger:
            logger.error(f"Failed to get audio duration: {e}")
        raise


def format_duration(seconds: float) -> str:
    """Format seconds into MM:SS string"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes"""
    return os.path.getsize(file_path) / (1024 * 1024)


def save_metadata(metadata_list: List[ImageMetadata], output_path: str) -> None:
    """Save image metadata to JSON file for debugging"""
    json_path = Path(output_path).with_suffix('.json')

    # Convert to JSON-serializable format
    data = []
    for m in metadata_list:
        item = asdict(m)
        
        # Handle KenBurnsConfig object
        if item.get('ken_burns_type') is not None:
            kb_config = item['ken_burns_type']
            # Convert nested dataclass to dict with enum values as strings
            item['ken_burns_type'] = {
                'zoom_start': kb_config['zoom_start'],
                'zoom_end': kb_config['zoom_end'],
                'pan_x': kb_config['pan_x'],
                'pan_y': kb_config['pan_y'],
                'effect_type': kb_config['effect_type'].value,  # Convert enum to string
                'easing': kb_config['easing'].value,  # Convert enum to string
                'speed_multiplier': kb_config['speed_multiplier']
            }
        data.append(item)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def print_header(text: str) -> None:
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def find_image_by_name(images: List[str], partial_name: str,
                       logger: Optional[logging.Logger] = None) -> Optional[str]:
    """
    Find image by partial filename match (case-insensitive)
    Handles both full paths and filenames in partial_name
    """
    if logger:
        logger.debug(f"Searching for image: {partial_name}")
    
    # Extract just the filename if a path was provided
    search_filename = Path(partial_name).name.lower()
    
    # Try exact match first
    for img_path in images:
        filename = Path(img_path).name.lower()
        if search_filename == filename:
            if logger:
                logger.info(f"Found special image (exact match): {Path(img_path).name}")
            return img_path
    
    # Try partial match
    for img_path in images:
        filename = Path(img_path).name.lower()
        if search_filename in filename:
            if logger:
                logger.info(f"Found special image (partial match): {Path(img_path).name}")
            return img_path
    
    # Not found
    if logger:
        logger.error(f"Special image not found: '{partial_name}'")
        logger.error(f"Extracted filename: '{search_filename}'")
    
    return None


def create_hebrew_title_card(text: str, duration: float, resolution: tuple,
                             output_label: str, y_position: str = "(h-text_h)/2",
                             logger: Optional[logging.Logger] = None) -> str:
    """
    Create title card with Hebrew text using proper UTF-8 encoding

    Args:
        text: Hebrew text to display
        duration: Duration in seconds
        resolution: (width, height)
        output_label: Output stream label
        y_position: Y position expression (default: centered)
        logger: Optional logger instance

    Returns:
        FFmpeg filter string
    """
    width, height = resolution

    # Find Hebrew-compatible font
    font_path = get_hebrew_font_path(logger)
    if not font_path:
        font_path = "arial.ttf"  # Fallback to system font

    # Create black background with centered Hebrew text
    # Using text_shaping=1 for proper Hebrew/RTL rendering
    filter_str = (
        f"color=c=black:s={width}x{height}:d={duration}[bg_{output_label}];"
        f"[bg_{output_label}]drawtext="
        f"text='{text}':"
        f"fontfile={font_path}:"
        f"fontsize=80:"
        f"fontcolor=white:"
        f"borderw=3:"
        f"bordercolor=black:"
        f"text_shaping=1:"
        f"x=(w-text_w)/2:"
        f"y={y_position}:"
        f"alpha='if(lt(t,0.8),t/0.8,if(lt(t,{duration-0.8}),1,(({duration}-t)/0.8)))',"
        f"fps=30,settb=1/30"
        f"[{output_label}]"
    )

    if logger:
        logger.info(f"Created Hebrew title card with label [{output_label}], duration={duration}s")
        logger.debug(f"Title text length: {len(text)} characters")
        logger.debug(f"Y position: {y_position}")

    return filter_str


def print_summary(images_count: int, audio_file: str, output_file: str,
                 duration: float, elapsed_time: float, logger: logging.Logger) -> None:
    """Print final summary"""
    print_header("Summary")

    info = [
        f"Images processed: {images_count}",
        f"Audio file: {Path(audio_file).name}",
        f"Output file: {output_file}",
    ]

    if os.path.exists(output_file):
        file_size = get_file_size_mb(output_file)
        info.extend([
            f"File size: {file_size:.2f} MB",
            f"Video duration: {format_duration(duration)}",
        ])

    info.append(f"Processing time: {format_duration(elapsed_time)}")

    for line in info:
        print(f"  {line}")
        logger.info(line)

    print("=" * 70)

    if os.path.exists(output_file):
        logger.info("Slideshow video created successfully!")
        print("\n[+] Slideshow video created successfully!")
        print("[+] Ready for your celebration!")
    else:
        logger.error("Output file not found!")
        print("\n[!] Output file not found!")

# Add these at the END of utils.py

def validate_image(image_path: str, logger: Optional[logging.Logger] = None) -> bool:
    """
    Validate image integrity using FFmpeg
    
    Args:
        image_path: Path to image file
        logger: Optional logger instance
        
    Returns:
        True if image is valid, False if corrupted
    """
    cmd = [
        'ffmpeg',
        '-v', 'error',
        '-i', image_path,
        '-f', 'null',
        '-'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0 or result.stderr.strip():
            if logger:
                logger.error(f"Image validation failed: {Path(image_path).name}")
                logger.error(f"FFmpeg error: {result.stderr.strip()}")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        if logger:
            logger.error(f"Image validation timeout: {Path(image_path).name}")
        return False
    except Exception as e:
        if logger:
            logger.error(f"Image validation exception for {Path(image_path).name}: {e}")
        return False


def validate_all_images(images: List[str], logger: Optional[logging.Logger] = None) -> Tuple[List[str], List[str]]:
    """
    Validate all images and return valid/invalid lists
    
    Args:
        images: List of image paths
        logger: Optional logger instance
        
    Returns:
        Tuple of (valid_images, invalid_images)
    """
    valid = []
    invalid = []
    
    if logger:
        logger.info(f"Validating {len(images)} images...")
    
    print(f"[*] Validating {len(images)} images...")
    
    for i, img in enumerate(images, 1):
        if validate_image(img, logger):
            valid.append(img)
            if i % 10 == 0:  # Progress every 10 images
                print(f"    Validated {i}/{len(images)} images...")
        else:
            invalid.append(img)
            if logger:
                logger.warning(f"Skipping corrupted image: {Path(img).name}")
            print(f"    [!] Corrupted image skipped: {Path(img).name}")
    
    if logger:
        logger.info(f"Validation complete: {len(valid)} valid, {len(invalid)} invalid")
    
    print(f"[*] Validation complete: {len(valid)} valid, {len(invalid)} invalid")
    
    return valid, invalid