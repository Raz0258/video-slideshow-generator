#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Particle Overlay Module
Generates transparent animated overlay videos with particle effects
(hearts, sparkles, petals, confetti) using PIL/Pillow and FFmpeg.
"""

import math
import random
import hashlib
import subprocess
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from pathlib import Path

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ParticleType(Enum):
    HEARTS = 'hearts'
    SPARKLES = 'sparkles'
    PETALS = 'petals'
    CONFETTI = 'confetti'
    RANDOM = 'random'

# Types available for random selection (excludes RANDOM itself)
CONCRETE_TYPES = [ParticleType.HEARTS, ParticleType.SPARKLES,
                  ParticleType.PETALS, ParticleType.CONFETTI]


# Default color palettes per particle type
DEFAULT_COLORS = {
    ParticleType.HEARTS: [
        (220, 20, 60),    # Crimson
        (255, 105, 180),  # Hot pink
        (255, 182, 193),  # Light pink
        (199, 21, 133),   # Medium violet red
    ],
    ParticleType.SPARKLES: [
        (255, 255, 224),  # Light yellow
        (255, 215, 0),    # Gold
        (255, 255, 255),  # White
        (255, 250, 205),  # Lemon chiffon
    ],
    ParticleType.PETALS: [
        (255, 182, 193),  # Light pink
        (255, 192, 203),  # Pink
        (255, 228, 225),  # Misty rose
        (219, 112, 147),  # Pale violet red
    ],
    ParticleType.CONFETTI: [
        (255, 50, 50),    # Red
        (50, 130, 255),   # Blue
        (255, 215, 0),    # Gold
        (50, 200, 50),    # Green
        (255, 105, 180),  # Pink
        (148, 0, 211),    # Violet
        (255, 165, 0),    # Orange
    ],
}


@dataclass
class Particle:
    """Represents a single animated particle"""
    x: float
    y: float
    size: float
    alpha: float              # 0.0 to 1.0 (current, may be modified by fading)
    rotation: float           # degrees
    speed_x: float
    speed_y: float
    color: Tuple[int, int, int]
    life: float               # frames remaining
    max_life: float           # starting life in frames
    rotation_speed: float = 0.0
    phase: float = 0.0        # for sine sway / pulse
    base_alpha: float = 0.0   # original alpha (for fade calculations)


class ParticleOverlayGenerator:
    """Generates transparent overlay videos with animated particle effects"""

    def __init__(self, overlay_config: dict, resolution: tuple,
                 fps: int, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.width, self.height = resolution
        self.fps = fps

        self.enabled = overlay_config.get('enabled', False)
        try:
            self.particle_type = ParticleType(overlay_config.get('type', 'hearts'))
        except ValueError:
            self.particle_type = ParticleType.HEARTS

        self._is_random_mode = (self.particle_type == ParticleType.RANDOM)

        self.density = max(0.0, min(1.0, float(overlay_config.get('density', 0.5))))
        self.application_rate = max(0.0, min(1.0, float(overlay_config.get('application_rate', 0.3))))
        self.apply_to_opening = overlay_config.get('apply_to_opening', True)
        self.apply_to_closing = overlay_config.get('apply_to_closing', True)

        # Size multiplier: extra_small=0.25, small=0.5, medium=1.0, large=1.5, extra_large=2.0
        size_map = {'extra_small': 0.25, 'small': 0.5, 'medium': 1.0, 'large': 1.5, 'extra_large': 2.0}
        self.size_multiplier = size_map.get(overlay_config.get('size', 'medium'), 1.0)

        # For random mode, start with hearts as placeholder; randomize_type() is called per transition
        if self._is_random_mode:
            self.colors = DEFAULT_COLORS[ParticleType.HEARTS]
        else:
            self.colors = DEFAULT_COLORS.get(self.particle_type, DEFAULT_COLORS[ParticleType.HEARTS])

        # Particle count scales with density: 15 at 0.0, 50 at 1.0
        self.particle_count = int(15 + self.density * 35)

        if self.enabled:
            size_label = {0.25: 'extra_small', 0.5: 'small', 1.0: 'medium', 1.5: 'large', 2.0: 'extra_large'}.get(
                self.size_multiplier, f'{self.size_multiplier}x')
            self.logger.info(f"Particle overlays: {self.particle_type.value}, "
                             f"density={self.density:.0%}, rate={self.application_rate:.0%}, "
                             f"size={size_label}, count={self.particle_count}")

    def should_apply(self) -> bool:
        """Check if particles should be applied to a transition (random per application_rate)"""
        if not self.enabled or not PIL_AVAILABLE:
            return False
        return random.random() < self.application_rate

    @property
    def is_random_mode(self) -> bool:
        """True when particle type is randomized per transition"""
        return self._is_random_mode

    def randomize_type(self) -> 'ParticleType':
        """Randomly select a concrete particle type. Called per transition in random mode."""
        self.particle_type = random.choice(CONCRETE_TYPES)
        self.colors = DEFAULT_COLORS[self.particle_type]
        self.logger.debug(f"Randomized particle type: {self.particle_type.value}")
        return self.particle_type

    def get_cache_key(self, duration: float,
                      active_windows: List[Tuple[float, float]] = None) -> str:
        """Generate cache key for overlay reuse based on settings + duration + windows"""
        windows_str = ""
        if active_windows:
            windows_str = "_".join(f"{s:.2f}-{e:.2f}" for s, e in active_windows)
        key_str = (f"{self.particle_type.value}_{self.density:.2f}_{self.size_multiplier:.1f}_"
                   f"{duration:.2f}_{self.width}x{self.height}_{windows_str}")
        return hashlib.md5(key_str.encode()).hexdigest()[:12]

    def generate_overlay_video(self, duration: float, output_path: str,
                               active_windows: List[Tuple[float, float]] = None) -> bool:
        """
        Generate a transparent overlay video with particle animations.

        Args:
            duration: Video duration in seconds
            output_path: Output .mov file path
            active_windows: List of (start_sec, end_sec) tuples where particles are visible.
                           If None, particles render for the entire duration.

        Returns:
            True if successful
        """
        if not PIL_AVAILABLE:
            self.logger.warning("Pillow not installed - skipping particle overlay")
            return False

        total_frames = int(duration * self.fps)
        if total_frames <= 0:
            return False

        # Compute frame-level active ranges
        if active_windows:
            active_frame_ranges = []
            for start_sec, end_sec in active_windows:
                start_frame = int(start_sec * self.fps)
                end_frame = int(end_sec * self.fps)
                active_frame_ranges.append((start_frame, min(end_frame, total_frames)))
            windows_desc = ", ".join(f"{s:.1f}-{e:.1f}s" for s, e in active_windows)
            self.logger.info(f"Generating {self.particle_type.value} overlay: "
                             f"{duration:.1f}s, windows=[{windows_desc}]")
        else:
            active_frame_ranges = None
            self.logger.info(f"Generating {self.particle_type.value} overlay: "
                             f"{duration:.1f}s, {total_frames} frames")

        try:
            # Start FFmpeg process to receive piped RGBA frames
            cmd = [
                'ffmpeg', '-y', '-loglevel', 'warning',
                '-f', 'rawvideo',
                '-pix_fmt', 'rgba',
                '-s', f'{self.width}x{self.height}',
                '-r', str(self.fps),
                '-i', 'pipe:0',
                '-c:v', 'png',
                '-pix_fmt', 'rgba',
                output_path
            ]

            process = subprocess.Popen(
                cmd, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Pre-compute transparent frame bytes (all zeros = fully transparent RGBA)
            transparent_bytes = b'\x00' * (self.width * self.height * 4)

            # Track which window we're in, re-init particles per window
            particles = None
            current_window_idx = -1

            # Render and pipe each frame
            for frame_num in range(total_frames):
                # Determine if this frame is in an active window
                if active_frame_ranges is not None:
                    window_idx = -1
                    window_start = 0
                    window_length = total_frames
                    for idx, (start, end) in enumerate(active_frame_ranges):
                        if start <= frame_num < end:
                            window_idx = idx
                            window_start = start
                            window_length = end - start
                            break

                    if window_idx == -1:
                        # Inactive frame — write transparent
                        process.stdin.write(transparent_bytes)
                        continue

                    # Re-initialize particles at the start of each new window
                    if window_idx != current_window_idx:
                        particles = self._init_particles(window_length)
                        current_window_idx = window_idx

                    local_frame = frame_num - window_start
                    self._update_particles(particles, local_frame, window_length)
                else:
                    # No active_windows — render all frames (backward compatible)
                    if particles is None:
                        particles = self._init_particles(total_frames)
                    self._update_particles(particles, frame_num, total_frames)

                frame = self._render_frame(particles)
                process.stdin.write(frame.tobytes())

            process.stdin.close()
            _, stderr = process.communicate(timeout=120)

            if process.returncode != 0:
                self.logger.error(f"FFmpeg overlay encoding failed: {stderr.decode('utf-8', errors='replace')}")
                return False

            self.logger.info(f"Overlay generated: {Path(output_path).name}")
            return True

        except Exception as e:
            self.logger.error(f"Error generating particle overlay: {e}")
            return False

    # ----------------------------------------------------------------
    # Particle initialization
    # ----------------------------------------------------------------

    def _init_particles(self, total_frames: int) -> List[Particle]:
        """Create initial set of particles based on type"""
        particles = []
        for _ in range(self.particle_count):
            particles.append(self._spawn_particle(total_frames, initial=True))
        return particles

    def _spawn_particle(self, total_frames: int, initial: bool = False) -> Particle:
        """Spawn a single particle with type-specific properties"""
        color = random.choice(self.colors)
        phase = random.uniform(0, 2 * math.pi)
        sm = self.size_multiplier

        if self.particle_type == ParticleType.HEARTS:
            size = random.uniform(30, 85) * sm
            life = random.uniform(total_frames * 0.5, total_frames * 0.9)
            x = random.uniform(0, self.width)
            y = random.uniform(self.height * 0.3, self.height * 1.3) if initial else self.height + size
            a = random.uniform(0.6, 0.95)
            return Particle(
                x=x, y=y, size=size,
                alpha=a,
                rotation=random.uniform(-15, 15),
                speed_x=0, speed_y=-random.uniform(1.5, 4.0),
                color=color, life=life, max_life=life,
                rotation_speed=random.uniform(-0.5, 0.5),
                phase=phase, base_alpha=a
            )

        elif self.particle_type == ParticleType.SPARKLES:
            size = random.uniform(8, 28) * sm
            life = random.uniform(self.fps * 0.5, self.fps * 1.5)  # 0.5-1.5 seconds
            a = random.uniform(0.6, 0.95)
            return Particle(
                x=random.uniform(0, self.width),
                y=random.uniform(0, self.height),
                size=size, alpha=0.0,
                rotation=random.uniform(0, 360),
                speed_x=0, speed_y=0,
                color=color, life=life, max_life=life,
                phase=phase, base_alpha=a
            )

        elif self.particle_type == ParticleType.PETALS:
            size = random.uniform(15, 40) * sm
            life = random.uniform(total_frames * 0.4, total_frames * 0.8)
            x = random.uniform(-size, self.width + size)
            y = random.uniform(-self.height * 0.3, self.height * 0.7) if initial else -size * 2
            a = random.uniform(0.5, 0.85)
            return Particle(
                x=x, y=y, size=size,
                alpha=a,
                rotation=random.uniform(0, 360),
                speed_x=random.uniform(0.4, 1.2),
                speed_y=random.uniform(0.8, 2.0),
                color=color, life=life, max_life=life,
                rotation_speed=random.uniform(-2.0, 2.0),
                phase=phase, base_alpha=a
            )

        else:  # CONFETTI
            size = random.uniform(6, 18) * sm
            life = random.uniform(total_frames * 0.3, total_frames * 0.7)
            x = random.uniform(0, self.width)
            y = random.uniform(-self.height * 0.3, self.height * 0.5) if initial else -size * 3
            a = random.uniform(0.6, 0.95)
            return Particle(
                x=x, y=y, size=size,
                alpha=a,
                rotation=random.uniform(0, 360),
                speed_x=random.uniform(-1.5, 1.5),
                speed_y=random.uniform(1.5, 3.5),
                color=color, life=life, max_life=life,
                rotation_speed=random.uniform(-6, 6),
                phase=phase, base_alpha=a
            )

    # ----------------------------------------------------------------
    # Per-frame update
    # ----------------------------------------------------------------

    def _update_particles(self, particles: List[Particle],
                          frame_num: int, total_frames: int):
        """Update all particles for the current frame"""
        for i, p in enumerate(particles):
            p.life -= 1
            p.phase += 0.08
            p.rotation += p.rotation_speed

            if self.particle_type == ParticleType.HEARTS:
                p.y += p.speed_y
                p.x += math.sin(p.phase) * 1.2  # Horizontal sway
                # Fade in/out based on life progress
                progress = 1.0 - (p.life / p.max_life)
                if progress < 0.12:
                    p.alpha = p.base_alpha * (progress / 0.12)
                elif progress > 0.88:
                    p.alpha = p.base_alpha * ((1.0 - progress) / 0.12)
                else:
                    p.alpha = p.base_alpha
                # Respawn if dead or off-screen
                if p.life <= 0 or p.y < -p.size * 2:
                    particles[i] = self._spawn_particle(total_frames)

            elif self.particle_type == ParticleType.SPARKLES:
                # Pulse alpha: fade in -> hold -> fade out
                progress = 1.0 - (p.life / p.max_life)
                if progress < 0.2:
                    p.alpha = p.base_alpha * (progress / 0.2)
                elif progress > 0.8:
                    p.alpha = p.base_alpha * ((1.0 - progress) / 0.2)
                else:
                    p.alpha = p.base_alpha * (0.8 + 0.2 * math.sin(p.phase * 3))
                # Pulse size
                p.size *= (0.97 + 0.06 * math.sin(p.phase * 2))
                p.size = max(5, min(35, p.size))
                if p.life <= 0:
                    particles[i] = self._spawn_particle(total_frames)

            elif self.particle_type == ParticleType.PETALS:
                p.x += p.speed_x + math.sin(p.phase) * 0.6
                p.y += p.speed_y
                # Fade at edges using base_alpha
                progress = 1.0 - (p.life / p.max_life)
                if progress < 0.1:
                    p.alpha = p.base_alpha * (progress / 0.1)
                elif progress > 0.9:
                    p.alpha = p.base_alpha * ((1.0 - progress) / 0.1)
                else:
                    p.alpha = p.base_alpha
                if p.life <= 0 or p.y > self.height + p.size * 2:
                    particles[i] = self._spawn_particle(total_frames)

            else:  # CONFETTI
                p.x += p.speed_x + math.sin(p.phase * 1.5) * 0.5
                p.y += p.speed_y
                p.speed_x *= 0.999  # Slight air resistance
                # Fade at bottom
                if p.y > self.height * 0.85:
                    p.alpha *= 0.95
                if p.life <= 0 or p.y > self.height + p.size * 2:
                    particles[i] = self._spawn_particle(total_frames)

    # ----------------------------------------------------------------
    # Frame rendering
    # ----------------------------------------------------------------

    def _render_frame(self, particles: List[Particle]) -> Image.Image:
        """Render all particles onto a transparent RGBA frame"""
        frame = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)

        for p in particles:
            if p.alpha <= 0.01:
                continue
            alpha_int = int(max(0, min(255, p.alpha * 255)))

            if self.particle_type == ParticleType.HEARTS:
                self._draw_heart(draw, p, alpha_int)
            elif self.particle_type == ParticleType.SPARKLES:
                self._draw_sparkle(draw, p, alpha_int)
            elif self.particle_type == ParticleType.PETALS:
                self._draw_petal(frame, p, alpha_int)
            else:  # CONFETTI
                self._draw_confetti(frame, p, alpha_int)

        return frame

    # ----------------------------------------------------------------
    # Shape drawing
    # ----------------------------------------------------------------

    def _draw_heart(self, draw: 'ImageDraw.Draw', p: Particle, alpha: int):
        """Draw a heart shape using parametric curve"""
        points = self._heart_polygon(p.x, p.y, p.size)
        color = (*p.color, alpha)
        if len(points) >= 3:
            draw.polygon(points, fill=color)

    def _heart_polygon(self, cx: float, cy: float, size: float) -> List[Tuple[int, int]]:
        """Generate heart shape points using parametric equations"""
        points = []
        num_points = 50
        scale = size / 32.0
        for i in range(num_points):
            t = (i / num_points) * 2 * math.pi
            x = 16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t) -
                  2 * math.cos(3 * t) - math.cos(4 * t))
            points.append((int(cx + x * scale), int(cy + y * scale)))
        return points

    def _draw_sparkle(self, draw: 'ImageDraw.Draw', p: Particle, alpha: int):
        """Draw a 4-pointed star sparkle"""
        color = (*p.color, alpha)
        s = p.size
        cx, cy = p.x, p.y
        angle_offset = math.radians(p.rotation)

        # 4-pointed star: 8 vertices alternating outer/inner
        points = []
        for i in range(8):
            angle = angle_offset + math.pi * i / 4
            r = s if i % 2 == 0 else s * 0.3
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            points.append((int(px), int(py)))

        if len(points) >= 3:
            draw.polygon(points, fill=color)

    def _draw_petal(self, frame: Image.Image, p: Particle, alpha: int):
        """Draw a rotated ellipse petal shape"""
        s = max(3, int(p.size))
        w = s
        h = int(s * 1.8)

        # Draw ellipse on small transparent image, then rotate and paste
        petal_img = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0))
        petal_draw = ImageDraw.Draw(petal_img)
        color = (*p.color, alpha)
        petal_draw.ellipse(
            [w // 2, 0, w + w // 2, h * 2],
            fill=color
        )

        # Rotate
        rotated = petal_img.rotate(p.rotation, resample=Image.BICUBIC, expand=False)

        # Paste onto frame at particle position
        paste_x = int(p.x - rotated.width // 2)
        paste_y = int(p.y - rotated.height // 2)

        # Bounds check
        if (paste_x + rotated.width > 0 and paste_x < self.width and
                paste_y + rotated.height > 0 and paste_y < self.height):
            frame.paste(rotated, (paste_x, paste_y), rotated)

    def _draw_confetti(self, frame: Image.Image, p: Particle, alpha: int):
        """Draw a small rotated rectangle confetti piece"""
        s = max(2, int(p.size))
        w = s
        h = int(s * 1.6)

        # Draw rectangle on small transparent image, then rotate and paste
        conf_img = Image.new('RGBA', (w * 3, h * 3), (0, 0, 0, 0))
        conf_draw = ImageDraw.Draw(conf_img)
        color = (*p.color, alpha)
        cx, cy = conf_img.width // 2, conf_img.height // 2
        conf_draw.rectangle(
            [cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2],
            fill=color
        )

        rotated = conf_img.rotate(p.rotation, resample=Image.BICUBIC, expand=False)

        paste_x = int(p.x - rotated.width // 2)
        paste_y = int(p.y - rotated.height // 2)

        if (paste_x + rotated.width > 0 and paste_x < self.width and
                paste_y + rotated.height > 0 and paste_y < self.height):
            frame.paste(rotated, (paste_x, paste_y), rotated)
