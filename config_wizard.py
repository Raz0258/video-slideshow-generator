#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Configuration Wizard
Step-by-step CLI tool for creating slideshow configurations
"""

import os
import sys
from pathlib import Path
from typing import Optional


class ConfigWizard:
    """Interactive wizard for creating slideshow configurations"""

    def __init__(self):
        self.config = {}

    def run(self):
        """Run the interactive wizard"""
        self.print_header()

        # Select template
        template = self.select_template()
        if template:
            self.load_template(template)

        # Collect project information
        self.collect_project_info()

        # Collect paths
        self.collect_paths()

        # Ask about customization
        if self.ask_yes_no("\nWould you like to customize advanced settings?", default=False):
            self.collect_video_settings()
            self.collect_timing_settings()
            self.collect_effects()
            self.collect_text_settings()
        else:
            print("\n✓ Using smart defaults for all advanced settings")

        # Save configuration
        self.save_configuration()

        self.print_footer()

    def print_header(self):
        """Print welcome header"""
        print("\n" + "=" * 70)
        print("  Slideshow Configuration Wizard")
        print("=" * 70)
        print("\nThis wizard will help you create a configuration file for your slideshow.")
        print("Press Ctrl+C at any time to cancel.\n")

    def print_footer(self):
        """Print completion message"""
        print("\n" + "=" * 70)
        print("  Configuration Created Successfully!")
        print("=" * 70)
        output_file = self.config.get('_output_path', 'my_slideshow.yaml')
        print(f"\n✓ Configuration saved to: {output_file}")
        print(f"\nNext steps:")
        print(f"  1. Review the configuration file")
        print(f"  2. Run: python create_slideshow_enhanced.py --config {output_file}")
        print(f"  3. Or generate a preview: python create_slideshow_enhanced.py --config {output_file} --preview")
        print("\n")

    def select_template(self) -> Optional[str]:
        """Let user select a template"""
        print("Step 1: Template Selection")
        print("-" * 70)
        print("\nAvailable templates:")
        print("  1. Start from scratch (empty configuration)")
        print("  2. Anniversary - Romantic theme with gold text")
        print("  3. Birthday - Celebratory theme with vibrant colors")
        print("  4. Wedding - Elegant theme with soft transitions")
        print("  5. Travel - Adventure theme with dynamic transitions")
        print("  6. Minimal - Simple slideshow without text")

        choice = self.ask_choice("\nSelect a template", ["1", "2", "3", "4", "5", "6"], default="1")

        templates = {
            "1": None,
            "2": "anniversary",
            "3": "birthday",
            "4": "wedding",
            "5": "travel",
            "6": "minimal"
        }

        selected = templates[choice]
        if selected:
            print(f"\n✓ Using {selected} template as starting point")
        else:
            print("\n✓ Starting with empty configuration")

        return selected

    def load_template(self, template_name: str):
        """Load template defaults"""
        templates = {
            "anniversary": {
                "project_name": "Anniversary Celebration",
                "opening_text": "Years of Love",
                "closing_text": "Happy Anniversary!",
                "color_grading": "warm"
            },
            "birthday": {
                "project_name": "Birthday Celebration",
                "opening_text": "Happy Birthday!",
                "closing_text": "Best Wishes!",
                "color_grading": "vibrant"
            },
            "wedding": {
                "project_name": "Our Wedding Day",
                "opening_text": "Our Wedding Day",
                "closing_text": "Just Married!",
                "color_grading": "soft"
            },
            "travel": {
                "project_name": "Travel Adventures",
                "opening_text": "Our Journey",
                "closing_text": "What an Adventure!",
                "color_grading": "vibrant"
            },
            "minimal": {
                "project_name": "Simple Slideshow",
                "text_enabled": False,
                "color_grading": "neutral"
            }
        }

        if template_name in templates:
            self.config.update(templates[template_name])

    def collect_project_info(self):
        """Collect project information"""
        print("\n\nStep 2: Project Information")
        print("-" * 70)

        default_name = self.config.get("project_name", "My Slideshow")
        self.config["project_name"] = self.ask_string(
            "Project name",
            default=default_name
        )

        self.config["project_description"] = self.ask_string(
            "Description (optional)",
            default="",
            required=False
        )

    def collect_paths(self):
        """Collect file paths"""
        print("\n\nStep 3: File Paths")
        print("-" * 70)

        # Images directory
        while True:
            images_dir = self.ask_path("Images directory (folder with your photos)")
            if Path(images_dir).exists():
                # Count images
                image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.JPG', '.JPEG', '.PNG'}
                images = [f for f in Path(images_dir).iterdir()
                         if f.is_file() and f.suffix in image_exts]

                if len(images) >= 2:
                    print(f"  ✓ Found {len(images)} images")
                    self.config["images_dir"] = str(Path(images_dir))
                    break
                else:
                    print(f"  ✗ Only {len(images)} images found. Need at least 2.")
            else:
                print(f"  ✗ Directory not found: {images_dir}")

        # Audio directory
        while True:
            audio_dir = self.ask_path("Audio directory (folder with background music)")
            if Path(audio_dir).exists():
                audio_exts = {'.mp3', '.wav', '.m4a', '.MP3', '.WAV'}
                audio_files = [f for f in Path(audio_dir).iterdir()
                              if f.is_file() and f.suffix in audio_exts]

                if len(audio_files) >= 1:
                    print(f"  ✓ Found {len(audio_files)} audio file(s)")
                    if len(audio_files) > 1:
                        print(f"  ℹ Will use: {audio_files[0].name}")
                    self.config["audio_dir"] = str(Path(audio_dir))
                    break
                else:
                    print(f"  ✗ No audio files found. Add at least one MP3 or WAV file.")
            else:
                print(f"  ✗ Directory not found: {audio_dir}")

        # Output directory
        output_dir = self.ask_path("Output directory (where to save the video)")
        self.config["output_dir"] = str(Path(output_dir))

        # Special photo
        print("\nAvailable images:")
        images_path = Path(self.config["images_dir"])
        image_files = sorted([f.name for f in images_path.iterdir()
                             if f.is_file() and f.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp'}])

        for i, img in enumerate(image_files[:10], 1):
            print(f"  {i}. {img}")

        if len(image_files) > 10:
            print(f"  ... and {len(image_files) - 10} more")

        self.config["special_photo"] = self.ask_string(
            "\nSpecial photo filename (for opening/closing)",
            default=image_files[0] if image_files else "photo.jpg"
        )

    def collect_video_settings(self):
        """Collect video settings"""
        print("\n\nVideo Settings")
        print("-" * 70)

        resolutions = ["1920x1080 (Full HD)", "1280x720 (HD)", "3840x2160 (4K)"]
        res_choice = self.ask_choice("Resolution", ["1", "2", "3"], default="1")
        res_map = {"1": [1920, 1080], "2": [1280, 720], "3": [3840, 2160]}
        self.config["resolution"] = res_map[res_choice]

        fps_choice = self.ask_choice("Frame rate", ["24 (Cinematic)", "30 (Standard)", "60 (Smooth)"], default="30")
        self.config["fps"] = int(fps_choice.split()[0])

        crf = self.ask_int("Quality (CRF, 18=Excellent, 23=Good, 28=Fair)", default=23, min_val=0, max_val=51)
        self.config["crf"] = crf

    def collect_timing_settings(self):
        """Collect timing settings"""
        print("\n\nTiming Settings")
        print("-" * 70)

        self.config["image_duration"] = self.ask_float(
            "Seconds per image",
            default=6.0,
            min_val=2.0,
            max_val=15.0
        )

    def collect_effects(self):
        """Collect effects settings"""
        print("\n\nVisual Effects")
        print("-" * 70)

        colors = ["warm", "vibrant", "soft", "neutral"]
        default_color = self.config.get("color_grading", "warm")
        default_idx = str(colors.index(default_color) + 1) if default_color in colors else "1"

        color_choice = self.ask_choice(
            "Color grading",
            ["1. Warm", "2. Vibrant", "3. Soft", "4. Neutral"],
            default=default_idx
        )
        self.config["color_grading"] = colors[int(color_choice.split('.')[0]) - 1]

        kb_rate = self.ask_int(
            "Ken Burns effect (% of images with zoom/pan)",
            default=65,
            min_val=0,
            max_val=100
        )
        self.config["ken_burns_rate"] = kb_rate / 100.0

    def collect_text_settings(self):
        """Collect text overlay settings"""
        print("\n\nText Overlays")
        print("-" * 70)

        text_enabled = self.config.get("text_enabled", True)
        if not isinstance(text_enabled, bool):
            text_enabled = True

        use_text = self.ask_yes_no("Enable text overlays?", default=text_enabled)
        self.config["text_enabled"] = use_text

        if use_text:
            default_opening = self.config.get("opening_text", "Welcome")
            self.config["opening_text"] = self.ask_string("Opening text", default=default_opening)

            default_closing = self.config.get("closing_text", "Thank You")
            self.config["closing_text"] = self.ask_string("Closing text", default=default_closing)

    def save_configuration(self):
        """Save configuration to YAML file"""
        filename = self.config["project_name"].lower().replace(" ", "_") + ".yaml"
        output_path = Path.cwd() / "config" / "projects" / filename

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate YAML
        yaml_content = self.generate_yaml()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        self.config["_output_path"] = str(output_path)

    def generate_yaml(self) -> str:
        """Generate YAML configuration"""
        yaml = f"""# {self.config['project_name']} Configuration
