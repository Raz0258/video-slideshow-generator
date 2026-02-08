# -*- coding: utf-8 -*-
"""
Transitions Module for Slideshow Generator
Intelligent transition selection and management
"""

import random
import logging
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class TransitionCategory(Enum):
    """Categories of transitions for weighted selection"""
    GENTLE = "gentle"
    DYNAMIC = "dynamic"
    ARTISTIC = "artistic"


@dataclass
class Transition:
    """Transition definition with metadata"""
    name: str
    category: TransitionCategory
    description: str


# Transition definitions organized by category
GENTLE_TRANSITIONS = [
    Transition("circlecrop", TransitionCategory.GENTLE, "Soft circular crop reveal"),
    Transition("circleclose", TransitionCategory.GENTLE, "Circular close transition"),
    Transition("circleopen", TransitionCategory.GENTLE, "Circular open transition"),
    Transition("fade", TransitionCategory.GENTLE, "Classic fade transition"),
    Transition("fadeblack", TransitionCategory.GENTLE, "Fade through black"),
    Transition("fadewhite", TransitionCategory.GENTLE, "Fade through white"),
    Transition("dissolve", TransitionCategory.GENTLE, "Smooth dissolve"),
    Transition("pixelize", TransitionCategory.GENTLE, "Subtle pixelize effect"),
    Transition("hblur", TransitionCategory.GENTLE, "Horizontal blur transition"),
    Transition("vdslice", TransitionCategory.GENTLE, "Vertical down slice transition"),
    Transition("fadegrays", TransitionCategory.GENTLE, "Fade to grayscale transition"),
    Transition("fadefast", TransitionCategory.GENTLE, "Fast fade transition"),
]

DYNAMIC_TRANSITIONS = [
    Transition("smoothleft", TransitionCategory.DYNAMIC, "Smooth left slide"),
    Transition("smoothright", TransitionCategory.DYNAMIC, "Smooth right slide"),
    Transition("smoothup", TransitionCategory.DYNAMIC, "Smooth upward slide"),
    Transition("smoothdown", TransitionCategory.DYNAMIC, "Smooth downward slide"),
    Transition("diagtl", TransitionCategory.DYNAMIC, "Diagonal top-left"),
    Transition("diagtr", TransitionCategory.DYNAMIC, "Diagonal top-right"),
    Transition("diagbl", TransitionCategory.DYNAMIC, "Diagonal bottom-left"),
    Transition("diagbr", TransitionCategory.DYNAMIC, "Diagonal bottom-right"),
    Transition("hlwind", TransitionCategory.DYNAMIC, "Horizontal left wind"),
    Transition("hrwind", TransitionCategory.DYNAMIC, "Horizontal right wind"),
]

ARTISTIC_TRANSITIONS = [
    Transition("radial", TransitionCategory.ARTISTIC, "Radial wipe transition"),
    Transition("zoomin", TransitionCategory.ARTISTIC, "Zoom in transition"),
    Transition("squeezeh", TransitionCategory.ARTISTIC, "Horizontal squeeze"),
    Transition("squeezev", TransitionCategory.ARTISTIC, "Vertical squeeze"),
]

