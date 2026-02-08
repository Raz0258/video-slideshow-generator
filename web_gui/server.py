"""
Backend Server for Slideshow Configuration Builder
Provides API endpoint for video generation
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Get the project root directory (parent of web_gui)
PROJECT_ROOT = Path(__file__).parent.parent

@app.route('/api/generate', methods=['POST'])
def generate_video():
    """
    Generate video from YAML configuration

    Expected JSON payload:
    {
        "yaml_content": "...",
        "filename": "config.yaml",
        "output_dir": "/path/to/output"
    }
    """
    try:
        data = request.json
        yaml_content = data.get('yaml_content')
        filename = data.get('filename', 'config.yaml')
        output_dir = data.get('output_dir', '')

        if not yaml_content:
            return jsonify({'success': False, 'error': 'No YAML content provided'}), 400

        # Create output directory if it doesn't exist
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            config_path = os.path.join(output_dir, filename)
        else:
            config_path = os.path.join(PROJECT_ROOT, filename)

        # Write YAML file
        logger.info(f"Writing config to: {config_path}")
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        # Path to the slideshow script
        script_path = PROJECT_ROOT / 'create_slideshow_enhanced.py'

        if not script_path.exists():
            return jsonify({
                'success': False,
                'error': f'Slideshow script not found at {script_path}'
            }), 404

        # Run the slideshow generation script
        logger.info(f"Starting video generation with config: {config_path}")

        cmd = [sys.executable, str(script_path), '--config', config_path]
        logger.info(f"Running command: {' '.join(cmd)}")

        # Set environment for UTF-8 encoding on Windows
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'

        # Run subprocess and capture output
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
            env=env,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode == 0:
            logger.info("Video generation completed successfully")

            # Parse output to find the generated video file
            output_lines = result.stdout.split('\n')
            output_file = None
            log_file = None

            for line in output_lines:
                if 'Output file:' in line or 'output_file:' in line:
                    output_file = line.split(':', 1)[1].strip()
                elif 'Log file:' in line or 'log_file:' in line:
                    log_file = line.split(':', 1)[1].strip()

            # If not found in output, construct expected paths
            if not output_file and output_dir:
                # Try to find the video file in output directory
                for ext in ['.mp4', '.avi', '.mov']:
                    potential_file = os.path.join(output_dir, filename.replace('.yaml', ext))
                    if os.path.exists(potential_file):
                        output_file = potential_file
                        break

            return jsonify({
                'success': True,
                'output_file': output_file or 'Video generated (check output directory)',
                'log_file': log_file or 'Log file created',
                'stdout': result.stdout,
                'config_path': config_path
            })
        else:
            logger.error(f"Video generation failed with return code {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")

            return jsonify({
                'success': False,
                'error': f'Video generation failed: {result.stderr}',
                'stdout': result.stdout,
                'return_code': result.returncode
            }), 500

    except subprocess.TimeoutExpired:
        logger.error("Video generation timed out")
        return jsonify({
            'success': False,
            'error': 'Video generation timed out (exceeded 1 hour)'
        }), 500
    except Exception as e:
        logger.error(f"Error during video generation: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/validate', methods=['POST'])
def validate_config():
    """
    Validate YAML configuration before generation

    Expected JSON payload:
    {
        "yaml_content": "..."
    }
    """
    try:
        import yaml
        import tempfile
        sys.path.insert(0, str(PROJECT_ROOT))
        from config import ProjectConfig

        data = request.json
        yaml_content = data.get('yaml_content')

        if not yaml_content:
            return jsonify({'valid': False, 'errors': ['No YAML content provided']}), 400

        # Write to temp file for validation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Try to load and validate config
            config = ProjectConfig(temp_path)
            validation_errors = config.validate()

            # Additional checks
            warnings = []

            # Check if special photo is specified
            special_images = config.get_special_images()
            if special_images.get('opening_closing'):
                warnings.append(
                    f"Special photo '{special_images['opening_closing']}' must exist in images directory. "
                    "If not found, first image will be used as fallback."
                )

            # Check for resource-intensive settings
            effect_settings = config.get_effect_settings()
            kb_config = effect_settings.get('ken_burns', {})
            kb_rate = kb_config.get('application_rate', 0.65)

            paths = config.get_paths()
            images_dir = paths.get('images_dir', '')
            if images_dir and os.path.exists(images_dir):
                import glob
                image_count = len(glob.glob(os.path.join(images_dir, '*.[jp][pn]g*')))

                if image_count > 25:
                    warnings.append(
                        f"Large project detected ({image_count} images). "
                        "Memory optimizations will be applied automatically (Ken Burns and color grading will be limited)."
                    )
                elif image_count > 15 and kb_rate > 0.7:
                    warnings.append(
                        f"Moderate project size ({image_count} images) with high Ken Burns rate ({kb_rate:.0%}). "
                        "Consider reducing Ken Burns application rate to 0.5-0.6 for better performance."
                    )

            if validation_errors:
                return jsonify({
                    'valid': False,
                    'errors': validation_errors,
                    'warnings': warnings
                })
            else:
                return jsonify({
                    'valid': True,
                    'errors': [],
                    'warnings': warnings,
                    'message': 'Configuration is valid'
                })

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass

    except Exception as e:
        logger.error(f"Validation error: {str(e)}", exc_info=True)
        return jsonify({
            'valid': False,
            'errors': [f'Validation failed: {str(e)}']
        }), 500

@app.route('/api/browse/quick-paths', methods=['GET'])
def get_quick_paths():
    """
    Get common user folders for quick access

    Returns:
    {
        "paths": [
            {"name": "Desktop", "path": "C:/Users/Username/Desktop"},
            {"name": "Documents", "path": "C:/Users/Username/Documents"},
            ...
        ]
    }
    """
    try:
        import os
        from pathlib import Path

        # Get user home directory
        home = Path.home()

        # Common folders
        common_folders = [
            ("Desktop", home / "Desktop"),
            ("Documents", home / "Documents"),
            ("Pictures", home / "Pictures"),
            ("Music", home / "Music"),
            ("Videos", home / "Videos"),
        ]

        # Build response with existing folders only
        paths = []
        for name, path in common_folders:
            if path.exists():
                # Convert to forward slashes for consistency
                path_str = str(path).replace('\\', '/')
                paths.append({"name": name, "path": path_str})

        return jsonify({"success": True, "paths": paths})

    except Exception as e:
        logger.error(f"Error getting quick paths: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to get quick paths: {str(e)}"
        }), 500

@app.route('/api/browse/folder', methods=['POST'])
def browse_folder():
    """
    Browse folder contents and return list of subfolders

    Expected JSON payload:
    {
        "path": "C:/Users/Username/Documents"
    }

    Returns:
    {
        "success": true,
        "current_path": "C:/Users/Username/Documents",
        "parent_path": "C:/Users/Username",
        "folders": [
            {"name": "Folder1", "path": "C:/Users/Username/Documents/Folder1"},
            {"name": "Folder2", "path": "C:/Users/Username/Documents/Folder2"}
        ]
    }
    """
    try:
        data = request.json
        folder_path = data.get('path', '')

        if not folder_path:
            return jsonify({
                "success": False,
                "error": "No path provided"
            }), 400

        # Convert to Path object and normalize
        path = Path(folder_path)

        # Security check - ensure path exists
        if not path.exists():
            return jsonify({
                "success": False,
                "error": f"Path does not exist: {folder_path}"
            }), 404

        if not path.is_dir():
            return jsonify({
                "success": False,
                "error": f"Path is not a directory: {folder_path}"
            }), 400

        # Get parent path (if not at root)
        parent_path = None
        if path.parent != path:  # Not at root
            parent_path = str(path.parent).replace('\\', '/')

        # Check if we should include image files
        include_images = data.get('include_images', False)
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

        # List all subfolders (and optionally image files)
        folders = []
        files = []
        try:
            for item in sorted(path.iterdir()):
                if item.is_dir():
                    # Skip hidden folders and system folders
                    if not item.name.startswith('.') and not item.name.startswith('$'):
                        folders.append({
                            "name": item.name,
                            "path": str(item).replace('\\', '/')
                        })
                elif include_images and item.suffix.lower() in image_extensions:
                    files.append({
                        "name": item.name,
                        "path": str(item).replace('\\', '/')
                    })
        except PermissionError:
            logger.warning(f"Permission denied accessing some items in {folder_path}")

        result = {
            "success": True,
            "current_path": str(path).replace('\\', '/'),
            "parent_path": parent_path,
            "folders": folders
        }

        if include_images:
            result["files"] = files

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error browsing folder: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to browse folder: {str(e)}"
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'project_root': str(PROJECT_ROOT),
        'script_exists': (PROJECT_ROOT / 'create_slideshow_enhanced.py').exists()
    })

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'Slideshow Configuration Builder API',
        'version': '1.2',
        'endpoints': {
            '/api/generate': 'POST - Generate video from YAML config',
            '/api/validate': 'POST - Validate YAML config before generation',
            '/api/browse/quick-paths': 'GET - Get common user folders for quick access',
            '/api/browse/folder': 'POST - Browse folder contents and subfolders',
            '/api/health': 'GET - Health check'
        }
    })

if __name__ == '__main__':
    logger.info(f"Starting server...")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Script exists: {(PROJECT_ROOT / 'create_slideshow_enhanced.py').exists()}")
    logger.info(f"Server running at http://localhost:5000")
    logger.info(f"Frontend should be opened from: {PROJECT_ROOT / 'web_gui' / 'index.html'}")

    app.run(host='127.0.0.1', port=5000, debug=True)
