# -*- coding: utf-8 -*-
"""
Color Grading Module for Slideshow Generator
Apply consistent color correction and artistic grading
"""

import logging
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class ColorGradeConfig:
    """Configuration for color grading"""
    brightness: float = 0.0  # -1.0 to 1.0
    contrast: float = 1.0    # 0.0 to 3.0
    saturation: float = 1.0  # 0.0 to 3.0
    gamma: float = 1.0       # 0.1 to 10.0
    warm_shift: float = 0.0  # -1.0 to 1.0
    vignette: bool = True
    film_grain: bool = False
    grain_strength: float = 0.01


# Presets for different moods
PRESET_WARM = ColorGradeConfig(
    brightness=0.02,
    contrast=1.05,
    saturation=1.1,
    gamma=1.0,
    warm_shift=0.03,
    vignette=True,
    film_grain=False
)

PRESET_VIBRANT = ColorGradeConfig(
    brightness=0.03,
    contrast=1.08,
    saturation=1.15,
    gamma=0.98,
    warm_shift=0.0,
    vignette=False,
    film_grain=False
)

PRESET_SOFT = ColorGradeConfig(
    brightness=0.01,
    contrast=0.98,
    saturation=0.95,
    gamma=1.02,
    warm_shift=0.02,
    vignette=True,
    film_grain=True,
    grain_strength=0.005
)

PRESET_NEUTRAL = ColorGradeConfig()


class ColorGrader:
    """Apply color grading to images"""

    def __init__(self, preset: str = "warm",
                 logger: Optional[logging.Logger] = None):
        """
        Initialize color grader

        Args:
            preset: Preset name (warm, vibrant, soft, neutral)
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Select preset
        presets = {
            "warm": PRESET_WARM,
            "vibrant": PRESET_VIBRANT,
            "soft": PRESET_SOFT,
            "neutral": PRESET_NEUTRAL,
        }

        self.config = presets.get(preset, PRESET_WARM)
        self.logger.info(f"Color grading preset: {preset}")
        self._log_config()

    def _log_config(self) -> None:
        """Log color grading configuration"""
        self.logger.debug(f"Brightness: {self.config.brightness:+.2f}")
        self.logger.debug(f"Contrast: {self.config.contrast:.2f}")
        self.logger.debug(f"Saturation: {self.config.saturation:.2f}")
        self.logger.debug(f"Gamma: {self.config.gamma:.2f}")
        self.logger.debug(f"Warm shift: {self.config.warm_shift:+.3f}")
        self.logger.debug(f"Vignette: {self.config.vignette}")
        self.logger.debug(f"Film grain: {self.config.film_grain}")

    def create_filter_chain(self, input_label: str = "0:v") -> List[str]:
        """
        Create filter chain for color grading

        Args:
            input_label: Input video stream label

        Returns:
            List of filter strings
        """
        filters = []

        # Exposure and contrast adjustment using eq filter
        if (self.config.brightness != 0.0 or
            self.config.contrast != 1.0 or
            self.config.gamma != 1.0 or
            self.config.saturation != 1.0):

            eq_params = []

            if self.config.brightness != 0.0:
                eq_params.append(f"brightness={self.config.brightness:.3f}")

            if self.config.contrast != 1.0:
                eq_params.append(f"contrast={self.config.contrast:.3f}")

            if self.config.gamma != 1.0:
                eq_params.append(f"gamma={self.config.gamma:.3f}")

            if self.config.saturation != 1.0:
                eq_params.append(f"saturation={self.config.saturation:.3f}")

            if eq_params:
                filters.append(f"eq={':'.join(eq_params)}")
                self.logger.debug(f"Added eq filter: {filters[-1]}")

        # Warm color shift (adjust hue toward warm tones)
        if self.config.warm_shift != 0.0:
            # Use colorbalance or hue filter for warm shift
            # Warm shift: increase reds/yellows, decrease blues
            hue_shift = self.config.warm_shift * 10  # Scale to appropriate range

            filters.append(f"hue=h={hue_shift:.2f}")
            self.logger.debug(f"Added hue adjustment: {hue_shift:.2f}")

        # Vignette effect
        if self.config.vignette:
            # Subtle vignette using vignette filter
            filters.append("vignette=angle=PI/4:mode=forward")
            self.logger.debug("Added vignette effect")

        # Film grain
        if self.config.film_grain:
            strength = int(self.config.grain_strength * 100)
            filters.append(f"noise=alls={strength}:allf=t")
            self.logger.debug(f"Added film grain: strength={strength}")

        return filters

    def apply_to_filter_chain(self, base_filter: str) -> str:
        """
        Apply color grading to existing filter chain

        Args:
            base_filter: Base filter string

        Returns:
            Enhanced filter string with color grading
        """
        color_filters = self.create_filter_chain()

        if not color_filters:
            return base_filter

        # Append color filters
        combined = base_filter + "," + ",".join(color_filters)

        return combined


def create_color_correction_filter(brightness: float = 0.0,
                                   contrast: float = 1.0,
                                   saturation: float = 1.0) -> str:
    """
    Create simple color correction filter

    Args:
        brightness: Brightness adjustment (-1.0 to 1.0)
        contrast: Contrast multiplier (0.0 to 3.0)
        saturation: Saturation multiplier (0.0 to 3.0)

    Returns:
        FFmpeg eq filter string
    """
    params = []

    if brightness != 0.0:
        params.append(f"brightness={brightness:.3f}")

    if contrast != 1.0:
        params.append(f"contrast={contrast:.3f}")

    if saturation != 1.0:
        params.append(f"saturation={saturation:.3f}")

    if params:
        return f"eq={':'.join(params)}"

    return ""


def create_vignette_filter(intensity: str = "PI/4") -> str:
    """
    Create vignette effect filter

    Args:
        intensity: Vignette intensity (FFmpeg angle expression)

    Returns:
        FFmpeg vignette filter string
    """
    return f"vignette=angle={intensity}:mode=forward"


def normalize_exposure(images: List[str],
                       logger: Optional[logging.Logger] = None) -> dict:
    """
    Analyze images and suggest normalization parameters
    (Placeholder for future implementation with actual image analysis)

    Args:
        images: List of image paths
        logger: Optional logger instance

    Returns:
        Dictionary with suggested adjustments
    """
    if logger:
        logger.debug("Exposure normalization analysis (placeholder)")

    # Return neutral adjustments for now
    return {
        "brightness": 0.0,
        "contrast": 1.0,
        "gamma": 1.0
    }
