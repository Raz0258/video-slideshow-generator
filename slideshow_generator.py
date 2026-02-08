#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Slideshow Generator Module - Segment-Based Version
Memory-efficient approach: renders one segment at a time
Handles unlimited images without memory issues
"""

import time
import shutil
from pathlib import Path
from typing import List

import utils
import ken_burns
import color_grading
from particle_overlay import ParticleOverlayGenerator, PIL_AVAILABLE
from timing_calculator import TimingCalculator
from sequence_builder import SequenceBuilder
from segment_renderer import SegmentRenderer, SegmentFilterBuilder
from config import ProjectConfig


class SlideshowGenerator:
    """Main slideshow generator class using segment-based rendering"""

    def __init__(self, project_config: ProjectConfig, logger):
        """
        Initialize slideshow generator with project configuration

        Args:
            project_config: ProjectConfig instance with all settings
            logger: Logger instance
        """
        self.project_config = project_config
        self.logger = logger

        # Get configuration settings
        video_settings = project_config.get_video_settings()
        effect_settings = project_config.get_effect_settings()
        audio_settings = project_config.get_audio_settings()

        # Extract video settings
        self.resolution = tuple(video_settings['resolution'])
        self.fps = video_settings['fps']
        self.crf = video_settings['crf']
        self.preset = video_settings['preset']

        # Extract effect settings
        self.transition_duration = effect_settings['transition_duration']

        # Extract audio settings
        self.audio_fade_in = audio_settings['fade_in']
        self.audio_fade_out = audio_settings['fade_out']

        # Initialize modules with configuration
        kb_config = effect_settings.get('ken_burns', {})
        self.kb_generator = ken_burns.KenBurnsGenerator(
            effect_config=kb_config,
            logger=logger
        )

        color_preset = project_config.get_color_grading_preset()
        self.grader = color_grading.ColorGrader(preset=color_preset, logger=logger)
        
        # Initialize segment renderer
        self.segment_renderer = SegmentRenderer(video_settings, logger)

        # Initialize particle overlay generator
        particle_settings = project_config.get_particle_settings()
        self.particle_generator = ParticleOverlayGenerator(
            particle_settings, self.resolution, self.fps, logger
        )
        if particle_settings.get('enabled') and not PIL_AVAILABLE:
            logger.warning("Particle overlays enabled but Pillow not installed. "
                           "Install with: pip install Pillow")
        
    def generate(self, images: List[str], audio_file: str, output_file: str) -> bool:
        """
        Generate slideshow video using segment-based approach
        
        Args:
            images: List of image file paths
            audio_file: Path to audio file
            output_file: Output video file path
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        sequence_builder = None
        temp_dir = None
        
        try:
            # Get audio duration
            audio_duration = utils.get_audio_duration(audio_file, self.logger)
            self.logger.info(f"Audio duration: {audio_duration:.1f}s")
            
            # Validate all images first
            self.logger.info("Validating images...")
            valid_images, invalid_images = utils.validate_all_images(images, self.logger)
            
            if len(valid_images) < 2:
                self.logger.error(f"Only {len(valid_images)} valid images (need at least 2)")
                print(f"[!] Only {len(valid_images)} valid images found (need at least 2)")
                return False
            
            if invalid_images:
                self.logger.warning(f"Skipping {len(invalid_images)} corrupted images:")
                for invalid in invalid_images:
                    self.logger.warning(f"  - {Path(invalid).name}")
            
            images = valid_images
            
            # Find and process special photo
            special_photo = self._find_special_photo(images)
            regular_images = self._filter_regular_images(images, special_photo)

            # Calculate timings
            timing_config = self.project_config.get_timing_settings()
            timing_calc = TimingCalculator(audio_duration, timing_config, self.logger)
            timings = timing_calc.calculate_timings(len(regular_images))
            
            # Build metadata
            metadata_list = self._build_metadata(
                regular_images, 
                timing_calc.get_image_durations(len(regular_images))
            )
            
            # Save metadata for debugging
            utils.save_metadata(metadata_list, output_file)
            
            # Create temp directory for segments
            temp_dir = Path(output_file).parent / 'temp_segments'
            temp_dir.mkdir(exist_ok=True)
            self.logger.info(f"Using temp directory: {temp_dir}")

            # Overlay video cache: maps cache_key -> overlay file path
            overlay_cache = {}

            # Render all segments
            segments = []
            
            # Initialize sequence builder
            text_config = self.project_config.get_text_overlays()
            sequence_builder = SequenceBuilder(
                self.resolution, self.fps, text_config, self.logger
            )
            
            # 1. Render opening part 1
            self.logger.info("=" * 60)
            self.logger.info("RENDERING SEGMENTS")
            self.logger.info("=" * 60)
            
            opening1_file = temp_dir / 'seg_000_opening1.mp4'
            opening1_filter, _ = sequence_builder.create_opening_part1(0, timings['opening_part1'])
            # Fix filter to use [0:v] input and [out] output for segment rendering
            opening1_filter = opening1_filter.replace('[0:v]', '[0:v]').replace('[opening_part1]', '[out]')

            # No particles on opening 1 (brief intro segment)
            opening1_overlay = None

            if self.segment_renderer.render_segment(
                'Opening-1', special_photo, timings['opening_part1'],
                opening1_filter, str(opening1_file),
                overlay_path=opening1_overlay
            ):
                segments.append(str(opening1_file))
            else:
                self.logger.error("Failed to render opening part 1")
                return False

            # 2. Render opening part 2
            opening2_file = temp_dir / 'seg_001_opening2.mp4'
            opening2_filter, _ = sequence_builder.create_opening_part2(0, timings['opening_part2'])
            # Fix filter to use [0:v] input and [out] output
            opening2_filter = opening2_filter.replace('[0:v]', '[0:v]').replace('[opening_part2]', '[out]')

            # Particle overlay for opening 2: particles at tail only (bridge to first image)
            opening2_overlay = None
            if self.particle_generator.enabled and self.particle_generator.apply_to_opening:
                opening2_overlay = self._get_transition_overlay(
                    timings['opening_part2'], 'opening', overlay_cache, temp_dir)

            if self.segment_renderer.render_segment(
                'Opening-2', special_photo, timings['opening_part2'],
                opening2_filter, str(opening2_file),
                overlay_path=opening2_overlay
            ):
                segments.append(str(opening2_file))
            else:
                self.logger.error("Failed to render opening part 2")
                return False
            
            # 3. Render each regular image as a segment
            filter_builder = SegmentFilterBuilder(self.resolution, self.fps, self.logger)

            for i, meta in enumerate(metadata_list, start=1):
                seg_file = temp_dir / f'seg_{i+1:03d}_image{i}.mp4'

                # Build filter for this image
                img_filter = filter_builder.build_image_filter(meta, self.kb_generator, self.grader)

                # Transition-only particle overlay (particles at start/end of segment)
                img_overlay = None
                if self.particle_generator.should_apply():
                    img_overlay = self._get_transition_overlay(
                        meta.duration, 'middle', overlay_cache, temp_dir)

                if self.segment_renderer.render_segment(
                    f'Image-{i}', meta.path, meta.duration,
                    img_filter, str(seg_file),
                    overlay_path=img_overlay
                ):
                    segments.append(str(seg_file))
                else:
                    self.logger.error(f"Failed to render image {i}")
                    return False
            
            # 4. Render closing segment
            closing_file = temp_dir / f'seg_{len(segments):03d}_closing.mp4'
            closing_filter, _ = sequence_builder.create_closing_sequence(0, timings['closing'])
            # Fix filter to use [0:v] input and [out] output
            closing_filter = closing_filter.replace('[0:v]', '[0:v]').replace('[closing]', '[out]')

            # Particle overlay for closing: particles at head only (bridge from last image)
            closing_overlay = None
            if self.particle_generator.enabled and self.particle_generator.apply_to_closing:
                closing_overlay = self._get_transition_overlay(
                    timings['closing'], 'closing', overlay_cache, temp_dir)

            if self.segment_renderer.render_segment(
                'Closing', special_photo, timings['closing'],
                closing_filter, str(closing_file),
                overlay_path=closing_overlay
            ):
                segments.append(str(closing_file))
            else:
                self.logger.error("Failed to render closing segment")
                return False
            
            # 5. Concatenate all segments with audio
            self.logger.info("=" * 60)
            self.logger.info("FINALIZING VIDEO")
            self.logger.info("=" * 60)
            
            success = self.segment_renderer.concatenate_segments(
                segments, audio_file, output_file,
                self.audio_fade_in, self.audio_fade_out
            )
            
            if success:
                # Log summaries
                self.kb_generator.log_summary()
                
                # Print summary
                elapsed = time.time() - start_time
                utils.print_summary(
                    len(images), audio_file, output_file,
                    audio_duration, elapsed, self.logger
                )
            
            return success
            
        except Exception as e:
            self.logger.exception(f"Error generating slideshow: {e}")
            return False
            
        finally:
            # Clean up temporary text files
            if sequence_builder:
                sequence_builder.cleanup_temp_files()
            
            # Clean up temp segments directory
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    self.logger.info("Cleaned up temporary segments")
                except Exception as e:
                    self.logger.warning(f"Could not clean up temp directory: {e}")
    
    def _get_transition_overlay(self, duration: float, segment_position: str,
                                overlay_cache: dict, temp_dir: Path):
        """
        Generate a particle overlay with transition-only active windows.

        Args:
            duration: Full segment duration in seconds
            segment_position: 'middle' (both ends), 'opening' (tail only), 'closing' (head only)
            overlay_cache: Cache dict mapping cache_key -> overlay file path
            temp_dir: Temp directory for overlay files

        Returns:
            Path to overlay file, or None if generation failed
        """
        td = self.transition_duration

        # Compute active windows based on segment position
        if segment_position == 'opening':
            # Opening: particles at the tail (bridging to first image)
            active_windows = [(max(0, duration - td), duration)]
        elif segment_position == 'closing':
            # Closing: particles at the head (bridging from last image)
            active_windows = [(0, min(td, duration))]
        else:
            # Middle (all image segments): particles at both ends
            if duration <= 2 * td:
                # Short segment: split evenly to avoid overlap
                mid = duration / 2
                active_windows = [(0, mid), (mid, duration)]
            else:
                active_windows = [(0, td), (duration - td, duration)]

        # Randomize type per transition if in random mode
        if self.particle_generator.is_random_mode:
            self.particle_generator.randomize_type()

        # Check cache
        cache_key = self.particle_generator.get_cache_key(duration, active_windows)
        if cache_key in overlay_cache:
            return overlay_cache[cache_key]

        # Generate overlay
        overlay_file = str(temp_dir / f'overlay_{cache_key}.mov')
        if self.particle_generator.generate_overlay_video(duration, overlay_file, active_windows):
            overlay_cache[cache_key] = overlay_file
            return overlay_file

        return None

    def _find_special_photo(self, images: List[str]) -> str:
        """Find the special family photo from configuration"""
        special_images = self.project_config.get_special_images()
        special_filename = special_images.get('opening_closing')

        if not special_filename:
            self.logger.warning("No special photo specified in config, using first image")
            return images[0]

        special_photo = utils.find_image_by_name(
            images, special_filename, self.logger
        )

        if not special_photo:
            self.logger.warning(
                f"Special photo '{special_filename}' not found! "
                f"Using first image as fallback: {Path(images[0]).name}"
            )
            return images[0]

        self.logger.info(f"Special photo: {Path(special_photo).name}")
        return special_photo
    
    def _filter_regular_images(self, images: List[str], special_photo: str) -> List[str]:
        """Remove special photo from regular images list"""
        special_photo_abs = str(Path(special_photo).resolve()).lower()
        regular_images = []
        removed_count = 0
        
        for img in images:
            img_abs = str(Path(img).resolve()).lower()
            if img_abs == special_photo_abs:
                removed_count += 1
                self.logger.debug(
                    f"Removing special photo from regular images: {Path(img).name}"
                )
            else:
                regular_images.append(img)
        
        self.logger.info(f"Total images: {len(images)}")
        self.logger.info(f"Regular images: {len(regular_images)}")
        self.logger.info(f"Removed {removed_count} occurrence(s) of special photo")
        
        return regular_images
    
    def _build_metadata(self, images: List[str], durations: List[float]) -> List[utils.ImageMetadata]:
        """Build metadata for all regular images"""
        self.logger.info("Analyzing images...")
        metadata_list = []
        
        for i, img_path in enumerate(images):
            width, height = utils.get_image_dimensions(img_path, self.logger)
            is_portrait = height > width
            duration = durations[i]
            
            # Generate Ken Burns effect
            kb_config = self.kb_generator.generate_effect(is_portrait)
            
            metadata = utils.ImageMetadata(
                path=img_path,
                index=i,
                width=width,
                height=height,
                is_portrait=is_portrait,
                duration=duration,
                use_ken_burns=kb_config is not None,
                ken_burns_type=kb_config
            )
            
            metadata_list.append(metadata)
        
        return metadata_list