class TransitionSelector:
    """Intelligent transition selector with history tracking"""

    def __init__(self, weights: dict, logger: Optional[logging.Logger] = None,
                 simple_mode: bool = False, anniversary_mode: bool = False):
        """
        Initialize transition selector with configurable weights

        Args:
            weights: Dictionary mapping category names to weights (e.g., {'gentle': 0.70, 'dynamic': 0.20, 'artistic': 0.10})
            logger: Optional logger instance
            simple_mode: If True, use only basic transitions
            anniversary_mode: If True, enable anniversary '50' overlays
        """
        self.logger = logger or logging.getLogger(__name__)
        self.simple_mode = simple_mode
        self.anniversary_mode = anniversary_mode
        self.history: List[str] = []
        self.category_history: List[TransitionCategory] = []
        self.same_category_count = 0

        # Anniversary overlay tracking
        self.overlay_history: List[bool] = []  # Track which transitions have overlays
        self.overlay_count = 0

        # Convert string-based weights to enum-based weights
        self.category_weights = {}
        for category_name, weight in weights.items():
            try:
                category = TransitionCategory(category_name.lower())
                self.category_weights[category] = weight
            except ValueError:
                self.logger.warning(f"Unknown transition category: {category_name}")

        # Use defaults if no valid weights provided
        if not self.category_weights:
            self.logger.warning("No valid transition weights, using defaults")
            self.category_weights = {
                TransitionCategory.GENTLE: 0.70,
                TransitionCategory.DYNAMIC: 0.20,
                TransitionCategory.ARTISTIC: 0.10,
            }

        # Build transition pool
        if simple_mode:
            self.transitions = GENTLE_TRANSITIONS[:6]  # Basic fades and dissolves
        else:
            self.transitions = (
                GENTLE_TRANSITIONS + DYNAMIC_TRANSITIONS + ARTISTIC_TRANSITIONS
            )

        self.logger.info(f"TransitionSelector initialized with {len(self.transitions)} transitions")
        self.logger.debug(f"Simple mode: {simple_mode}")
        if anniversary_mode:
            self.logger.info("Anniversary mode enabled: '50' overlays will be added to 20-30% of transitions")

    def select_next(self) -> Transition:
        """
        Select next transition using intelligent algorithm

        Returns:
            Selected Transition object
        """
        # Select category based on weights and history
        category = self._select_category()

        # Get transitions for this category
        category_transitions = [t for t in self.transitions if t.category == category]

        # Safety check: if no transitions in selected category, use all available
        if not category_transitions:
            category_transitions = self.transitions

        # Filter out recently used transitions
        available = [t for t in category_transitions if t.name not in self.history[-2:]]

        if not available:
            available = category_transitions

        # Select random transition from available pool
        transition = random.choice(available)

        # Update history
        self.history.append(transition.name)
        self.category_history.append(category)

        # Log selection
        self.logger.debug(
            f"Selected transition: {transition.name} ({transition.category.value}) - "
            f"{transition.description}"
        )

        return transition

    def _select_category(self) -> TransitionCategory:
        """
        Select transition category with intelligent weighting

        Returns:
            Selected TransitionCategory
        """
        # Check if we need to switch categories
        if len(self.category_history) >= 3:
            recent_categories = self.category_history[-3:]
            if len(set(recent_categories)) == 1:
                # Same category 3 times, force switch
                current_cat = recent_categories[0]
                available_cats = [cat for cat in TransitionCategory if cat != current_cat and cat in self.category_weights]
                weights = [self.category_weights[cat] for cat in available_cats]

                # Safety check: ensure weights are valid
                if not available_cats or not weights or sum(weights) == 0:
                    # Fallback: use equal weights for all categories except current
                    available_cats = [cat for cat in TransitionCategory if cat != current_cat]
                    if available_cats:
                        category = random.choice(available_cats)
                    else:
                        # Last resort: use any category
                        category = random.choice(list(TransitionCategory))
                else:
                    category = random.choices(available_cats, weights=weights)[0]

                self.logger.debug(f"Forcing category switch from {current_cat.value} to {category.value}")
                return category

        # Normal weighted selection
        categories = [cat for cat in TransitionCategory if cat in self.category_weights]
        weights = [self.category_weights[cat] for cat in categories]

        # Safety check: ensure weights are valid
        if not categories or not weights or sum(weights) == 0:
            # Fallback: use equal weights for all categories
            self.logger.warning("Invalid category weights detected, using equal distribution")
            category = random.choice(list(TransitionCategory))
        else:
            category = random.choices(categories, weights=weights)[0]

        return category

    def get_transition_name(self) -> str:
        """Get next transition name (convenience method)"""
        return self.select_next().name

    def get_statistics(self) -> dict:
        """Get statistics about transition usage"""
        total = len(self.history)
        if total == 0:
            return {}

        stats = {
            "total_transitions": total,
            "unique_transitions": len(set(self.history)),
            "category_distribution": {}
        }

        for category in TransitionCategory:
            count = self.category_history.count(category)
            percentage = (count / total) * 100
            stats["category_distribution"][category.value] = {
                "count": count,
                "percentage": percentage
            }

        return stats

    def should_add_anniversary_overlay(self, transition_index: int, total_transitions: int) -> bool:
        """
        Determine if this transition should have '50' overlay (20-30% of transitions)

        Args:
            transition_index: Current transition index
            total_transitions: Total number of transitions

        Returns:
            True if overlay should be added
        """
        # TEMPORARILY DISABLED due to FFmpeg filter parsing issues on Windows
        return False

        if not self.anniversary_mode:
            return False

        # Don't add overlay to consecutive transitions
        if self.overlay_history and self.overlay_history[-1]:
            self.overlay_history.append(False)
            self.logger.debug(f"Transition {transition_index}: Skipping overlay (previous had overlay)")
            return False

        # Calculate current percentage
        current_percentage = (self.overlay_count / max(len(self.overlay_history), 1)) * 100
        target_percentage = 25  # Aim for 25% (middle of 20-30%)

        # Use weighted random selection based on current percentage
        if current_percentage < target_percentage:
            # Need more overlays - higher probability
            probability = 0.35
        else:
            # Have enough overlays - lower probability
            probability = 0.15

        add_overlay = random.random() < probability

        self.overlay_history.append(add_overlay)
        if add_overlay:
            self.overlay_count += 1
            self.logger.info(f"Transition {transition_index}: Adding gold '50' overlay")
        else:
            self.logger.debug(f"Transition {transition_index}: No overlay")

        return add_overlay

    def log_summary(self) -> None:
        """Log summary of transition selections"""
        stats = self.get_statistics()

        if not stats:
            return

        self.logger.info("=== Transition Selection Summary ===")
        self.logger.info(f"Total transitions: {stats['total_transitions']}")
        self.logger.info(f"Unique transitions used: {stats['unique_transitions']}")

        for category, data in stats["category_distribution"].items():
            self.logger.info(
                f"{category.capitalize()}: {data['count']} ({data['percentage']:.1f}%)"
            )

        # Log anniversary overlay statistics
        if self.anniversary_mode and self.overlay_history:
            total = len(self.overlay_history)
            percentage = (self.overlay_count / total) * 100
            self.logger.info(f"Anniversary overlays: {self.overlay_count} out of {total} transitions ({percentage:.1f}%)")


