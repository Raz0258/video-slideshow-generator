/**
 * Configuration Builder Module
 * Handles building configuration objects and generating YAML
 */

/**
 * Detect if text is primarily Hebrew (for RTL support)
 * @param {string} text - Text to analyze
 * @returns {boolean} - True if text contains significant Hebrew characters
 */
function isHebrewText(text) {
    if (!text || text.trim() === '') return false;
    
    // Hebrew Unicode range: \u0590-\u05FF
    const hebrewChars = text.match(/[\u0590-\u05FF]/g);
    const totalChars = text.replace(/\s/g, '').length;
    
    // If no characters or more than 30% are Hebrew, treat as RTL
    if (totalChars === 0) return false;
    return hebrewChars && (hebrewChars.length / totalChars) > 0.3;
}

/**
 * Build configuration object from form inputs
 */
function buildConfig() {
    const res = document.getElementById('resolution').value.split(',');
    const gentle = parseInt(document.getElementById('transGentle').value) / 100;
    const dynamic = parseInt(document.getElementById('transDynamic').value) / 100;
    const artistic = parseInt(document.getElementById('transArtistic').value) / 100;

    return {
        project: {
            name: document.getElementById('projectName').value || 'My Slideshow',
            description: document.getElementById('projectDescription').value || ''
        },
        paths: {
            images_dir: document.getElementById('imagesDir').value.replace(/\\/g, '/'),
            audio_dir: document.getElementById('audioDir').value.replace(/\\/g, '/'),
            output_file: (document.getElementById('outputDir').value.replace(/\\/g, '/') + '/' +
                         (document.getElementById('projectName').value || 'slideshow').replace(/\s+/g, '_') + '.mp4'),
            preview_file: (document.getElementById('outputDir').value.replace(/\\/g, '/') + '/' +
                          (document.getElementById('projectName').value || 'slideshow').replace(/\s+/g, '_') + '_preview.mp4')
        },
        special_images: {
            opening_closing: document.getElementById('specialPhoto').value.replace(/\\/g, '/')
        },
        video_settings: {
            resolution: [parseInt(res[0]), parseInt(res[1])],
            fps: parseInt(document.getElementById('fps').value),
            crf: parseInt(document.getElementById('crf').value),
            preset: document.getElementById('preset').value
        },
        sequences: {
            opening: {
                part1_duration: parseFloat(document.getElementById('openingPart1').value),
                part2_duration: parseFloat(document.getElementById('openingPart2').value)
            },
            images: {
                duration_per_image: parseFloat(document.getElementById('imageDuration').value)
            },
            closing: {
                min_duration: parseFloat(document.getElementById('closingDuration').value)
            }
        },
        style: {
            transitions: {
                duration: parseFloat(document.getElementById('transitionDuration').value),
                categories: ['gentle', 'dynamic', 'artistic'],
                weights: [gentle, dynamic, artistic]
            },
            ken_burns: {
                application_rate: parseInt(document.getElementById('kenBurns').value) / 100
            },
            color_grading: {
                preset: document.getElementById('colorGrading').value
            },
            audio: {
                fade_in: 1.0,
                fade_out: 2.0
            },
            particle_overlays: {
                enabled: document.getElementById('particleEnabled').checked,
                type: document.getElementById('particleType').value,
                size: document.getElementById('particleSize').value,
                density: parseInt(document.getElementById('particleDensity').value) / 100,
                application_rate: parseInt(document.getElementById('particleRate').value) / 100,
                apply_to_opening: document.getElementById('particleOpening').checked,
                apply_to_closing: document.getElementById('particleClosing').checked
            }
        },
        text_overlays: {
            opening: buildOpeningText(),
            closing: buildClosingText()
        }
    };
}

/**
 * Build opening text configuration
 */
function buildOpeningText() {
    if (!document.getElementById('openingEnabled').checked) {
        return { enabled: false };
    }

    const openingText = document.getElementById('openingText').value || 'Welcome';

    return {
        enabled: true,
        main: {
            text: openingText,
            font: 'C:/Windows/Fonts/arial.ttf',
            fontsize: parseInt(document.getElementById('openingSize').value),
            fontcolor: document.getElementById('openingColor').value,
            position: {
                x: '(w-text_w)/2',
                y: '810-text_h/2'
            },
            shadow: {
                color: 'black@0.7',
                x: 4,
                y: 4
            },
            effects: {
                fade_in: 0.8,
                fade_out: 0.8
            },
            text_shaping: isHebrewText(openingText) ? 1 : 1  // Always 1 for proper text rendering
        }
    };
}

/**
 * Build closing text configuration
 */
