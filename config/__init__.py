"""
Configuration module for slideshow generator
"""

from .base_config import (
    VIDEO_DEFAULTS,
    EFFECT_DEFAULTS,
    TRANSITION_WEIGHTS,
    COLOR_GRADING_PRESETS,
    TIMING_DEFAULTS,
    AUDIO_DEFAULTS
)
from .project_config import ProjectConfig

__all__ = [
    'VIDEO_DEFAULTS',
    'EFFECT_DEFAULTS',
    'TRANSITION_WEIGHTS',
    'COLOR_GRADING_PRESETS',
    'TIMING_DEFAULTS',
    'AUDIO_DEFAULTS',
    'ProjectConfig'
]
