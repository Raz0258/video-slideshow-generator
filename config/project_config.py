"""
Project configuration loader and accessor
Loads YAML project files and provides access to settings
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_config import (
    VIDEO_DEFAULTS,
    EFFECT_DEFAULTS,
    TRANSITION_WEIGHTS,
    COLOR_GRADING_PRESETS,
    TIMING_DEFAULTS,
    AUDIO_DEFAULTS,
    PARTICLE_OVERLAY_DEFAULTS
)


class ProjectConfig:
    """
    Loads and provides access to project configuration
    Merges project-specific settings with base defaults
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize project configuration

        Args:
            config_path: Path to project YAML file. If None, uses defaults only.
        """
        self.config_path = config_path
        self.config_data = {}

        if config_path:
            self._load_config(config_path)

    def _load_config(self, filepath: str):
        """Load and parse YAML configuration file"""
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            self.config_data = yaml.safe_load(f) or {}

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Access nested config using dot notation

        Args:
            key_path: Dot-separated path (e.g., 'paths.images_dir')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config_data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_video_settings(self) -> Dict[str, Any]:
        """Get video settings, merging project overrides with defaults"""
        settings = VIDEO_DEFAULTS.copy()

        # Override with project-specific settings if provided
        project_settings = self.get('video_settings', {})
        if project_settings:
            settings.update(project_settings)

        return settings

    def get_effect_settings(self) -> Dict[str, Any]:
        """Get effect settings, merging project overrides with defaults"""
        settings = EFFECT_DEFAULTS.copy()

        # Override transition duration if specified
        style_config = self.get('style', {})
        if 'transitions' in style_config:
            trans_config = style_config['transitions']
            if 'duration' in trans_config:
                settings['transition_duration'] = trans_config['duration']

        # Override Ken Burns settings if specified
        if 'ken_burns' in style_config:
            kb_config = style_config['ken_burns']
            if 'application_rate' in kb_config:
                settings['ken_burns']['application_rate'] = kb_config['application_rate']
            if 'zoom_range' in kb_config:
                settings['ken_burns']['zoom_range'] = tuple(kb_config['zoom_range'])
            if 'pan_amount' in kb_config:
                settings['ken_burns']['pan_amount'] = kb_config['pan_amount']
            if 'speed_variations' in kb_config:
                settings['ken_burns']['speed_variations'] = kb_config['speed_variations']

        return settings

    def get_transition_weights(self) -> Dict[str, float]:
        """Get transition category weights"""
        weights = TRANSITION_WEIGHTS.copy()

        style_config = self.get('style.transitions', {})
        if 'weights' in style_config and 'categories' in style_config:
            categories = style_config['categories']
            weight_values = style_config['weights']

            if len(categories) == len(weight_values):
                weights = dict(zip(categories, weight_values))

        return weights

    def get_timing_settings(self) -> dict:
        """
        Get timing configuration for sequences
        
        Returns:
            Dictionary with timing settings matching YAML structure
        """
        sequences = self.config_data.get('sequences', {})
        
        # Opening timings
        opening = sequences.get('opening', {})
        opening_part1 = opening.get('part1_duration', 3.0)
        opening_part2 = opening.get('part2_duration', 6.0)
        
        # Image timings
        images = sequences.get('images', {})
        duration_per_image = images.get('duration_per_image', 6.0)
        
        # Closing timings
        closing = sequences.get('closing', {})
        min_closing = closing.get('min_duration', 8.0)
        
        return {
            'opening_part1_duration': opening_part1,
            'opening_part2_duration': opening_part2,
            'duration_per_image': duration_per_image,  # ← Key name to match YAML
            'min_closing_duration': min_closing
        }

    def get_audio_settings(self) -> Dict[str, Any]:
        """Get audio settings, merging project overrides with defaults"""
        settings = AUDIO_DEFAULTS.copy()

        style_config = self.get('style.audio', {})
        if style_config:
            settings.update(style_config)

        return settings

    def get_particle_settings(self) -> Dict[str, Any]:
        """Get particle overlay settings, merging project overrides with defaults"""
        settings = PARTICLE_OVERLAY_DEFAULTS.copy()

        style_config = self.get('style', {})
        if 'particle_overlays' in style_config:
            particle_config = style_config['particle_overlays']
            for key in settings:
                if key in particle_config:
                    settings[key] = particle_config[key]

        return settings

    def get_text_overlays(self) -> Dict[str, Any]:
        """Get text overlay configurations"""
        return self.get('text_overlays', {})

    def get_special_images(self) -> Dict[str, Any]:
        """Get special image specifications"""
        return self.get('special_images', {})

    def get_color_grading_preset(self) -> str:
        """Get color grading preset name"""
        return self.get('style.color_grading.preset', 'warm')

    def get_paths(self) -> Dict[str, str]:
        """Get all path configurations"""
        return self.get('paths', {})

    def validate(self) -> List[str]:
        """
        Validate configuration

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required paths exist
        paths = self.get_paths()

        if not paths:
            errors.append("No paths configuration found")
            return errors

        required_paths = ['images_dir', 'audio_dir', 'output_file']
        for path_key in required_paths:
            if path_key not in paths:
                errors.append(f"Missing required path: {path_key}")

        # Verify directories exist
        if 'images_dir' in paths:
            images_dir = Path(paths['images_dir'])
            if not images_dir.exists():
                errors.append(f"Images directory does not exist: {images_dir}")

        if 'audio_dir' in paths:
            audio_dir = Path(paths['audio_dir'])
            if not audio_dir.exists():
                errors.append(f"Audio directory does not exist: {audio_dir}")

        # Verify special image exists if specified
        special_images = self.get_special_images()
        if 'opening_closing' in special_images and 'images_dir' in paths:
            special_file = Path(paths['images_dir']) / special_images['opening_closing']
            if not special_file.exists():
                errors.append(f"Special image not found: {special_file}")

        # Validate transition weights sum to 1.0
        weights = self.get_transition_weights()
        weight_sum = sum(weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            errors.append(f"Transition weights must sum to 1.0, got {weight_sum}")

        # Validate timing values are positive
        timing = self.get_timing_settings()
        for key, value in timing.items():
            if value <= 0:
                errors.append(f"Timing value must be positive: {key} = {value}")

        # Validate text overlay fonts exist if text is enabled
        text_overlays = self.get_text_overlays()
        for section_name, section_config in text_overlays.items():
            if section_config.get('enabled', True):
                for text_key in ['main', 'subtitles']:
                    if text_key in section_config:
                        text_config = section_config[text_key]
                        if isinstance(text_config, dict) and 'font' in text_config:
                            font_path = Path(text_config['font'])
                            if not font_path.exists():
                                errors.append(f"Font file not found: {font_path} (in {section_name}.{text_key})")

        return errors