function buildClosingText() {
    if (!document.getElementById('closingEnabled').checked) {
        return { enabled: false };
    }

    const closingText = document.getElementById('closingText').value || 'Thank You';

    const config = {
        enabled: true,
        main: {
            text: closingText,
            font: 'C:/Windows/Fonts/arial.ttf',
            fontsize: parseInt(document.getElementById('closingSize').value),
            fontcolor: document.getElementById('closingColor').value,
            position: {
                x: '(w-text_w)/2',
                y_offset: -70
            },
            shadow: {
                color: 'black@0.7',
                x: 4,
                y: 4
            },
            effects: {
                fade_in: 1.2,
                fade_out: 2.0
            },
            text_shaping: isHebrewText(closingText) ? 1 : 1  // Always 1 for proper text rendering
        },
        base_position: {
            y: 0.75
        }
    };

    const subtitles = [];
    const sub1 = document.getElementById('subtitle1').value;
    const sub2 = document.getElementById('subtitle2').value;

    if (sub1) {
        subtitles.push({
            text: sub1,
            font: 'C:/Windows/Fonts/arial.ttf',
            fontsize: 52,
            fontcolor: 'white',
            position: { x: '(w-text_w)/2', y_offset: 50 },
            shadow: { color: 'black@0.7', x: 3, y: 3 },
            effects: { fade_in: 1.2, fade_out: 2.0 },
            text_shaping: isHebrewText(sub1) ? 1 : 1  // Always 1 for proper text rendering
        });
    }

    if (sub2) {
        subtitles.push({
            text: sub2,
            font: 'C:/Windows/Fonts/arial.ttf',
            fontsize: 48,
            fontcolor: 'white',
            position: { x: '(w-text_w)/2', y_offset: 110 },
            shadow: { color: 'black@0.7', x: 3, y: 3 },
            effects: { fade_in: 1.2, fade_out: 2.0 },
            text_shaping: isHebrewText(sub2) ? 1 : 1  // Always 1 for proper text rendering
        });
    }

    if (subtitles.length > 0) {
        config.subtitles = subtitles;
    }

    return config;
}

/**
 * Generate YAML string from configuration object
 */
function generateYAML(config) {
    let yaml = `# Slideshow Configuration
# Generated by Slideshow Configuration Builder

# Project Information
project:
  name: "${config.project.name}"
  description: "${config.project.description}"
  version: "1.0"

# File Paths
paths:
  images_dir: "${config.paths.images_dir}"
  audio_dir: "${config.paths.audio_dir}"
  output_file: "${config.paths.output_file}"
  preview_file: "${config.paths.preview_file}"

# Special Images
special_images:
  opening_closing: "${config.special_images.opening_closing}"

# Video Settings
video_settings:
  resolution: [${config.video_settings.resolution.join(', ')}]
  fps: ${config.video_settings.fps}
  crf: ${config.video_settings.crf}
  preset: "${config.video_settings.preset}"

# Sequence Timing
sequences:
  opening:
    part1_duration: ${config.sequences.opening.part1_duration}
    part2_duration: ${config.sequences.opening.part2_duration}
  images:
    duration_per_image: ${config.sequences.images.duration_per_image}
  closing:
    min_duration: ${config.sequences.closing.min_duration}

# Style Configuration
style:
  transitions:
    duration: ${config.style.transitions.duration}
    categories: [${config.style.transitions.categories.map(c => `"${c}"`).join(', ')}]
    weights: [${config.style.transitions.weights.join(', ')}]

  ken_burns:
    application_rate: ${config.style.ken_burns.application_rate}
    zoom_range: [1.0, 1.08]
    pan_amount: 0.06
    speed_variations: [0.7, 0.85, 1.0]

  color_grading:
    preset: "${config.style.color_grading.preset}"

  audio:
    fade_in: ${config.style.audio.fade_in}
    fade_out: ${config.style.audio.fade_out}

  particle_overlays:
    enabled: ${config.style.particle_overlays.enabled}
    type: "${config.style.particle_overlays.type}"
    size: "${config.style.particle_overlays.size}"
    density: ${config.style.particle_overlays.density}
    application_rate: ${config.style.particle_overlays.application_rate}
    apply_to_opening: ${config.style.particle_overlays.apply_to_opening}
    apply_to_closing: ${config.style.particle_overlays.apply_to_closing}

# Text Overlays
text_overlays:
`;

    // Opening text
    if (config.text_overlays.opening.enabled) {
        yaml += `  opening:
    enabled: true
    main:
      text: "${config.text_overlays.opening.main.text}"
      font: "${config.text_overlays.opening.main.font}"
      fontsize: ${config.text_overlays.opening.main.fontsize}
      fontcolor: "${config.text_overlays.opening.main.fontcolor}"
      position:
        x: "${config.text_overlays.opening.main.position.x}"
        y: "${config.text_overlays.opening.main.position.y}"
      shadow:
        color: "${config.text_overlays.opening.main.shadow.color}"
        x: ${config.text_overlays.opening.main.shadow.x}
        y: ${config.text_overlays.opening.main.shadow.y}
      effects:
        fade_in: ${config.text_overlays.opening.main.effects.fade_in}
        fade_out: ${config.text_overlays.opening.main.effects.fade_out}
      text_shaping: ${config.text_overlays.opening.main.text_shaping}
`;
    } else {
        yaml += `  opening:
    enabled: false
`;
    }

    // Closing text
    if (config.text_overlays.closing.enabled) {
        yaml += `  closing:
    enabled: true
    main:
      text: "${config.text_overlays.closing.main.text}"
      font: "${config.text_overlays.closing.main.font}"
      fontsize: ${config.text_overlays.closing.main.fontsize}
      fontcolor: "${config.text_overlays.closing.main.fontcolor}"
      position:
        x: "${config.text_overlays.closing.main.position.x}"
        y_offset: ${config.text_overlays.closing.main.position.y_offset}
      shadow:
        color: "${config.text_overlays.closing.main.shadow.color}"
        x: ${config.text_overlays.closing.main.shadow.x}
        y: ${config.text_overlays.closing.main.shadow.y}
      effects:
        fade_in: ${config.text_overlays.closing.main.effects.fade_in}
        fade_out: ${config.text_overlays.closing.main.effects.fade_out}
      text_shaping: ${config.text_overlays.closing.main.text_shaping}
`;

        if (config.text_overlays.closing.subtitles && config.text_overlays.closing.subtitles.length > 0) {
            yaml += `    subtitles:\n`;
            config.text_overlays.closing.subtitles.forEach(sub => {
                yaml += `      - text: "${sub.text}"
        font: "${sub.font}"
        fontsize: ${sub.fontsize}
        fontcolor: "${sub.fontcolor}"
        position:
          x: "${sub.position.x}"
          y_offset: ${sub.position.y_offset}
        shadow:
          color: "${sub.shadow.color}"
          x: ${sub.shadow.x}
          y: ${sub.shadow.y}
        effects:
          fade_in: ${sub.effects.fade_in}
          fade_out: ${sub.effects.fade_out}
        text_shaping: ${sub.text_shaping}
`;
            });
        }

        yaml += `    base_position:
      y: ${config.text_overlays.closing.base_position.y}
`;
    } else {
        yaml += `  closing:
    enabled: false
`;
    }

    return yaml;
}

