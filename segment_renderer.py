#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Segment Renderer Module
Renders individual video segments (opening, images, closing)
FIXED: Remove -t from input to let filter chain control duration
"""

import subprocess
import time
import json
from pathlib import Path
from typing import List, Optional
import logging
import ken_burns
import color_grading
import utils


class SegmentRenderer:
    """Renders video segments individually for memory-efficient processing"""
    
    def __init__(self, video_settings: dict, logger: logging.Logger):
        """
        Initialize segment renderer
        
        Args:
            video_settings: Video configuration (resolution, fps, crf, preset)
            logger: Logger instance
        """
        self.logger = logger
        self.resolution = tuple(video_settings['resolution'])
        self.fps = video_settings['fps']
        self.crf = video_settings['crf']
        self.preset = video_settings['preset']
        
    def render_segment(
        self,
        segment_name: str,
        input_file: str,
        duration: float,
        filter_str: str,
        output_file: str,
        show_progress: bool = True,
        overlay_path: str = None
    ) -> bool:
        """Render a single video segment with detailed logging"""

        # CRITICAL DEBUG: Log the exact duration being used
        self.logger.info(f"=" * 70)
        self.logger.info(f"RENDERING: {segment_name}")
        self.logger.info(f"  Input: {Path(input_file).name}")
        self.logger.info(f"  Duration: {duration:.2f} seconds")
        self.logger.info(f"  Expected frames: {int(duration * self.fps)} @ {self.fps}fps")
        self.logger.info(f"  Filter (first 200 chars): {filter_str[:200]}...")
        if overlay_path:
            self.logger.info(f"  Particle overlay: {Path(overlay_path).name}")
        self.logger.info(f"=" * 70)

        # If overlay video provided, add as second input and composite
        if overlay_path and Path(overlay_path).exists():
            filter_str = filter_str.replace('[out]', '[base]')
            filter_str += ';[1:v]format=rgba[ov];[base][ov]overlay=0:0:shortest=1[out]'

        # CRITICAL FIX: Remove -t from input, let filter chain control duration
        # The filter chain now includes trim=duration={duration} to cut precisely
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            # REMOVED: '-t', str(duration),  # Don't limit input duration
            '-i', input_file,
        ]

        # Add overlay video as second input if provided
        if overlay_path and Path(overlay_path).exists():
            cmd.extend(['-i', overlay_path])

        cmd.extend([
            '-filter_complex', filter_str,
            '-map', '[out]',
            '-c:v', 'libx264',
            '-preset', self.preset,
            '-crf', str(self.crf),
            '-pix_fmt', 'yuv420p',
            '-an',
            '-movflags', '+faststart',
            output_file
        ])
        
        # DEBUG: Log the complete FFmpeg command
        self.logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        try:
            start_time = time.time()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding='utf-8',
                errors='replace'
            )
            
            last_progress_time = time.time()
            frame_count = 0
            last_time_str = "00:00:00"
            
            for line in process.stdout:
                # Log all output at debug level
                self.logger.debug(f"FFmpeg: {line.rstrip()}")
                
                # Extract frame count and time from FFmpeg output
                if 'frame=' in line:
                    try:
                        # Parse frame number
                        frame_part = line.split('frame=')[1].split()[0]
                        frame_count = int(frame_part)
                        
                        # Parse time
                        if 'time=' in line:
                            time_part = line.split('time=')[1].split()[0]
                            last_time_str = time_part
                    except:
                        pass
                    
                    # Show progress every 2 seconds
                    if show_progress:
                        current_time = time.time()
                        if current_time - last_progress_time >= 2:
                            print(f"\r  {segment_name}: {line.strip()}", end='', flush=True)
                            last_progress_time = current_time
            
            process.wait()
            
            if show_progress:
                print()  # New line after progress
            
            elapsed = time.time() - start_time
            
            if process.returncode == 0:
                # Verify output file was created
                if Path(output_file).exists():
                    file_size = Path(output_file).stat().st_size / (1024 * 1024)
                    
                    # Get actual duration of rendered segment
                    actual_duration = self._get_duration(output_file)
                    
                    # CRITICAL VERIFICATION
                    expected_frames = int(duration * self.fps)
                    frame_diff = abs(frame_count - expected_frames)
                    duration_diff = abs(actual_duration - duration)
                    
                    self.logger.info(f"✓ {segment_name} completed in {elapsed:.1f}s")
                    self.logger.info(f"  File size: {file_size:.2f} MB")
                    self.logger.info(f"  Expected: {duration:.2f}s ({expected_frames} frames)")
                    self.logger.info(f"  Rendered: {actual_duration:.2f}s ({frame_count} frames)")
                    
                    if frame_diff > 10:
                        self.logger.error(f"  ❌ FRAME COUNT MISMATCH: {frame_diff} frames difference!")
                        self.logger.error(f"  This segment is {abs(actual_duration - duration):.1f}s {'longer' if actual_duration > duration else 'shorter'} than expected!")
                    elif duration_diff > 0.5:
                        self.logger.warning(f"  ⚠️  Duration difference: {duration_diff:.2f}s")
                    else:
                        self.logger.info(f"  ✓ Duration matches: ±{duration_diff:.2f}s")
                    
                    return True
                else:
                    self.logger.error(f"✗ {segment_name} output file not created")
                    return False
            else:
                self.logger.error(f"✗ {segment_name} failed with return code {process.returncode}")
                return False
                
        except Exception as e:
            self.logger.error(f"✗ {segment_name} exception: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def add_simple_fade_transition(
        self,
        segment1: str,
        segment2: str,
        output_file: str,
        fade_duration: float = 0.5
    ) -> bool:
        """
        Add a simple cross-fade transition between two segments
        
        Args:
            segment1: First segment path
            segment2: Second segment path
            output_file: Output merged segment path
            fade_duration: Fade duration in seconds
            
        Returns:
            True if successful
        """
        cmd = [
            'ffmpeg', '-y',
            '-i', segment1,
            '-i', segment2,
            '-filter_complex',
            f'[0:v][1:v]xfade=transition=fade:duration={fade_duration}:offset=-{fade_duration}[out]',
            '-map', '[out]',
            '-c:v', 'libx264',
            '-preset', self.preset,
            '-crf', str(self.crf),
            '-pix_fmt', 'yuv420p',
            '-an',
            '-movflags', '+faststart',
            output_file
        ]
        
        self.logger.debug(f"Adding fade transition: {Path(segment1).name} -> {Path(segment2).name}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                self.logger.debug("Transition added successfully")
                return True
            else:
                self.logger.warning(f"Transition failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Transition exception: {e}")
            return False
    
    def concatenate_segments(
        self,
        segments: List[str],
        audio_file: str,
        output_file: str,
        audio_fade_in: float = 1.0,
        audio_fade_out: float = 2.0
    ) -> bool:
        """
        Concatenate all video segments and add audio
        
        Args:
            segments: List of segment file paths
            audio_file: Audio file path
            output_file: Final output video path
            audio_fade_in: Audio fade in duration
            audio_fade_out: Audio fade out duration
            
        Returns:
            True if successful
        """
        if not segments:
            self.logger.error("No segments to concatenate")
            return False
        
        self.logger.info(f"Concatenating {len(segments)} segments...")
        
        # Create concat list file
        concat_list = Path(output_file).parent / 'concat_list.txt'
        
        try:
            with open(concat_list, 'w', encoding='utf-8') as f:
                for segment in segments:
                    # FFmpeg concat requires forward slashes and escaped special chars
                    segment_path = str(Path(segment).resolve()).replace('\\', '/')
                    f.write(f"file '{segment_path}'\n")
            
            # Get audio duration for fade out
            audio_duration = self._get_duration(audio_file)
            
            # Concatenate with audio
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_list),
                '-i', audio_file,
                '-c:v', 'copy',  # Copy video (already encoded)
                '-c:a', 'aac',
                '-b:a', '320k',
                '-af', f'afade=t=in:st=0:d={audio_fade_in},'
                       f'afade=t=out:st={audio_duration-audio_fade_out}:d={audio_fade_out}',
                '-shortest',
                '-movflags', '+faststart',
                output_file
            ]
            
            self.logger.info("Merging video segments with audio...")
            
            start_time = time.time()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding='utf-8',
                errors='replace'
            )
            
            last_progress_time = time.time()
            
            for line in process.stdout:
                self.logger.debug(f"FFmpeg: {line.rstrip()}")
                
                if 'time=' in line:
                    current_time = time.time()
                    if current_time - last_progress_time >= 3:
                        print(f"\r  Final merge: {line.strip()}", end='', flush=True)
                        last_progress_time = current_time
            
            process.wait()
            print()  # New line
            
            elapsed = time.time() - start_time
            
            if process.returncode == 0:
                if Path(output_file).exists():
                    file_size = Path(output_file).stat().st_size / (1024 * 1024)
                    self.logger.info(
                        f"✓ Final video created in {elapsed:.1f}s ({file_size:.2f} MB)"
                    )
                    return True
                else:
                    self.logger.error("Final output file not created")
                    return False
            else:
                self.logger.error(f"Concatenation failed with code {process.returncode}")
                return False
                
        except Exception as e:
            self.logger.error(f"Concatenation exception: {e}")
            return False
            
        finally:
            # Cleanup concat list
            if concat_list.exists():
                concat_list.unlink()
    
    def _get_duration(self, file_path: str) -> float:
        """Get media file duration using ffprobe"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            file_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return float(data['format']['duration'])
        except Exception as e:
            self.logger.warning(f"Could not get duration for {file_path}: {e}")
            return 0.0



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
        """Build filter without Ken Burns effect - includes trim for exact duration"""
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
        
        # Add trim to ensure exact duration for static images too
        filter_str += f",trim=duration={meta.duration}"
        
        return filter_str