# Generated by Configuration Wizard

project:
  name: "{self.config['project_name']}"
  description: "{self.config.get('project_description', '')}"
  version: "1.0"

paths:
  images_dir: "{self.config['images_dir'].replace(chr(92), '/')}"
  audio_dir: "{self.config['audio_dir'].replace(chr(92), '/')}"
  output_file: "{self.config['output_dir'].replace(chr(92), '/')}/{self.config['project_name'].replace(' ', '_')}.mp4"
  preview_file: "{self.config['output_dir'].replace(chr(92), '/')}/{self.config['project_name'].replace(' ', '_')}_preview.mp4"

special_images:
  opening_closing: "{self.config['special_photo']}"

"""

        # Video settings
        if "resolution" in self.config:
            yaml += f"""video_settings:
  resolution: {self.config['resolution']}
  fps: {self.config.get('fps', 30)}
  crf: {self.config.get('crf', 23)}
  preset: "medium"

"""

        # Timing
        if "image_duration" in self.config:
            yaml += f"""sequences:
  opening:
    part1_duration: 3.0
    part2_duration: 6.0
  images:
    duration_per_image: {self.config['image_duration']}
  closing:
    min_duration: 8.0

"""

        # Effects
        yaml += f"""style:
  color_grading:
    preset: "{self.config.get('color_grading', 'warm')}"

