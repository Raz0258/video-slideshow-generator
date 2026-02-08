/**
 * Slideshow Configuration Builder - Main Application Script
 * Coordinates all modules and handles UI initialization
 */

// Global state
let currentConfig = {};

/**
 * DOM Ready - Initialize application
 */
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeSliders();
    initializeTextToggles();

    // Initialize preview and validation
    updatePreview();
    validateTransitionWeights();
    highlightInvalidTabs();
});

/**
 * Initialize all event listeners
 */
function initializeEventListeners() {
    // Tab click handlers
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            showTab(tabName);
        });
    });

    // Real-time validation and preview on all inputs
    const allInputs = document.querySelectorAll('input, select, textarea');
    allInputs.forEach(input => {
        input.addEventListener('input', () => {
            updatePreview(input.id); // Pass active field ID for highlighting
            if (input.hasAttribute('required')) {
                validateField(input);
            }
            // Validate special photo on input
            if (input.id === 'specialPhoto') {
                validateSpecialPhoto();
            }
            // Update tab highlighting in real-time
            highlightInvalidTabs();
        });

        // Add focus listener to scroll YAML preview to relevant section
        input.addEventListener('focus', () => {
            highlightYAMLSection(input.id);
            updatePreview(input.id); // Highlight on focus as well
        });

        // Clear highlight on blur
        input.addEventListener('blur', () => {
            setTimeout(() => {
                updatePreview(); // Remove highlight after a short delay
            }, 300);
        });
    });
}

/**
 * Initialize slider value displays
 */
function initializeSliders() {
    // CRF slider with quality label
    document.getElementById('crf').addEventListener('input', (e) => {
        const value = e.target.value;
        let quality = 'Excellent';
        if (value > 28) quality = 'Fair';
        else if (value > 23) quality = 'Good';
        else if (value > 18) quality = 'Very Good';
        document.getElementById('crfValue').textContent = `${value} (${quality})`;
    });

    // Transition sliders with validation
    ['transGentle', 'transDynamic', 'transArtistic'].forEach(id => {
        document.getElementById(id).addEventListener('input', (e) => {
            document.getElementById(id + 'Value').textContent = e.target.value;
            validateTransitionWeights();
            highlightInvalidTabs();
        });
    });

    // Ken Burns slider
    document.getElementById('kenBurns').addEventListener('input', (e) => {
        document.getElementById('kenBurnsValue').textContent = e.target.value;
    });

    // Particle density slider
    document.getElementById('particleDensity').addEventListener('input', (e) => {
        document.getElementById('particleDensityValue').textContent = e.target.value;
    });

    // Particle application rate slider
    document.getElementById('particleRate').addEventListener('input', (e) => {
        document.getElementById('particleRateValue').textContent = e.target.value;
    });
}

/**
 * Initialize text overlay toggles
 */
function initializeTextToggles() {
    document.getElementById('openingEnabled').addEventListener('change', (e) => {
        document.getElementById('openingTextFields').style.display = e.target.checked ? 'block' : 'none';
        updatePreview();
    });

    document.getElementById('closingEnabled').addEventListener('change', (e) => {
        document.getElementById('closingTextFields').style.display = e.target.checked ? 'block' : 'none';
        updatePreview();
    });

    // Particle overlay toggle
    document.getElementById('particleEnabled').addEventListener('change', (e) => {
        document.getElementById('particleFields').style.display = e.target.checked ? 'block' : 'none';
        updatePreview();
    });
}

/**
 * Tab Navigation
 */
function showTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));

    document.querySelector(`[data-tab="${tabName}"].tab`).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"].tab-content`).classList.add('active');
}

function nextTab() {
    const tabs = ['start', 'project', 'paths', 'video', 'timing', 'effects', 'text'];
    const currentTab = document.querySelector('.tab.active').dataset.tab;
    const currentIndex = tabs.indexOf(currentTab);
    if (currentIndex < tabs.length - 1) {
        showTab(tabs[currentIndex + 1]);
    }
}

function prevTab() {
    const tabs = ['start', 'project', 'paths', 'video', 'timing', 'effects', 'text'];
    const currentTab = document.querySelector('.tab.active').dataset.tab;
    const currentIndex = tabs.indexOf(currentTab);
    if (currentIndex > 0) {
        showTab(tabs[currentIndex - 1]);
    }
}

/**
 * Template/Workflow Selection
 */
function startNewVideo() {
    currentConfig = {};
    document.querySelectorAll('.template-card').forEach(c => c.classList.remove('selected'));
    document.querySelector('[data-template="new"]').classList.add('selected');
}

/**
 * Load Existing Configuration
 */
