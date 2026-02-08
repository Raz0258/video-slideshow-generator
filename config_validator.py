#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Configuration Validator
Provides comprehensive validation with actionable feedback
"""

import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class IssueLevel(Enum):
    """Severity levels for validation issues"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    level: IssueLevel
    message: str
    suggestion: Optional[str] = None
    field: Optional[str] = None


@dataclass
class PreFlightReport:
    """Pre-flight check report before rendering"""
    is_ready: bool
    errors: List[ValidationIssue]
    warnings: List[ValidationIssue]
    info: List[ValidationIssue]
    estimated_duration: Optional[float] = None
    estimated_render_time: Optional[float] = None


class ConfigValidator:
    """Comprehensive configuration validator"""

    def __init__(self, logger=None):
        self.logger = logger

    def validate_config(self, config_path: str) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate configuration file comprehensively

        Args:
            config_path: Path to YAML config file

        Returns:
            (is_valid, issues_list)
        """
        from config import ProjectConfig

        issues = []

        # Load config
        try:
            config = ProjectConfig(config_path)
        except FileNotFoundError:
            issues.append(ValidationIssue(
                level=IssueLevel.ERROR,
                message=f"Configuration file not found: {config_path}",
                suggestion="Check the file path and ensure the file exists"
            ))
            return False, issues
        except Exception as e:
            issues.append(ValidationIssue(
                level=IssueLevel.ERROR,
                message=f"Failed to load configuration: {e}",
                suggestion="Check YAML syntax - ensure proper indentation and no tabs"
            ))
            return False, issues

        # Run built-in validation
        validation_errors = config.validate()
        for error in validation_errors:
            issues.append(ValidationIssue(
                level=IssueLevel.ERROR,
                message=error,
                suggestion=self._get_suggestion_for_error(error)
            ))

        # Additional checks
        issues.extend(self.check_file_paths(config))
        issues.extend(self.check_video_settings(config))
        issues.extend(self.check_text_overlays(config))

        # Try to validate timing if possible
        try:
            timing_issues = self.validate_timing_estimates(config)
            issues.extend(timing_issues)
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Could not validate timing: {e}")

        # Determine if valid (no errors, only warnings/info allowed)
        has_errors = any(issue.level == IssueLevel.ERROR for issue in issues)

        return not has_errors, issues

    def check_file_paths(self, config) -> List[ValidationIssue]:
        """Validate file paths and their contents"""
        issues = []
        paths = config.get_paths()

        # Check images directory
        images_dir = Path(paths.get('images_dir', ''))
        if not images_dir.exists():
            issues.append(ValidationIssue(
                level=IssueLevel.ERROR,
                message=f"Images directory does not exist: {images_dir}",
                suggestion=f"Create the directory: mkdir \"{images_dir}\" or update the path in your config",
                field="paths.images_dir"
            ))
        else:
            # Count images
            image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.JPG', '.JPEG', '.PNG'}
            images = [f for f in images_dir.iterdir()
                     if f.is_file() and f.suffix in image_exts]

            if len(images) < 2:
                issues.append(ValidationIssue(
                    level=IssueLevel.ERROR,
                    message=f"Need at least 2 images, found {len(images)} in {images_dir}",
                    suggestion="Add more images to the directory",
                    field="paths.images_dir"
                ))
            elif len(images) < 5:
                issues.append(ValidationIssue(
                    level=IssueLevel.WARNING,
                    message=f"Only {len(images)} images found - slideshow will be very short",
                    suggestion="Consider adding more images for a longer slideshow"
                ))
            else:
                issues.append(ValidationIssue(
                    level=IssueLevel.INFO,
                    message=f"Found {len(images)} images - looks good!"
                ))

        # Check audio directory
        audio_dir = Path(paths.get('audio_dir', ''))
        if not audio_dir.exists():
            issues.append(ValidationIssue(
                level=IssueLevel.ERROR,
                message=f"Audio directory does not exist: {audio_dir}",
                suggestion=f"Create the directory: mkdir \"{audio_dir}\" or update the path in your config",
                field="paths.audio_dir"
            ))
        else:
            audio_exts = {'.mp3', '.wav', '.m4a', '.aac', '.MP3', '.WAV'}
            audio_files = [f for f in audio_dir.iterdir()
                          if f.is_file() and f.suffix in audio_exts]

            if len(audio_files) == 0:
                issues.append(ValidationIssue(
                    level=IssueLevel.ERROR,
                    message=f"No audio files found in {audio_dir}",
                    suggestion="Add at least one MP3 or WAV file",
                    field="paths.audio_dir"
                ))
            elif len(audio_files) > 1:
                issues.append(ValidationIssue(
                    level=IssueLevel.INFO,
                    message=f"Found {len(audio_files)} audio files - will use the first one: {audio_files[0].name}"
                ))

        # Check output directory (create if doesn't exist)
        output_file = Path(paths.get('output_file', ''))
        output_dir = output_file.parent
        if not output_dir.exists():
            issues.append(ValidationIssue(
                level=IssueLevel.INFO,
                message=f"Output directory {output_dir} will be created when rendering"
            ))

        return issues

    def check_video_settings(self, config) -> List[ValidationIssue]:
        """Validate video settings"""
        issues = []
        video_settings = config.get_video_settings()

        # Check CRF
        crf = video_settings.get('crf', 18)
        if crf < 0 or crf > 51:
            issues.append(ValidationIssue(
                level=IssueLevel.ERROR,
                message=f"CRF must be 0-51, got {crf}",
                suggestion="Use 18 for visually lossless, 23 for good quality, 28 for acceptable quality",
                field="video_settings.crf"
            ))
        elif crf > 28:
            issues.append(ValidationIssue(
                level=IssueLevel.WARNING,
                message=f"CRF {crf} will produce lower quality video",
                suggestion="Consider using 23-28 for better quality"
            ))
        elif crf < 18:
            issues.append(ValidationIssue(
                level=IssueLevel.WARNING,
                message=f"CRF {crf} will produce very large files with marginal quality improvement",
                suggestion="CRF 18 is already visually lossless for most content"
            ))

        # Check FPS
        fps = video_settings.get('fps', 30)
        if fps not in [24, 25, 30, 50, 60]:
            issues.append(ValidationIssue(
                level=IssueLevel.WARNING,
                message=f"Unusual FPS value: {fps}",
                suggestion="Standard values are 24 (cinematic), 30 (standard), or 60 (smooth)"
            ))

        # Check preset
        preset = video_settings.get('preset', 'medium')
        if preset in ['veryslow', 'slower']:
            issues.append(ValidationIssue(
                level=IssueLevel.WARNING,
                message=f"Preset '{preset}' will result in very long rendering times",
                suggestion="Use 'medium' or 'slow' for a good balance between speed and file size"
            ))

        return issues

    def check_text_overlays(self, config) -> List[ValidationIssue]:
        """Validate text overlay settings"""
        issues = []
        text_overlays = config.get_text_overlays()

        # Check opening text
        opening = text_overlays.get('opening', {})
        if opening.get('enabled', True):
            main = opening.get('main', {})
            font = main.get('font', '')
            if font and not Path(font).exists():
                issues.append(ValidationIssue(
                    level=IssueLevel.WARNING,
                    message=f"Opening text font not found: {font}",
                    suggestion="Ensure the font file exists or use a default like C:/Windows/Fonts/arial.ttf",
                    field="text_overlays.opening.main.font"
                ))

            text = main.get('text', '')
            if not text:
                issues.append(ValidationIssue(
                    level=IssueLevel.WARNING,
                    message="Opening text is enabled but no text provided",
                    suggestion="Add opening text or disable: text_overlays.opening.enabled = false"
                ))

        # Check closing text
        closing = text_overlays.get('closing', {})
        if closing.get('enabled', True):
            main = closing.get('main', {})
            font = main.get('font', '')
            if font and not Path(font).exists():
                issues.append(ValidationIssue(
                    level=IssueLevel.WARNING,
                    message=f"Closing text font not found: {font}",
                    suggestion="Ensure the font file exists or use a default like C:/Windows/Fonts/arial.ttf",
                    field="text_overlays.closing.main.font"
                ))

        return issues

    def validate_timing_estimates(self, config) -> List[ValidationIssue]:
        """Estimate timing and check for potential issues"""
        issues = []
        timing_settings = config.get_timing_settings()

        # Get image duration
        image_duration = timing_settings.get('image_duration', 6.0)

        if image_duration < 2.0:
            issues.append(ValidationIssue(
                level=IssueLevel.WARNING,
                message=f"Image duration {image_duration}s is very short",
                suggestion="Consider 4-8 seconds per image for comfortable viewing"
            ))
        elif image_duration > 10.0:
            issues.append(ValidationIssue(
                level=IssueLevel.WARNING,
                message=f"Image duration {image_duration}s is very long",
                suggestion="Most viewers prefer 5-8 seconds per image"
            ))

        return issues

    def suggest_optimal_settings(self, num_images: int, audio_duration: float) -> Dict:
        """
        Suggest optimal settings based on content

        Args:
            num_images: Number of images
            audio_duration: Audio length in seconds

        Returns:
            Dictionary of suggested settings
        """
        # Default timing
        opening_part1 = 3.0
        opening_part2 = 6.0
        min_closing = 8.0

        # Calculate available time for images
        available = audio_duration - opening_part1 - opening_part2 - min_closing

        # Calculate suggested image duration
        suggested_duration = available / num_images if num_images > 0 else 6.0

        # Clamp to reasonable range
        suggested_duration = max(3.0, min(10.0, suggested_duration))

        # Adjust closing duration if needed
        actual_image_total = suggested_duration * num_images
        actual_closing = audio_duration - opening_part1 - opening_part2 - actual_image_total

        return {
            'sequences': {
                'opening': {
                    'part1_duration': opening_part1,
                    'part2_duration': opening_part2
                },
                'images': {
                    'duration_per_image': round(suggested_duration, 1)
                },
                'closing': {
                    'min_duration': round(max(min_closing, actual_closing), 1)
                }
            },
            'notes': [
                f"Based on {num_images} images and {audio_duration:.0f}s audio",
                f"Suggested {suggested_duration:.1f}s per image",
                f"This will result in a {audio_duration:.0f}s video"
            ]
        }

    def pre_flight_check(self, config_path: str) -> PreFlightReport:
        """
        Comprehensive pre-flight check before rendering

        Args:
            config_path: Path to config file

        Returns:
            PreFlightReport with all issues and estimates
        """
        is_valid, issues = self.validate_config(config_path)

        errors = [i for i in issues if i.level == IssueLevel.ERROR]
        warnings = [i for i in issues if i.level == IssueLevel.WARNING]
        info = [i for i in issues if i.level == IssueLevel.INFO]

        is_ready = len(errors) == 0

        return PreFlightReport(
            is_ready=is_ready,
            errors=errors,
            warnings=warnings,
            info=info
        )

    def _get_suggestion_for_error(self, error_message: str) -> str:
        """Get actionable suggestion for common errors"""
        error_lower = error_message.lower()

        if "not found" in error_lower and "image" in error_lower:
            return "Check the images directory path and ensure the directory exists with at least 2 images"
        elif "not found" in error_lower and "audio" in error_lower:
            return "Check the audio directory path and ensure it contains at least one MP3 or WAV file"
        elif "special image" in error_lower:
            return "Ensure the special photo filename matches exactly (including extension) a file in your images directory"
        elif "weights" in error_lower and "sum" in error_lower:
            return "Transition weights must add up to exactly 1.0. Example: [0.70, 0.20, 0.10]"
        elif "timing" in error_lower and "positive" in error_lower:
            return "All timing values must be greater than 0. Use reasonable values like 3-10 seconds"
        elif "font" in error_lower:
            return "Ensure font files exist. Use C:/Windows/Fonts/arial.ttf for a safe default"
        else:
            return "Check the configuration documentation for valid values"


def print_validation_report(issues: List[ValidationIssue], show_info: bool = True):
    """Print formatted validation report"""
    errors = [i for i in issues if i.level == IssueLevel.ERROR]
    warnings = [i for i in issues if i.level == IssueLevel.WARNING]
    info = [i for i in issues if i.level == IssueLevel.INFO]

    if errors:
        print("\nERRORS:")
        for i, issue in enumerate(errors, 1):
            print(f"\n  {i}. {issue.message}")
            if issue.field:
                print(f"     Field: {issue.field}")
            if issue.suggestion:
                print(f"     Suggestion: {issue.suggestion}")

    if warnings:
        print("\nWARNINGS:")
        for i, issue in enumerate(warnings, 1):
            print(f"\n  {i}. {issue.message}")
            if issue.suggestion:
                print(f"     Suggestion: {issue.suggestion}")

    if show_info and info:
        print("\nINFO:")
        for issue in info:
            print(f"  - {issue.message}")

    if not errors and not warnings:
        print("\nAll checks passed! Configuration is valid.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python config_validator.py <config_file.yaml>")
        sys.exit(1)

    config_file = sys.argv[1]

    print("=" * 70)
    print("  Configuration Validator")
    print("=" * 70)
    print(f"\nValidating: {config_file}\n")

    validator = ConfigValidator()
    is_valid, issues = validator.validate_config(config_file)

    print_validation_report(issues)

    print("\n" + "=" * 70)
    if is_valid:
        print("Configuration is VALID - Ready to generate slideshow!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("Configuration has ERRORS - Please fix before proceeding")
        print("=" * 70)
        sys.exit(1)