"""

        if "ken_burns_rate" in self.config:
            yaml += f"""  ken_burns:
    application_rate: {self.config['ken_burns_rate']}

"""

        # Text overlays
        if self.config.get("text_enabled", True):
            yaml += f"""text_overlays:
  opening:
    enabled: true
    main:
      text: "{self.config.get('opening_text', 'Welcome')}"
      font: "C:/Windows/Fonts/arial.ttf"
      fontsize: 80
      fontcolor: "white"
      position:
        x: "(w-text_w)/2"
        y: "810-text_h/2"
      shadow:
        color: "black@0.7"
        x: 4
        y: 4
      effects:
        fade_in: 0.8
        fade_out: 0.8
      text_shaping: 0

  closing:
    enabled: true
    main:
      text: "{self.config.get('closing_text', 'Thank You')}"
      font: "C:/Windows/Fonts/arial.ttf"
      fontsize: 90
      fontcolor: "gold"
      position:
        x: "(w-text_w)/2"
        y_offset: -70
      shadow:
        color: "black@0.7"
        x: 4
        y: 4
      effects:
        fade_in: 1.2
        fade_out: 2.0
      text_shaping: 0
    base_position:
      y: 0.75
"""
        else:
            yaml += """text_overlays:
  opening:
    enabled: false
  closing:
    enabled: false
"""

        return yaml

    # Helper methods for user input
    def ask_string(self, prompt: str, default: str = "", required: bool = True) -> str:
        """Ask for string input"""
        while True:
            default_text = f" [{default}]" if default else ""
            user_input = input(f"  {prompt}{default_text}: ").strip()

            if not user_input:
                if default:
                    return default
                elif not required:
                    return ""
                else:
                    print("  ✗ This field is required")
                    continue

            return user_input

    def ask_path(self, prompt: str) -> str:
        """Ask for path input"""
        return self.ask_string(prompt).replace('"', '').replace("'", "")

    def ask_int(self, prompt: str, default: int = 0, min_val: int = None, max_val: int = None) -> int:
        """Ask for integer input"""
        while True:
            value = self.ask_string(prompt, default=str(default))
            try:
                num = int(value)
                if min_val is not None and num < min_val:
                    print(f"  ✗ Value must be at least {min_val}")
                    continue
                if max_val is not None and num > max_val:
                    print(f"  ✗ Value must be at most {max_val}")
                    continue
                return num
            except ValueError:
                print("  ✗ Please enter a valid number")

    def ask_float(self, prompt: str, default: float = 0.0, min_val: float = None, max_val: float = None) -> float:
        """Ask for float input"""
        while True:
            value = self.ask_string(prompt, default=str(default))
            try:
                num = float(value)
                if min_val is not None and num < min_val:
                    print(f"  ✗ Value must be at least {min_val}")
                    continue
                if max_val is not None and num > max_val:
                    print(f"  ✗ Value must be at most {max_val}")
                    continue
                return num
            except ValueError:
                print("  ✗ Please enter a valid number")

    def ask_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Ask for yes/no input"""
        default_text = "[Y/n]" if default else "[y/N]"
        while True:
            response = input(f"  {prompt} {default_text}: ").strip().lower()

            if not response:
                return default

            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("  ✗ Please enter 'y' or 'n'")

    def ask_choice(self, prompt: str, choices: list, default: str = None) -> str:
        """Ask user to select from choices"""
        while True:
            default_text = f" [{default}]" if default else ""
            for choice in choices:
                print(f"  {choice}")

            user_input = input(f"  {prompt}{default_text}: ").strip()

            if not user_input and default:
                return default

            # Check if input matches a choice
            for choice in choices:
                if user_input == choice.split()[0] or user_input == choice.split('.')[0]:
                    return user_input

            print("  ✗ Invalid choice")


def main():
    """Main entry point"""
    try:
        wizard = ConfigWizard()
        wizard.run()
        return 0
    except KeyboardInterrupt:
        print("\n\n✗ Wizard cancelled by user")
        return 130
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
