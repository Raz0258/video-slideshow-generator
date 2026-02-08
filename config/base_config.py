"""
Base configuration defaults for slideshow generator
These are sensible defaults that can be overridden by project configs
"""

# Video encoding settings
VIDEO_DEFAULTS = {
    'resolution': (1920, 1080),
    'fps': 30,
    'crf': 18,  # Quality: lower = better, 18 is visually lossless
    'preset': 'slow',  # Encoding speed vs compression: slow = better compression
}

# Visual effects settings
EFFECT_DEFAULTS = {
    'transition_duration': 0.9,  # Seconds of overlap between clips
    'ken_burns': {
        'application_rate': 0.65,  # Percentage of images that get Ken Burns effect
        'zoom_range': (1.0, 1.08),  # Min and max zoom levels
        'pan_amount': 0.06,  # How far to pan (as fraction of frame)
        'speed_variations': [0.7, 0.85, 1.0],  # Effect speed multipliers
    }
}

# Transition category weights (must sum to 1.0)
TRANSITION_WEIGHTS = {
    'gentle': 0.70,
    'dynamic': 0.20,
    'artistic': 0.10
}

# Color grading presets
COLOR_GRADING_PRESETS = {
    'warm': {
        'brightness': 0.02,
        'contrast': 1.05,
        'saturation': 1.10,
        'gamma': 1.00,
        'warm_shift': 0.030,
        'vignette': True,
        'film_grain': False
    },
    'vibrant': {
        'brightness': 0.03,
        'contrast': 1.08,
        'saturation': 1.15,
        'gamma': 1.00,
        'warm_shift': 0.015,
        'vignette': False,
        'film_grain': False
    },
    'soft': {
        'brightness': 0.05,
        'contrast': 0.98,
        'saturation': 1.05,
        'gamma': 1.05,
        'warm_shift': 0.020,
        'vignette': True,
        'film_grain': True
    },
    'neutral': {
        'brightness': 0.00,
        'contrast': 1.00,
        'saturation': 1.00,
        'gamma': 1.00,
        'warm_shift': 0.000,
        'vignette': False,
        'film_grain': False
    }
}

# Timing defaults
TIMING_DEFAULTS = {
    'opening_part1_duration': 3.0,  # Special photo only
    'opening_part2_duration': 6.0,  # Special photo + text
    'image_duration': 6.0,  # Duration per regular image
    'min_closing_duration': 8.0,  # Minimum closing sequence duration
}

# Audio settings
AUDIO_DEFAULTS = {
    'fade_in': 0.5,  # Seconds of fade in at start
    'fade_out': 1.5,  # Seconds of fade out at end
}

# Particle overlay settings
PARTICLE_OVERLAY_DEFAULTS = {
    'enabled': False,
    'type': 'random',           # hearts, sparkles, petals, confetti, random
    'size': 'medium',           # small, medium, large, extra_large
    'density': 0.5,             # 0.0 to 1.0, controls particle count
    'application_rate': 0.7,    # Fraction of transitions that get particle effects
    'apply_to_opening': True,
    'apply_to_closing': True,
}
