#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filter Builder Module
Builds FFmpeg filter chains for images and transitions
"""

from typing import List
from pathlib import Path
import utils
import transitions
import ken_burns
import color_grading


class FilterBuilder:
    """Builds FFmpeg filter chains for the slideshow"""
    
    def __init__(self, resolution: tuple, fps: int, transition_duration: float, logger):
        self.width, self.height = resolution
        self.fps = fps
        self.transition_duration = transition_duration
        self.logger = logger
        
    def build_image_filters(
        self,
        metadata_list: List[utils.ImageMetadata],
        kb_generator: ken_burns.KenBurnsGenerator,
        grader: color_grading.ColorGrader
    ) -> tuple:
        """
        Build filters for all images
        
        Args:
            metadata_list: List of image metadata
            kb_generator: Ken Burns effect generator
            grader: Color grading processor
            
        Returns:
            (filter_strings, output_labels)
        """
        filters = []
        labels = []
        
        for meta in metadata_list:
            self.logger.debug(f"Processing image {meta.index + 1}: {Path(meta.path).name}")
            
            # Build scale filter based on orientation and Ken Burns settings
            if meta.use_ken_burns and meta.ken_burns_type:
                scale_filter = self._build_ken_burns_filter(meta, kb_generator)
            else:
                scale_filter = self._build_static_filter(meta)
            
            # Apply color grading
            scale_filter = grader.apply_to_filter_chain(scale_filter)
            
            # Set framerate
            scale_filter += f",fps={self.fps},settb=1/{self.fps}"
            
            # Output label
            label = f"v{meta.index}"
            scale_filter += f"[{label}]"
            
            filters.append(scale_filter)
            labels.append(label)
        
        return filters, labels
    
    def _build_ken_burns_filter(
        self,
        meta: utils.ImageMetadata,
        kb_generator: ken_burns.KenBurnsGenerator
    ) -> str:
        """Build filter with Ken Burns effect"""
        kb_config = meta.ken_burns_type
        
        if meta.is_portrait:
            # Portrait: blur background + Ken Burns on foreground
            scale_filter = (
                f"[{meta.index}:v]split=2[blur{meta.index}][img{meta.index}];"
                f"[blur{meta.index}]scale={self.width}:{self.height}:"
                f"force_original_aspect_ratio=increase,"
                f"crop={self.width}:{self.height},gblur=sigma=20"
                f"[bg{meta.index}];"
                f"[img{meta.index}]scale={self.width}:{self.height}:"
                f"force_original_aspect_ratio=decrease"
                f"[fg{meta.index}];"
                f"[bg{meta.index}][fg{meta.index}]overlay=(W-w)/2:(H-h)/2"
            )
        else:
            # Landscape: simple scale with padding
            scale_filter = (
                f"[{meta.index}:v]scale={self.width}:{self.height}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black"
            )
        
        # Add Ken Burns effect
        kb_filter = ken_burns.create_ken_burns_filter(
            kb_config, meta.duration, self.fps,
            self.width, self.height
        )
        scale_filter += f",{kb_filter}"
        
        return scale_filter
    
    def _build_static_filter(self, meta: utils.ImageMetadata) -> str:
        """Build filter without Ken Burns effect"""
        if meta.is_portrait:
            # Portrait with blurred background
            scale_filter = (
                f"[{meta.index}:v]split=2[blur{meta.index}][img{meta.index}];"
                f"[blur{meta.index}]scale={self.width}:{self.height}:"
                f"force_original_aspect_ratio=increase,"
                f"crop={self.width}:{self.height},gblur=sigma=20"
                f"[bg{meta.index}];"
                f"[img{meta.index}]scale={self.width}:{self.height}:"
                f"force_original_aspect_ratio=decrease"
                f"[fg{meta.index}];"
                f"[bg{meta.index}][fg{meta.index}]overlay=(W-w)/2:(H-h)/2"
            )
        else:
            # Landscape with simple padding
            scale_filter = (
                f"[{meta.index}:v]scale={self.width}:{self.height}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black"
            )
        
        return scale_filter
    
    def build_transition_chain(
        self,
        labels: List[str],
        durations: List[float],
        transition_selector: transitions.TransitionSelector
    ) -> tuple:
        """
        Build transition chain between all segments

        Args:
            labels: List of segment labels
            durations: List[segment durations
            transition_selector: Transition effect selector

        Returns:
            (transition_filters, final_label)
        """
        trans_filters = []
        current_label = labels[0]

        cumulative_time = 0.0
        total_transitions = len(labels) - 1

        for i in range(total_transitions):
            # Add current segment duration to cumulative time
            cumulative_time += durations[i]

            # Calculate offset: transition starts transition_duration before segment end
            offset = cumulative_time - self.transition_duration

            # Select transition based on configuration weights
            transition = transition_selector.select_next()

            # Create filter
            next_label = f"t{i}"
            trans_filter = transitions.create_transition_filter(
                current_label, labels[i + 1],
                transition, self.transition_duration, offset
            )
            trans_filter += f"[{next_label}]"
            trans_filters.append(trans_filter)
            current_label = next_label

        return trans_filters, current_label
    
    def combine_filters(
        self,
        opening_filters: List[str],
        image_filters: List[str],
        closing_filter: str,
        transition_filters: List[str]
    ) -> str:
        """
        Combine all filters into final filter_complex string
        
        Args:
            opening_filters: Opening sequence filters
            image_filters: Regular image filters
            closing_filter: Closing sequence filter
            transition_filters: Transition filters
            
        Returns:
            Complete filter_complex string
        """
        all_filters = []
        all_filters.extend(opening_filters)
        all_filters.extend(image_filters)
        all_filters.append(closing_filter)
        all_filters.extend(transition_filters)
        
        return ";\n".join(all_filters)
    

class SegmentFilterBuilder:
    """Builds FFmpeg filters for individual video segments"""
    
    def __init__(self, resolution: tuple, fps: int, logger):
        self.width, self.height = resolution
        self.fps = fps
        self.logger = logger
    
    def build_image_filter(
        self,
        metadata: utils.ImageMetadata,
        kb_generator: ken_burns.KenBurnsGenerator,
        grader: color_grading.ColorGrader
    ) -> str:
        """
        Build filter for a single image segment
        
        Args:
            metadata: Image metadata
            kb_generator: Ken Burns effect generator
            grader: Color grading processor
            
        Returns:
            Complete filter string for this image
        """
        self.logger.debug(f"Building filter for: {Path(metadata.path).name}")
        
        # Input is always [0:v] for single-input segments
        input_label = "0:v"
        
        # Build scale filter based on orientation and Ken Burns
        if metadata.use_ken_burns and metadata.ken_burns_type:
            filter_str = self._build_ken_burns_filter(metadata, kb_generator, input_label)
        else:
            filter_str = self._build_static_filter(metadata, input_label)
        
        # Apply color grading
        filter_str = grader.apply_to_filter_chain(filter_str)
        
        # Set framerate and output
        filter_str += f",fps={self.fps},settb=1/{self.fps}[out]"
        
        return filter_str
    
    def _build_ken_burns_filter(
        self,
        meta: utils.ImageMetadata,
        kb_generator: ken_burns.KenBurnsGenerator,
        input_label: str
    ) -> str:
        """Build filter with Ken Burns effect"""
        kb_config = meta.ken_burns_type
        
        if meta.is_portrait:
            # Portrait: blur background + Ken Burns on foreground
            filter_str = (
                f"[{input_label}]format=yuv420p,split=2[blur][img];"
                f"[blur]scale={self.width}:{self.height}:"
                f"force_original_aspect_ratio=increase,"
                f"crop={self.width}:{self.height},gblur=sigma=20[bg];"
                f"[img]scale={self.width}:{self.height}:"
                f"force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
            )
        else:
            # Landscape: simple scale with padding
            filter_str = (
                f"[{input_label}]format=yuv420p,"
                f"scale={self.width}:{self.height}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black"
            )
        
        # Add Ken Burns effect
        kb_filter = ken_burns.create_ken_burns_filter(
            kb_config, meta.duration, self.fps,
            self.width, self.height
        )
        filter_str += f",{kb_filter}"
        
        return filter_str
    
    def _build_static_filter(self, meta: utils.ImageMetadata, input_label: str) -> str:
        """Build filter without Ken Burns effect"""
        if meta.is_portrait:
            # Portrait with blurred background
            filter_str = (
                f"[{input_label}]format=yuv420p,split=2[blur][img];"
                f"[blur]scale={self.width}:{self.height}:"
                f"force_original_aspect_ratio=increase,"
                f"crop={self.width}:{self.height},gblur=sigma=20[bg];"
                f"[img]scale={self.width}:{self.height}:"
                f"force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
            )
        else:
            # Landscape with simple padding
            filter_str = (
                f"[{input_label}]format=yuv420p,"
                f"scale={self.width}:{self.height}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black"
            )
        
        return filter_str