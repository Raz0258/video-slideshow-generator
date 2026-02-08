# -*- coding: utf-8 -*-
"""
Ken Burns Effect Module for Slideshow Generator
Advanced pan and zoom effects with easing
FIXED: Proper duration control using trim filter instead of relying on zoompan 'd' parameter
"""

import random
import math
import logging
from typing import Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class KenBurnsType(Enum):
    """Types of Ken Burns effects"""
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    PAN_UP = "pan_up"
    PAN_DOWN = "pan_down"
    DIAGONAL = "diagonal"


class EasingFunction(Enum):
    """Easing functions for smooth motion"""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"


@dataclass
class KenBurnsConfig:
    """Configuration for Ken Burns effect"""
    zoom_start: float
    zoom_end: float
    pan_x: float
    pan_y: float
    effect_type: KenBurnsType
    easing: EasingFunction
    speed_multiplier: float


class KenBurnsGenerator:
    """Generate Ken Burns effects with intelligent variation"""

    def __init__(self, effect_config: dict, logger: Optional[logging.Logger] = None):
        """
        Initialize Ken Burns generator with configuration

        Args:
            effect_config: Ken Burns configuration from ProjectConfig
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.stats = {effect.value: 0 for effect in KenBurnsType}
        self.stats["none"] = 0

        # Get configuration values
        self.application_rate = effect_config.get('application_rate', 0.65)
        self.zoom_range = tuple(effect_config.get('zoom_range', [1.0, 1.08]))
        self.pan_amount = effect_config.get('pan_amount', 0.06)
        self.speed_variations = effect_config.get('speed_variations', [0.7, 0.85, 1.0])

    def should_apply(self) -> bool:
        """
        Determine if Ken Burns should be applied to current image

        Returns:
            True if effect should be applied
        """
        return random.random() < self.application_rate

    def generate_effect(self, is_portrait: bool = False) -> Optional[KenBurnsConfig]:
        """
        Generate Ken Burns effect configuration

        Args:
            is_portrait: Whether the image is portrait orientation

        Returns:
            KenBurnsConfig or None if no effect
        """
        if not self.should_apply():
            self.stats["none"] += 1
            self.logger.debug("No Ken Burns effect applied")
            return None

        # Select effect type
        effect_type = self._select_effect_type(is_portrait)

        # Generate parameters based on effect type
        config = self._generate_config(effect_type)

        # Update statistics
        self.stats[effect_type.value] += 1

        self.logger.debug(
            f"Generated Ken Burns: {effect_type.value}, "
            f"zoom: {config.zoom_start:.3f}->{config.zoom_end:.3f}, "
            f"pan: ({config.pan_x:.3f}, {config.pan_y:.3f}), "
            f"easing: {config.easing.value}, "
            f"speed: {config.speed_multiplier:.2f}x"
        )

        return config

    def _select_effect_type(self, is_portrait: bool) -> KenBurnsType:
        """
        Select appropriate Ken Burns effect type

        Args:
            is_portrait: Whether image is portrait

        Returns:
            Selected KenBurnsType
        """
        # For portrait images, prefer vertical effects
        if is_portrait:
            effects = [
                KenBurnsType.ZOOM_IN,
                KenBurnsType.ZOOM_OUT,
                KenBurnsType.PAN_UP,
                KenBurnsType.PAN_DOWN,
            ]
            weights = [0.3, 0.3, 0.2, 0.2]
        else:
            effects = list(KenBurnsType)
            weights = [0.25, 0.25, 0.15, 0.15, 0.05, 0.05, 0.10]

        return random.choices(effects, weights=weights)[0]

    def _generate_config(self, effect_type: KenBurnsType) -> KenBurnsConfig:
        """
        Generate configuration for specific effect type

        Args:
            effect_type: Type of Ken Burns effect

        Returns:
            KenBurnsConfig object
        """
        zoom_min, zoom_max = self.zoom_range

        # Base configuration
        config = KenBurnsConfig(
            zoom_start=1.0,
            zoom_end=1.0,
            pan_x=0.0,
            pan_y=0.0,
            effect_type=effect_type,
            easing=self._select_easing(),
            speed_multiplier=random.choice(self.speed_variations)
        )

        # Adjust based on effect type
        if effect_type == KenBurnsType.ZOOM_IN:
            config.zoom_start = zoom_min
            config.zoom_end = zoom_max

        elif effect_type == KenBurnsType.ZOOM_OUT:
            config.zoom_start = zoom_max
            config.zoom_end = zoom_min

        elif effect_type == KenBurnsType.PAN_LEFT:
            config.zoom_start = zoom_min + 0.02
            config.zoom_end = zoom_min + 0.02
            config.pan_x = -self.pan_amount

        elif effect_type == KenBurnsType.PAN_RIGHT:
            config.zoom_start = zoom_min + 0.02
            config.zoom_end = zoom_min + 0.02
            config.pan_x = self.pan_amount

        elif effect_type == KenBurnsType.PAN_UP:
            config.zoom_start = zoom_min + 0.02
            config.zoom_end = zoom_min + 0.02
            config.pan_y = -self.pan_amount

        elif effect_type == KenBurnsType.PAN_DOWN:
            config.zoom_start = zoom_min + 0.02
            config.zoom_end = zoom_min + 0.02
            config.pan_y = self.pan_amount

        elif effect_type == KenBurnsType.DIAGONAL:
            config.zoom_start = zoom_min
            config.zoom_end = zoom_max
            config.pan_x = random.choice([-self.pan_amount * 0.5, self.pan_amount * 0.5])
            config.pan_y = random.choice([-self.pan_amount * 0.5, self.pan_amount * 0.5])

        return config

    def _select_easing(self) -> EasingFunction:
        """Select easing function with preference for smooth easing"""
        options = [
            EasingFunction.EASE_IN_OUT,
            EasingFunction.EASE_OUT,
            EasingFunction.EASE_IN,
            EasingFunction.LINEAR,
        ]
        weights = [0.5, 0.3, 0.15, 0.05]

        return random.choices(options, weights=weights)[0]

    def get_statistics(self) -> dict:
        """Get statistics about Ken Burns usage"""
        total = sum(self.stats.values())
        if total == 0:
            return {}

        return {
            "total_images": total,
            "effects_applied": total - self.stats["none"],
            "no_effect": self.stats["none"],
            "application_rate": ((total - self.stats["none"]) / total) * 100,
            "effect_distribution": {
                effect: count for effect, count in self.stats.items()
                if effect != "none" and count > 0
            }
        }

    def log_summary(self) -> None:
        """Log summary of Ken Burns usage"""
        stats = self.get_statistics()

        if not stats:
            return

        self.logger.info("=== Ken Burns Effect Summary ===")
        self.logger.info(f"Total images: {stats['total_images']}")
        self.logger.info(
            f"Effects applied: {stats['effects_applied']} "
            f"({stats['application_rate']:.1f}%)"
        )
        self.logger.info(f"No effect: {stats['no_effect']}")

        if stats["effect_distribution"]:
            self.logger.info("Effect distribution:")
            for effect, count in stats["effect_distribution"].items():
                self.logger.info(f"  {effect}: {count}")


def create_ken_burns_filter(config: KenBurnsConfig, duration: float,
                            fps: int, width: int, height: int) -> str:
    """
    Create FFmpeg zoompan filter string with proper duration control
    
    CRITICAL FIX: Use zoompan with d=1 (process each frame once) and trim to exact duration
    This prevents the zoompan filter from generating excessive frames

    Args:
        config: KenBurnsConfig object
        duration: Duration in seconds (ACTUAL segment duration)
        fps: Frames per second
        width: Video width
        height: Video height

    Returns:
        FFmpeg zoompan filter string
    """
    # Calculate exact number of frames needed
    total_frames = int(duration * fps)
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Ken Burns: duration={duration}s, fps={fps}, total_frames={total_frames}")
    logger.debug(f"Ken Burns config: zoom {config.zoom_start:.3f}->{config.zoom_end:.3f}, "
                f"pan ({config.pan_x:.3f}, {config.pan_y:.3f})")

    # Build zoom expression - uses 'on' which is the output frame counter
    zoom_expr = _create_zoom_expression(
        config.zoom_start, config.zoom_end,
        config.easing, total_frames
    )

    # Calculate pan positions - animate over the total frames
    pan_progress = f"min(on/{total_frames}, 1)"
    x_expr = f"iw/2-(iw/zoom/2)+({config.pan_x}*iw*{pan_progress})"
    y_expr = f"ih/2-(ih/zoom/2)+({config.pan_y}*ih*{pan_progress})"

    # CRITICAL FIX: Use d=1 to process each input frame once
    # Then use trim filter to cut to exact frame count
    # The zoompan filter will generate frames at the specified fps
    filter_str = (
        f"zoompan=z='{zoom_expr}'"
        f":x='{x_expr}':y='{y_expr}'"
        f":d=1"  # Process each input frame once (key fix!)
        f":s={width}x{height}"
        f":fps={fps},"
        f"trim=duration={duration}"  # Trim to exact duration
    )
    
    logger.debug(f"Ken Burns filter: zoompan d=1, trim to {duration}s ({total_frames} frames at {fps}fps)")

    return filter_str


def _create_zoom_expression(zoom_start: float, zoom_end: float,
                            easing: EasingFunction, total_frames: int) -> str:
    """
    Create zoom expression with easing function
    
    Uses 'on' which is the output frame number from zoompan filter

    Args:
        zoom_start: Starting zoom level
        zoom_end: Ending zoom level
        easing: Easing function to use
        total_frames: Total number of frames for progress calculation

    Returns:
        FFmpeg expression string
    """
    zoom_range = zoom_end - zoom_start
    
    # Progress through animation (0.0 to 1.0)
    # Using 'on' which is the output frame number
    # Clamp to ensure we never exceed 1.0
    progress = f"min(on/{total_frames}, 1)"

    if easing == EasingFunction.LINEAR:
        # Linear interpolation
        expr = f"{zoom_start}+{zoom_range}*({progress})"

    elif easing == EasingFunction.EASE_IN:
        # Quadratic ease in
        expr = f"{zoom_start}+{zoom_range}*pow({progress}, 2)"

    elif easing == EasingFunction.EASE_OUT:
        # Quadratic ease out
        expr = f"{zoom_start}+{zoom_range}*(1-pow(1-({progress}), 2))"

    elif easing == EasingFunction.EASE_IN_OUT:
        # Sine ease in-out (smooth)
        expr = f"{zoom_start}+{zoom_range}*((1-cos(({progress})*PI))/2)"

    return expr