def create_transition_filter(from_label: str, to_label: str,
                            transition: Transition, duration: float,
                            offset: float) -> str:
    """
    Create FFmpeg filter string for transition

    Args:
        from_label: Source video label
        to_label: Destination video label
        transition: Transition object
        duration: Transition duration in seconds
        offset: Offset time for transition

    Returns:
        FFmpeg filter string
    """
    return (
        f"[{from_label}][{to_label}]xfade="
        f"transition={transition.name}:"
        f"duration={duration}:"
        f"offset={offset}"
    )


def create_anniversary_overlay_filter(duration: float = 0.9) -> str:
    """
    Create gold '50' text overlay with fade in/out for anniversary slideshow

    Args:
        duration: Transition duration in seconds (default 0.9s)

    Returns:
        FFmpeg drawtext filter string for '50' overlay
    """
    # Animation timing within the transition:
    # 0.0-0.3s: fade in (alpha 0→1)
    # 0.3-0.6s: hold at full opacity
    # 0.6-0.9s: fade out (alpha 1→0)

    fade_in_end = duration * 0.33  # 0.3s for 0.9s transition
    hold_end = duration * 0.67     # 0.6s for 0.9s transition

    # Gold '50' text with shadow for readability
    # NOTE: Simplified to avoid parsing issues on Windows FFmpeg
    filter_str = (
        f"drawtext="
        f"text=50:"  # No quotes around number
        f"fontfile=C:/Windows/Fonts/arial.ttf:"  # Windows path with forward slashes
        f"fontsize=120:"
        f"fontcolor=gold:"  # Using named color instead of hex
        f"x=(w-text_w)/2:"  # Center horizontally
        f"y=(h-text_h)/2"  # Center vertically - no trailing colon
    )

    return filter_str


def get_simple_transitions() -> List[str]:
    """Get list of simple transition names for basic mode"""
    return [t.name for t in GENTLE_TRANSITIONS[:6]]
