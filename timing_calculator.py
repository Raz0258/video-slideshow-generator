#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Timing Calculator Module
Handles all duration calculations for the slideshow
"""

from typing import Tuple


class TimingCalculator:
    """Calculates and manages timing for all slideshow segments"""

    def __init__(self, audio_duration: float, timing_config: dict, logger):
        """
        Initialize timing calculator with configuration

        Args:
            audio_duration: Total audio duration in seconds
            timing_config: Timing configuration from ProjectConfig
            logger: Logger instance
        """
        self.audio_duration = audio_duration
        self.timing_config = timing_config
        self.logger = logger

        # Get durations from config - FIXED to match YAML structure
        self.OPENING_PART1_DURATION = timing_config.get('opening_part1_duration', 3.0)
        self.OPENING_PART2_DURATION = timing_config.get('opening_part2_duration', 6.0)
        
        # FIX: Support both old 'image_duration' and new 'duration_per_image' keys
        self.IMAGE_DURATION = timing_config.get('duration_per_image', 
                                                timing_config.get('image_duration', 6.0))
        
        self.MIN_CLOSING_DURATION = timing_config.get('min_closing_duration', 8.0)
        
        self.logger.debug(f"Timing config loaded: "
                         f"opening1={self.OPENING_PART1_DURATION}s, "
                         f"opening2={self.OPENING_PART2_DURATION}s, "
                         f"image={self.IMAGE_DURATION}s, "
                         f"closing_min={self.MIN_CLOSING_DURATION}s")
        
    def calculate_timings(self, num_regular_images: int) -> dict:
        """
        Calculate all timings for the slideshow
        
        Args:
            num_regular_images: Number of regular images (excluding special photo)
            
        Returns:
            Dictionary with all timing information
        """
        # Calculate regular images total time
        regular_images_total = num_regular_images * self.IMAGE_DURATION
        
        # Calculate closing duration (remaining time)
        closing_duration = (
            self.audio_duration 
            - self.OPENING_PART1_DURATION 
            - self.OPENING_PART2_DURATION 
            - regular_images_total
        )
        
        # Ensure minimum closing duration
        if closing_duration < self.MIN_CLOSING_DURATION:
            self.logger.warning(
                f"Calculated closing duration ({closing_duration:.1f}s) "
                f"is less than minimum ({self.MIN_CLOSING_DURATION}s)"
            )
            # Adjust by reducing regular image durations
            available_time = (
                self.audio_duration 
                - self.OPENING_PART1_DURATION 
                - self.OPENING_PART2_DURATION 
                - self.MIN_CLOSING_DURATION
            )
            
            if available_time > 0:
                adjusted_image_duration = available_time / num_regular_images
                self.IMAGE_DURATION = adjusted_image_duration
                regular_images_total = num_regular_images * self.IMAGE_DURATION
                closing_duration = self.MIN_CLOSING_DURATION
                
                self.logger.info(
                    f"Adjusted image duration to {self.IMAGE_DURATION:.2f}s "
                    f"to accommodate minimum closing duration"
                )
            else:
                self.logger.error(
                    "Cannot fit all segments within audio duration. "
                    "Consider using fewer images or longer audio."
                )
                closing_duration = self.MIN_CLOSING_DURATION
        
        # Calculate total video duration
        total_video_duration = (
            self.OPENING_PART1_DURATION 
            + self.OPENING_PART2_DURATION 
            + regular_images_total 
            + closing_duration
        )
        
        timings = {
            'opening_part1': self.OPENING_PART1_DURATION,
            'opening_part2': self.OPENING_PART2_DURATION,
            'image_duration': self.IMAGE_DURATION,
            'regular_images_total': regular_images_total,
            'closing': closing_duration,
            'total_video': total_video_duration,
            'num_images': num_regular_images
        }
        
        self.log_timing_breakdown(timings)
        
        return timings
    
    def log_timing_breakdown(self, timings: dict):
        """Log detailed timing breakdown"""
        self.logger.info("=" * 60)
        self.logger.info("TIMING BREAKDOWN:")
        self.logger.info(f"  Opening part 1 (special photo): {timings['opening_part1']:.1f}s")
        self.logger.info(f"  Opening part 2 (photo + text): {timings['opening_part2']:.1f}s")
        self.logger.info(
            f"  Regular images: {timings['num_images']} × {timings['image_duration']:.1f}s "
            f"= {timings['regular_images_total']:.1f}s"
        )
        self.logger.info(f"  Closing sequence (photo + text): {timings['closing']:.1f}s")
        self.logger.info(f"  TOTAL VIDEO: {timings['total_video']:.1f}s")
        self.logger.info(f"  Audio duration: {self.audio_duration:.1f}s")
        
        time_diff = abs(timings['total_video'] - self.audio_duration)
        if time_diff < 0.5:
            self.logger.info(f"  ✓ Video matches audio (±{time_diff:.2f}s)")
        else:
            self.logger.warning(f"  ⚠ Video differs from audio by {time_diff:.1f}s")
        
        self.logger.info("=" * 60)
    
    def get_image_durations(self, num_images: int) -> list:
        """
        Get list of durations for all regular images
        
        Args:
            num_images: Number of regular images
            
        Returns:
            List of durations (all equal to IMAGE_DURATION)
        """
        durations = [self.IMAGE_DURATION] * num_images
        
        self.logger.debug(f"Created {num_images} image durations, each {self.IMAGE_DURATION}s")
        self.logger.debug(f"Sample durations: {durations[:3]}")  # Log first 3 for verification
        
        return durations