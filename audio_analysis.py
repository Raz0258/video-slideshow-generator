# -*- coding: utf-8 -*-
"""
Audio Analysis Module for Slideshow Generator
Optional beat detection and audio-synchronized transitions
"""

import logging
from typing import List, Optional, Tuple


class AudioAnalyzer:
    """Analyze audio for beat detection and pacing"""

    def __init__(self, audio_path: str, logger: Optional[logging.Logger] = None):
        """
        Initialize audio analyzer

        Args:
            audio_path: Path to audio file
            logger: Optional logger instance
        """
        self.audio_path = audio_path
        self.logger = logger or logging.getLogger(__name__)
        self.beats: List[float] = []
        self.beat_detection_available = self._check_dependencies()

    def _check_dependencies(self) -> bool:
        """
        Check if beat detection libraries are available

        Returns:
            True if dependencies available
        """
        try:
            import librosa
            self.logger.info("librosa available for beat detection")
            return True
        except ImportError:
            pass

        try:
            import aubio
            self.logger.info("aubio available for beat detection")
            return True
        except ImportError:
            pass

        self.logger.info("No beat detection library available (optional feature)")
        return False

    def detect_beats(self) -> bool:
        """
        Detect beats in audio file

        Returns:
            True if beats detected successfully
        """
        if not self.beat_detection_available:
            self.logger.debug("Skipping beat detection - no library available")
            return False

        try:
            self.logger.info("Attempting beat detection...")
            self.beats = self._detect_with_librosa()

            if self.beats:
                self.logger.info(f"Detected {len(self.beats)} beats")
                return True
            else:
                self.logger.warning("No beats detected")
                return False

        except Exception as e:
            self.logger.warning(f"Beat detection failed: {e}")
            return False

    def _detect_with_librosa(self) -> List[float]:
        """
        Detect beats using librosa

        Returns:
            List of beat timestamps in seconds
        """
        try:
            import librosa

            # Load audio
            y, sr = librosa.load(self.audio_path)

            # Detect beats
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

            # Convert frames to timestamps
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)

            self.logger.debug(f"Detected tempo: {tempo:.1f} BPM")

            return beat_times.tolist()

        except Exception as e:
            self.logger.error(f"librosa beat detection failed: {e}")
            return []

    def get_nearest_beat(self, timestamp: float, tolerance: float = 0.5) -> Optional[float]:
        """
        Find nearest beat to given timestamp

        Args:
            timestamp: Target timestamp in seconds
            tolerance: Maximum distance to beat in seconds

        Returns:
            Nearest beat timestamp or None
        """
        if not self.beats:
            return None

        # Find closest beat
        closest_beat = min(self.beats, key=lambda b: abs(b - timestamp))

        # Check if within tolerance
        if abs(closest_beat - timestamp) <= tolerance:
            return closest_beat

        return None

    def align_to_beats(self, timestamps: List[float],
                      tolerance: float = 0.5) -> List[float]:
        """
        Align timestamps to nearest beats

        Args:
            timestamps: List of timestamps to align
            tolerance: Maximum adjustment in seconds

        Returns:
            Aligned timestamps
        """
        if not self.beats:
            self.logger.debug("No beats available for alignment")
            return timestamps

        aligned = []
        aligned_count = 0

        for ts in timestamps:
            nearest = self.get_nearest_beat(ts, tolerance)

            if nearest is not None:
                aligned.append(nearest)
                aligned_count += 1
                self.logger.debug(f"Aligned {ts:.2f}s -> {nearest:.2f}s")
            else:
                aligned.append(ts)

        self.logger.info(
            f"Aligned {aligned_count}/{len(timestamps)} timestamps to beats"
        )

        return aligned


def calculate_smart_pacing(num_images: int, total_duration: float,
                          logger: Optional[logging.Logger] = None) -> List[float]:
    """
    Calculate variable pacing for images with natural feel

    Args:
        num_images: Number of images
        total_duration: Total video duration in seconds
        logger: Optional logger instance

    Returns:
        List of durations for each image
    """
    if logger:
        logger.info("Calculating smart pacing...")

    base_duration = total_duration / num_images
    durations = []

    for i in range(num_images):
        # Apply variation: ±10% randomly
        variation = (hash(i) % 21 - 10) / 100.0  # -0.10 to +0.10
        duration = base_duration * (1.0 + variation)

        # Add breathing room every 5-6 images
        if i > 0 and i % 5 == 0:
            duration += 0.3

        durations.append(duration)

    # Normalize to match exact total duration
    current_total = sum(durations)
    scale_factor = total_duration / current_total

    durations = [d * scale_factor for d in durations]

    if logger:
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)

        logger.info(f"Pacing - Avg: {avg_duration:.2f}s, "
                   f"Min: {min_duration:.2f}s, Max: {max_duration:.2f}s")
        logger.debug(f"Total duration: {sum(durations):.2f}s (target: {total_duration:.2f}s)")

    return durations


def calculate_transition_times(durations: List[float],
                               transition_duration: float) -> List[float]:
    """
    Calculate transition start times based on image durations

    Args:
        durations: List of image durations
        transition_duration: Duration of each transition

    Returns:
        List of transition offset times
    """
    offsets = []
    cumulative = 0.0

    for i, duration in enumerate(durations[:-1]):  # All but last
        cumulative += duration
        offset = cumulative - transition_duration
        offsets.append(offset)

    return offsets


def calculate_fixed_pacing(num_images: int, duration_per_image: float = 6.0,
                          logger: Optional[logging.Logger] = None) -> List[float]:
    """
    Calculate fixed pacing for all images (anniversary mode)

    Args:
        num_images: Number of images
        duration_per_image: Fixed duration for each image (default 6.0 seconds)
        logger: Optional logger instance

    Returns:
        List of durations (all identical)
    """
    if logger:
        logger.info(f"Using fixed pacing: {duration_per_image}s per image for {num_images} images")
        logger.info(f"Total images duration: {num_images * duration_per_image:.2f}s")

    return [duration_per_image] * num_images
