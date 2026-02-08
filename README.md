# Video Slideshow Generator

A Python-based tool that transforms photo collections into professional video slideshows with background music, visual effects, and text overlays. Features a web-based GUI for easy configuration.

## Features

- **Ken Burns Effects** - Subtle zoom and pan animations on photos
- **Color Grading** - Warm, vibrant, soft, or neutral presets
- **Transitions** - Gentle fades, dynamic slides, and artistic effects with configurable mix
- **Particle Overlays** - Hearts, sparkles, petals, and confetti animations during transitions
- **Text Overlays** - Opening/closing titles with shadow effects and Hebrew/RTL text support
- **Web GUI** - Step-by-step configuration wizard with live YAML preview
- **Segment Rendering** - Memory-efficient approach that handles unlimited images
- **YAML Configuration** - Fully customizable via config files or the GUI
- **Preview Mode** - Quick test renders using a subset of images

## Requirements

- **Python 3.8+**
- **FFmpeg** - Must be installed and available on PATH ([download](https://ffmpeg.org/download.html))
- Python packages (install via `pip install -r requirements.txt`):
  - Flask
  - flask-cors
  - PyYAML
  - Pillow (optional, required for particle overlays)

## Quick Start

### Option 1: Web GUI (Recommended)

Double-click `START_GUI.bat` or run manually:

```bash
# Start the backend server
cd web_gui
python server.py

# Then open web_gui/index.html in your browser
```

The GUI walks you through:
1. **Project** - Name your slideshow
2. **Paths** - Select your images folder, audio folder, and output location
3. **Video** - Resolution, FPS, quality settings
4. **Timing** - Control duration of opening, images, and closing
5. **Effects** - Transitions, Ken Burns, color grading, particles
6. **Text Overlays** - Opening and closing text with styling

### Option 2: Command Line

```bash
# Generate from a config file
python create_slideshow_enhanced.py --config config/projects/my_project.yaml

# Quick preview (uses every 5th image)
python create_slideshow_enhanced.py --config my_project.yaml --preview

# Limit to first 10 images for testing
python create_slideshow_enhanced.py --config my_project.yaml --images 10
```

## Configuration

### Using Templates

Pre-built templates are available in `config/templates/`:

| Template | Style | Best For |
|----------|-------|----------|
| `wedding.yaml` | Soft, elegant, slow transitions | Weddings, romantic events |
| `birthday.yaml` | Vibrant, upbeat | Birthday parties, celebrations |
| `travel.yaml` | Dynamic, cinematic | Travel photos, adventures |
| `minimal.yaml` | Clean, no text overlays | Simple photo-and-music slideshows |

Copy a template to get started:

```bash
cp config/templates/wedding.yaml config/projects/my_wedding.yaml
```

Then edit the paths and text to match your project.

### Configuration Structure

```yaml
project:
  name: "My Slideshow"

paths:
  images_dir: "path/to/photos"
  audio_dir: "path/to/music"
  output_file: "path/to/output/video.mp4"

special_images:
  opening_closing: "featured_photo.jpg"

video_settings:
  resolution: [1920, 1080]   # 720p, 1080p, or 4K
  fps: 30                     # 24, 30, or 60
  crf: 18                     # 0-51 (lower = better quality)
  preset: "medium"            # ultrafast to veryslow

style:
  transitions:
    duration: 0.9
    weights: [0.70, 0.20, 0.10]  # gentle, dynamic, artistic
  ken_burns:
    application_rate: 0.65
  color_grading:
    preset: "warm"            # warm, vibrant, soft, neutral

text_overlays:
  opening:
    enabled: true
    main:
      text: "Welcome"
      fontsize: 80
  closing:
    enabled: true
    main:
      text: "Thank You"
```

See the template files for full configuration options.

## Project Structure

```
.
├── create_slideshow_enhanced.py  # Main entry point
├── slideshow_generator.py        # Core video generation engine
├── segment_renderer.py           # FFmpeg segment rendering
├── sequence_builder.py           # Opening/closing sequence builder
├── timing_calculator.py          # Audio-synced timing calculations
├── ken_burns.py                  # Ken Burns zoom/pan effects
├── color_grading.py              # Color grading presets
├── transitions.py                # Transition effect library
├── particle_overlay.py           # Particle animation generator
├── filter_builder.py             # FFmpeg filter chain builder
├── config_validator.py           # Configuration validation
├── config_wizard.py              # CLI configuration wizard
├── utils.py                      # Shared utilities
├── verify_setup.py               # Environment verification
├── requirements.txt              # Python dependencies
├── START_GUI.bat                 # One-click GUI launcher (Windows)
├── config/
│   ├── base_config.py            # Default configuration values
│   ├── project_config.py         # YAML config loader
│   └── templates/                # Pre-built config templates
│       ├── wedding.yaml
│       ├── birthday.yaml
│       ├── travel.yaml
│       └── minimal.yaml
└── web_gui/
    ├── server.py                 # Flask backend API
    ├── index.html                # Configuration wizard UI
    ├── START_SERVER.bat           # Server launcher (Windows)
    ├── css/styles.css
    └── js/
        ├── app.js                # Main application logic
        ├── api.js                # Backend communication
        ├── config.js             # YAML generation
        ├── validation.js         # Form validation
        ├── modals.js             # Modal dialogs
        └── file-browser.js       # Folder browser
```

## How It Works

1. **Configuration** is loaded from a YAML file (created via GUI or manually)
2. **Images** are validated and analyzed for orientation (portrait/landscape)
3. **Timing** is calculated to sync image durations with the audio track
4. **Segments** are rendered individually - each image becomes a short video clip with Ken Burns effects, color grading, and transitions
5. **Particle overlays** are composited during transition windows
6. **All segments** are concatenated with crossfade transitions and the audio track
7. **Final video** is output as an MP4 with H.264 encoding

## License

MIT
