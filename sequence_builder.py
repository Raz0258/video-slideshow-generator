#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sequence Builder Module
Creates opening and closing sequences with Hebrew text overlays
"""

import tempfile
from pathlib import Path


class SequenceBuilder:
    """Builds opening and closing sequences with text overlays"""

    def __init__(self, resolution: tuple, fps: int, text_config: dict, logger):
        """
        Initialize sequence builder with text overlay configuration

        Args:
            resolution: (width, height) tuple
            fps: Frames per second
            text_config: Text overlay configuration from ProjectConfig
            logger: Logger instance
        """
        self.width, self.height = resolution
        self.fps = fps
        self.text_config = text_config
        self.logger = logger

        # Track temporary text files for cleanup
        self.temp_text_files = []

    def create_text_file(self, text: str) -> str:
        """
        Create a temporary UTF-8 text file for FFmpeg textfile parameter
        This avoids Windows command-line Unicode issues

        Args:
            text: The text to write to file

        Returns:
            Path to the temporary text file (FFmpeg-escaped)
        """
        # Create temp file with UTF-8 encoding
        fd, temp_path = tempfile.mkstemp(suffix='.txt', text=True)
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(text)
            # Track for cleanup
            self.temp_text_files.append(temp_path)
            # Convert to forward slashes and escape colons for FFmpeg filter parameters
            # Use double backslash for Windows command-line escaping
            return temp_path.replace("\\", "/").replace(":", "\\\\:")
        finally:
            import os
            os.close(fd)

    def cleanup_temp_files(self):
        """Remove temporary text files"""
        import os
        for temp_file in self.temp_text_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to remove temp file {temp_file}: {e}")
        self.temp_text_files.clear()

    def create_opening_part1(self, input_index: int, duration: float) -> tuple:
        """
        Create opening sequence part 1: Special photo only (0-3s)
        FIXED: Added trim filter for exact duration
        
        Args:
            input_index: FFmpeg input index for the special photo
            duration: Duration in seconds
            
        Returns:
            (filter_string, output_label)
        """
        filter_str = (
            f"[{input_index}:v]"
            f"scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
            f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"trim=duration={duration},"  # ADDED: Ensure exact duration
            f"fps={self.fps},settb=1/{self.fps}"
        )
        
        output_label = "opening_part1"
        filter_str += f"[{output_label}]"
        
        self.logger.info(f"Created opening part 1 (special photo only): {duration}s")
        
        return filter_str, output_label
    
    def create_opening_part2(self, input_index: int, duration: float) -> tuple:
        """
        Create opening sequence part 2: Special photo + text overlay
        FIXED: Added trim filter for exact duration

        Args:
            input_index: FFmpeg input index for the special photo
            duration: Duration in seconds

        Returns:
            (filter_string, output_label)
        """
        opening_config = self.text_config.get('opening', {})

        if not opening_config.get('enabled', True):
            # No text overlay, just return scaled image with trim
            return self.create_opening_part1(input_index, duration)

        main_config = opening_config.get('main', {})

        # Get text and font settings from config
        main_text = main_config.get('text', 'Title')
        font_path = main_config.get('font', 'C:/Windows/Fonts/arial.ttf')
        fontsize = main_config.get('fontsize', 72)
        fontcolor = main_config.get('fontcolor', 'white')
        text_shaping = main_config.get('text_shaping', 1)

        # Position settings
        position = main_config.get('position', {})
        x_pos = position.get('x', '(w-text_w)/2')
        y_pos = position.get('y', '(h-text_h)/2')

        # Shadow settings
        shadow = main_config.get('shadow', {})
        shadow_color = shadow.get('color', 'black@0.6')
        shadow_x = shadow.get('x', 3)
        shadow_y = shadow.get('y', 3)

        # Fade effects
        effects = main_config.get('effects', {})
        fade_in = effects.get('fade_in', 0.5)
        fade_out = effects.get('fade_out', 0.5)

        # Create text file for text (avoids Windows Unicode issues)
        text_file_path = self.create_text_file(main_text)

        # Convert Windows path to FFmpeg format and escape colons
        font_path_escaped = font_path.replace("\\", "/").replace(":", "\\\\:")
        shadow_color_escaped = shadow_color.replace("@", "\\\\@")

        filter_str = (
            f"[{input_index}:v]"
            f"scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
            f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black,"

            # Add main text with fade effects
            f"drawtext="
            f"fontfile={font_path_escaped}:"
            f"textfile={text_file_path}:"
            f"fontsize={fontsize}:"
            f"fontcolor={fontcolor}:"
            f"x={x_pos}:"
            f"y={y_pos}:"
            f"shadowcolor={shadow_color_escaped}:"
            f"shadowx={shadow_x}:"
            f"shadowy={shadow_y}:"
            f"text_shaping={text_shaping}:"
            f"alpha=if(lt(t\\,{fade_in})\\,t/{fade_in}\\,if(lt(t\\,{duration-fade_out})\\,1\\,(1-(t-{duration-fade_out})/{fade_out}))),"
            f"trim=duration={duration},"  # ADDED: Ensure exact duration
            f"fps={self.fps},settb=1/{self.fps}"
        )

        output_label = "opening_part2"
        filter_str += f"[{output_label}]"

        self.logger.info(f"Created opening part 2 with text overlay: {duration}s")

        return filter_str, output_label
    
    def create_closing_sequence(self, input_index: int, duration: float) -> tuple:
        """
        Create closing sequence: Special photo + text overlay
        FIXED: Added trim filter for exact duration
        Shows main text and optional subtitles with fade effects

        Args:
            input_index: FFmpeg input index for the special photo
            duration: Duration in seconds

        Returns:
            (filter_string, output_label)
        """
        closing_config = self.text_config.get('closing', {})

        if not closing_config.get('enabled', True):
            # No text overlay, just return scaled image with trim
            filter_str = (
                f"[{input_index}:v]"
                f"scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
                f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black,"
                f"trim=duration={duration},"  # ADDED: Ensure exact duration
                f"fps={self.fps},settb=1/{self.fps}"
                f"[closing]"
            )
            return filter_str, "closing"

        # Get base position (percentage from top)
        base_position = closing_config.get('base_position', {})
        base_y_frac = base_position.get('y', 0.5)
        base_y = int(self.height * base_y_frac)

        # Start building filter
        filter_str = (
            f"[{input_index}:v]"
            f"scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
            f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black,"
        )

        # Add main text
        main_config = closing_config.get('main', {})
        if main_config:
            filter_str += self._build_text_overlay(
                main_config,
                base_y,
                duration
            )

        # Add subtitles
        subtitles = closing_config.get('subtitles', [])
        for subtitle_config in subtitles:
            filter_str += self._build_text_overlay(
                subtitle_config,
                base_y,
                duration
            )

        # Add trim filter and final filters
        filter_str += f"trim=duration={duration},"  # ADDED: Ensure exact duration
        filter_str += f"fps={self.fps},settb=1/{self.fps}[closing]"

        self.logger.info(f"Created closing sequence with text overlay: {duration:.1f}s")

        return filter_str, "closing"


    def _build_text_overlay(self, text_config: dict, base_y: int, duration: float) -> str:
        """
        Build a drawtext filter string from text configuration

        Args:
            text_config: Text configuration dictionary
            base_y: Base Y position (pixels)
            duration: Total duration for fade calculations

        Returns:
            FFmpeg drawtext filter string
        """
        # Get text and font settings
        text = text_config.get('text', '')
        if not text:
            return ""

        font_path = text_config.get('font', 'C:/Windows/Fonts/arial.ttf')
        fontsize = text_config.get('fontsize', 48)
        fontcolor = text_config.get('fontcolor', 'white')
        text_shaping = text_config.get('text_shaping', 1)  # Enable by default for RTL support

        # Position settings
        position = text_config.get('position', {})
        x_pos = position.get('x', '(w-text_w)/2')

        # Calculate Y position
        if 'y' in position:
            y_pos = position['y']
        elif 'y_offset' in position:
            y_offset = position['y_offset']
            y_pos = str(base_y + y_offset)
        else:
            y_pos = str(base_y)

        # Shadow settings
        shadow = text_config.get('shadow', {})
        shadow_color = shadow.get('color', 'black@0.6')
        shadow_x = shadow.get('x', 3)
        shadow_y = shadow.get('y', 3)

        # Fade effects
        effects = text_config.get('effects', {})
        fade_in = effects.get('fade_in', 1.0)
        fade_out = effects.get('fade_out', 1.5)
        fade_out_start = duration - fade_out

        # Create text file
        text_file_path = self.create_text_file(text)

        # Escape paths and colors
        font_path_escaped = font_path.replace("\\", "/").replace(":", "\\\\:")
        shadow_color_escaped = shadow_color.replace("@", "\\\\@")

        # Build drawtext filter
        drawtext = (
            f"drawtext="
            f"fontfile={font_path_escaped}:"
            f"textfile={text_file_path}:"
            f"fontsize={fontsize}:"
            f"fontcolor={fontcolor}:"
            f"x={x_pos}:"
            f"y={y_pos}:"
            f"shadowcolor={shadow_color_escaped}:"
            f"shadowx={shadow_x}:"
            f"shadowy={shadow_y}:"
            f"text_shaping={text_shaping}:"
            f"alpha=if(lt(t\\,{fade_in})\\,t/{fade_in}\\,"
            f"if(lt(t\\,{fade_out_start})\\,1\\,(1-(t-{fade_out_start})/{fade_out}))),"
        )

        return drawtext
    
    def escape_text_for_ffmpeg(self, text: str) -> str:
        """
        Escape special characters for FFmpeg drawtext filter
        FFmpeg requires specific escaping for command-line parsing

        Args:
            text: Original text

        Returns:
            Escaped text safe for FFmpeg
        """
        # For FFmpeg drawtext filter, escape special characters
        # Order matters: backslashes first, then other chars

        # 1. Escape backslashes FIRST (before anything else)
        text = text.replace("\\", "\\\\")

        # 2. Escape colons (parameter separators in FFmpeg filters)
        text = text.replace(":", "\\:")

        # 3. Escape commas (can cause parsing issues)
        text = text.replace(",", "\\,")

        # Don't use quotes - just return escaped text
        return text