/**
 * Apply syntax highlighting to YAML text
 */
function highlightYAML(yaml, activeFieldId = null) {
    // Map field IDs to YAML keys for highlighting
    const fieldToYamlKey = {
        'projectName': 'name:',
        'projectDescription': 'description:',
        'imagesDir': 'images_dir:',
        'audioDir': 'audio_dir:',
        'outputDir': 'output_file:',
        'specialPhoto': 'opening_closing:',
        'resolution': 'resolution:',
        'fps': 'fps:',
        'crf': 'crf:',
        'preset': 'preset:',
        'openingPart1': 'part1_duration:',
        'openingPart2': 'part2_duration:',
        'imageDuration': 'duration_per_image:',
        'closingDuration': 'min_duration:',
        'transitionDuration': 'duration:',
        'transGentle': 'weights:',
        'transDynamic': 'weights:',
        'transArtistic': 'weights:',
        'kenBurns': 'application_rate:',
        'colorGrading': 'preset:',
        'openingText': 'opening:',
        'closingText': 'closing:'
    };

    const activeKey = activeFieldId ? fieldToYamlKey[activeFieldId] : null;
    const lines = yaml.split('\n');
    let html = '';

    lines.forEach((line, index) => {
        let processedLine = line;
        let isHighlighted = false;

        // Check if this line should be highlighted
        if (activeKey && line.includes(activeKey)) {
            isHighlighted = true;
        }

        // Apply syntax highlighting
        if (line.trim().startsWith('#')) {
            // Comment line
            processedLine = `<span class="yaml-comment">${escapeHtml(line)}</span>`;
        } else if (line.includes(':')) {
            // Key-value pair
            const colonIndex = line.indexOf(':');
            const key = line.substring(0, colonIndex + 1);
            const value = line.substring(colonIndex + 1);

            processedLine = `<span class="yaml-key">${escapeHtml(key)}</span><span class="yaml-value">${escapeHtml(value)}</span>`;
        } else {
            processedLine = escapeHtml(line);
        }

        // Wrap highlighted lines
        if (isHighlighted) {
            processedLine = `<span class="yaml-highlight">${processedLine}</span>`;
        }

        html += processedLine + '\n';
    });

    return html;
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Update preview panel with current configuration
 */
function updatePreview(activeFieldId = null) {
    const config = buildConfig();
    const yaml = generateYAML(config);
    const highlightedYaml = highlightYAML(yaml, activeFieldId);
    document.getElementById('yamlPreview').innerHTML = highlightedYaml;
}

/**
 * Download YAML file
 */
function downloadYAML() {
    if (!validateAll()) {
        alert('Please fix validation errors before downloading.');
        return;
    }

    const config = buildConfig();
    const yaml = generateYAML(config);
    const filename = (config.project.name || 'slideshow').replace(/\s+/g, '_').toLowerCase() + '.yaml';

    const blob = new Blob([yaml], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    alert(`✅ Configuration downloaded as "${filename}"!\n\nNext steps:\n1. Place the file in your project folder\n2. Run: python create_slideshow_enhanced.py --config ${filename}`);
}

/**
 * Download YAML from progress modal
 */
function downloadYAMLFromProgress(filename, yaml) {
    const blob = new Blob([yaml], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Download YAML from summary modal
 */
function downloadYAMLFromSummary() {
    downloadYAML();
}