function loadExistingConfig(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const yamlText = e.target.result;
                parseAndLoadYAML(yamlText);
                document.querySelectorAll('.template-card').forEach(c => c.classList.remove('selected'));
                document.querySelector('[data-template="existing"]').classList.add('selected');
                showValidation('Configuration loaded successfully!', 'success');
            } catch (error) {
                showValidation('Error loading configuration: ' + error.message, 'error');
            }
        };
        reader.readAsText(file);
    }
}

/**
 * Parse YAML and populate form
 */
function parseAndLoadYAML(yamlText) {
    // Simple YAML parser for our structured config
    const lines = yamlText.split('\n');
    let currentSection = null;
    let inParticleSection = false;

    lines.forEach(line => {
        const trimmed = line.trim();
        if (trimmed.startsWith('#') || !trimmed) return;

        if (trimmed.includes(':') && !line.startsWith(' ')) {
            currentSection = trimmed.split(':')[0];
            inParticleSection = false;
        }

        // Track particle_overlays subsection
        if (trimmed.startsWith('particle_overlays:')) {
            inParticleSection = true;
            return;
        }
        // Exit particle section when hitting another non-indented key at same or higher level
        if (inParticleSection && trimmed.includes(':') && !line.startsWith('      ') && !line.startsWith('    ')) {
            if (!trimmed.startsWith('enabled') && !trimmed.startsWith('type') &&
                !trimmed.startsWith('size') && !trimmed.startsWith('density') &&
                !trimmed.startsWith('application_rate') && !trimmed.startsWith('apply_to_')) {
                inParticleSection = false;
            }
        }

        // Extract values
        if (trimmed.includes('name:') && currentSection === 'project') {
            document.getElementById('projectName').value = trimmed.split('"')[1] || '';
        }
        if (trimmed.includes('description:') && currentSection === 'project') {
            document.getElementById('projectDescription').value = trimmed.split('"')[1] || '';
        }
        if (trimmed.includes('images_dir:')) {
            document.getElementById('imagesDir').value = trimmed.split('"')[1] || '';
        }
        if (trimmed.includes('audio_dir:')) {
            document.getElementById('audioDir').value = trimmed.split('"')[1] || '';
        }
        if (trimmed.includes('output_file:')) {
            const path = trimmed.split('"')[1] || '';
            const dir = path.substring(0, path.lastIndexOf('/'));
            document.getElementById('outputDir').value = dir;
        }
        if (trimmed.includes('opening_closing:')) {
            document.getElementById('specialPhoto').value = (trimmed.split('"')[1] || '').replace(/\\/g, '/');
        }

        // Particle overlay settings
        if (inParticleSection) {
            if (trimmed.startsWith('enabled:')) {
                const enabled = trimmed.includes('true');
                document.getElementById('particleEnabled').checked = enabled;
                document.getElementById('particleFields').style.display = enabled ? 'block' : 'none';
            }
            if (trimmed.startsWith('type:')) {
                const type = trimmed.split('"')[1] || trimmed.split(':')[1].trim().replace(/"/g, '');
                if (type) document.getElementById('particleType').value = type;
            }
            if (trimmed.startsWith('size:')) {
                const size = trimmed.split('"')[1] || trimmed.split(':')[1].trim().replace(/"/g, '');
                if (size) document.getElementById('particleSize').value = size;
            }
            if (trimmed.startsWith('density:')) {
                const val = parseFloat(trimmed.split(':')[1]);
                if (!isNaN(val)) {
                    document.getElementById('particleDensity').value = Math.round(val * 100);
                    document.getElementById('particleDensityValue').textContent = Math.round(val * 100);
                }
            }
            if (trimmed.startsWith('application_rate:')) {
                const val = parseFloat(trimmed.split(':')[1]);
                if (!isNaN(val)) {
                    document.getElementById('particleRate').value = Math.round(val * 100);
                    document.getElementById('particleRateValue').textContent = Math.round(val * 100);
                }
            }
            if (trimmed.startsWith('apply_to_opening:')) {
                document.getElementById('particleOpening').checked = trimmed.includes('true');
            }
            if (trimmed.startsWith('apply_to_closing:')) {
                document.getElementById('particleClosing').checked = trimmed.includes('true');
            }
        }
    });

    updatePreview();
}

/**
 * File/Folder Selection Handlers
 */
function handleFolderSelect(event, targetId) {
    const files = event.target.files;
    if (files.length > 0) {
        // IMPORTANT: Browsers don't provide full paths for security reasons
        // We'll validate the folder contents and prompt user to paste the full path

        const feedbackDiv = document.getElementById(`${targetId}Feedback`);

        // Validate folder contents first
        if (targetId === 'imagesDir') {
            validateImageFolder(files);
            // Re-validate special photo after images are loaded
            validateSpecialPhoto();
        } else if (targetId === 'audioDir') {
            validateAudioFolder(files);
        }

        // Show instruction to paste full path
        const folderName = files[0].webkitRelativePath.split('/')[0];
        feedbackDiv.className = 'folder-feedback warning';
        feedbackDiv.innerHTML = `
            <strong>✓ Found folder: "${folderName}"</strong><br>
            <strong>⚠️ Action Required:</strong> Please paste the FULL path to this folder above.<br>
            <em>How to get the full path:</em><br>
            1. Open File Explorer and navigate to your folder<br>
            2. Click the address bar at the top<br>
            3. Copy the full path (Ctrl+C)<br>
            4. Paste it in the input field above<br>
            <em>Example: C:/Users/RAZ/Desktop/MyFolder</em>
        `;

        // Focus the input field so user can paste
        const inputField = document.getElementById(targetId);
        inputField.focus();
        inputField.select();

        updatePreview();
    }
}

function handleFileSelect(event, targetId) {
    const file = event.target.files[0];
    if (file) {
        // Just use the filename, not the full path
        document.getElementById(targetId).value = file.name;
        updatePreview();
    }
}

/**
 * Set quick path for output directory
 */
function setQuickPath(targetId, pathType) {
    const username = 'YourName'; // Placeholder - user will need to adjust
    let path = '';

    switch(pathType) {
        case 'Desktop':
            path = `C:/Users/${username}/Desktop`;
            break;
        case 'Videos':
            path = `C:/Users/${username}/Videos`;
            break;
        case 'Documents':
            path = `C:/Users/${username}/Documents`;
            break;
    }

    document.getElementById(targetId).value = path;

    // Show info message
    const feedbackDiv = document.getElementById('outputDirFeedback');
    feedbackDiv.className = 'folder-feedback warning';
    feedbackDiv.textContent = `ℹ️ Please update "YourName" with your actual Windows username, or paste the full path`;

    updatePreview();
}

/**
 * Browse for existing folder (for output directory)
 * Note: Browsers don't provide full paths for security reasons, so we prompt the user to paste
 */
function browseForExistingFolder(targetId) {
    const feedbackDiv = document.getElementById(`${targetId}Feedback`);

    // Show instruction to copy path from File Explorer
    feedbackDiv.className = 'folder-feedback warning';
    feedbackDiv.innerHTML = `
        <strong>📋 How to get folder path:</strong><br>
        1. Open File Explorer and navigate to your desired folder<br>
        2. Click on the address bar at the top<br>
        3. The full path will be highlighted - copy it (Ctrl+C)<br>
        4. Paste it into the Output Directory field above
    `;

    // Focus on the input field
    const inputField = document.getElementById(targetId);
    inputField.focus();
    inputField.select();
}

/**
 * Highlight and scroll to relevant YAML section when field is focused
 */
function highlightYAMLSection(fieldId) {
    // Map field IDs to YAML keywords/sections
    const yamlSectionMap = {
        'projectName': 'name:',
        'projectDescription': 'description:',
        'imagesDir': 'images_dir:',
        'audioDir': 'audio_dir:',
        'outputDir': 'output_file:',
        'specialPhoto': 'opening_closing:',
        'resolution': 'resolution:',
        'fps': 'fps:',
        'codec': 'codec:',
        'crf': 'crf:',
        'defaultDuration': 'default_duration:',
        'minDuration': 'min_duration:',
        'maxDuration': 'max_duration:',
        'transitionDuration': 'transition_duration:',
        'transGentle': 'transition_weights:',
        'transDynamic': 'transition_weights:',
        'transArtistic': 'transition_weights:',
        'kenBurns': 'ken_burns_intensity:',
        'colorGrading': 'color_grading_preset:',
        'openingText': 'opening_text:',
        'closingText': 'closing_text:'
    };

    const keyword = yamlSectionMap[fieldId];
    if (!keyword) return;

    const yamlPreview = document.querySelector('.yaml-preview');
    if (!yamlPreview) return;

    // Get text content (works with both text and HTML)
    const yamlContent = yamlPreview.innerText || yamlPreview.textContent;
    const lines = yamlContent.split('\n');

    // Find the line number containing the keyword
    let targetLineIndex = -1;
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes(keyword)) {
            targetLineIndex = i;
            break;
        }
    }

    if (targetLineIndex === -1) return;

    // Calculate approximate scroll position
    const lineHeight = 24; // Approximate line height in pixels
    const scrollPosition = targetLineIndex * lineHeight - 100; // Offset for better visibility

    // Smooth scroll to the section
    yamlPreview.scrollTo({
        top: Math.max(0, scrollPosition),
        behavior: 'smooth'
    });
}
