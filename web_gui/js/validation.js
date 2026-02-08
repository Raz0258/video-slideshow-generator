/**
 * Validation Module
 * Handles all form validation logic
 */

// File validation data (shared state)
let fileValidation = {
    imageFiles: [],
    audioFiles: [],
    imageCount: 0,
    audioCount: 0
};

/**
 * Validate image folder contents
 */
function validateImageFolder(files) {
    const imageExtensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif'];
    const imageFiles = Array.from(files).filter(file => {
        const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
        return imageExtensions.includes(ext);
    });

    fileValidation.imageFiles = imageFiles;
    fileValidation.imageCount = imageFiles.length;

    const feedbackDiv = document.getElementById('imagesDirFeedback');

    // Show feedback ONLY if validation fails OR for informational success
    if (imageFiles.length >= 2) {
        feedbackDiv.className = 'folder-feedback success';
        feedbackDiv.textContent = `✅ Found ${imageFiles.length} images - looks good!`;
        // Auto-hide success message after 3 seconds
        setTimeout(() => {
            feedbackDiv.textContent = '';
            feedbackDiv.className = 'folder-feedback';
        }, 3000);
    } else if (imageFiles.length === 1) {
        feedbackDiv.className = 'folder-feedback warning';
        feedbackDiv.textContent = `⚠️ Found 1 image - need at least 2`;
    } else {
        feedbackDiv.className = 'folder-feedback error';
        feedbackDiv.textContent = `❌ No images found in this folder`;
    }
}

/**
 * Validate audio folder contents
 */
function validateAudioFolder(files) {
    const audioExtensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'];
    const audioFiles = Array.from(files).filter(file => {
        const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
        return audioExtensions.includes(ext);
    }).sort((a, b) => a.name.localeCompare(b.name)); // Sort alphabetically

    fileValidation.audioFiles = audioFiles;
    fileValidation.audioCount = audioFiles.length;

    const feedbackDiv = document.getElementById('audioDirFeedback');

    // Show feedback ONLY if validation fails OR for informational success
    if (audioFiles.length > 0) {
        feedbackDiv.className = 'folder-feedback success';
        if (audioFiles.length === 1) {
            feedbackDiv.textContent = `✅ Found 1 audio file: ${audioFiles[0].name}`;
        } else {
            feedbackDiv.textContent = `✅ Found ${audioFiles.length} audio files - will use: ${audioFiles[0].name} (first alphabetically)`;
        }
        // Auto-hide success message after 3 seconds
        setTimeout(() => {
            feedbackDiv.textContent = '';
            feedbackDiv.className = 'folder-feedback';
        }, 3000);
    } else {
        feedbackDiv.className = 'folder-feedback error';
        feedbackDiv.textContent = `❌ No audio files found`;
    }
}

/**
 * Validate special photo exists in image files
 */
function validateSpecialPhoto() {
    const specialPhotoInput = document.getElementById('specialPhoto');
    const specialPhotoName = specialPhotoInput.value.trim();
    const feedbackDiv = document.getElementById('specialPhotoFeedback');

    // If no filename entered yet, just clear feedback
    if (!specialPhotoName) {
        feedbackDiv.textContent = '';
        feedbackDiv.className = 'folder-feedback';
        return;
    }

    // Check if we have image files loaded
    if (!fileValidation.imageFiles || fileValidation.imageFiles.length === 0) {
        feedbackDiv.className = 'folder-feedback warning';
        feedbackDiv.textContent = '⚠️ Please select Images Directory first to validate this photo';
        return;
    }

    // Check if the special photo exists in the image files
    const imageExtensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif'];
    const specialPhotoExists = fileValidation.imageFiles.some(file => {
        return file.name.toLowerCase() === specialPhotoName.toLowerCase();
    });

    if (specialPhotoExists) {
        feedbackDiv.className = 'folder-feedback success';
        feedbackDiv.textContent = '✅ Photo found in images directory!';
        // Auto-hide success message after 3 seconds
        setTimeout(() => {
            feedbackDiv.textContent = '';
            feedbackDiv.className = 'folder-feedback';
        }, 3000);
    } else {
        // Check if it has a valid image extension
        const hasValidExtension = imageExtensions.some(ext =>
            specialPhotoName.toLowerCase().endsWith(ext)
        );

        if (!hasValidExtension) {
            feedbackDiv.className = 'folder-feedback error';
            feedbackDiv.textContent = '❌ File must have a valid image extension (.jpg, .png, etc.)';
        } else {
            feedbackDiv.className = 'folder-feedback error';
            feedbackDiv.textContent = '❌ Photo not found in images directory. Check the filename.';
        }
    }
}

/**
 * Validate single field
 */
function validateField(field) {
    const value = field.value.trim();
    if (!value) {
        field.classList.add('error');
        return false;
    } else {
        field.classList.remove('error');
        return true;
    }
}

/**
 * Validate transition weights sum to 100%
 */
function validateTransitionWeights() {
    const gentle = parseInt(document.getElementById('transGentle').value);
    const dynamic = parseInt(document.getElementById('transDynamic').value);
    const artistic = parseInt(document.getElementById('transArtistic').value);
    const total = gentle + dynamic + artistic;

    const warningDiv = document.getElementById('transitionWarning');
    const totalSpan = document.getElementById('currentTotal');
    const totalDisplay = document.getElementById('transitionTotal');
    const gentleSlider = document.getElementById('transGentle');
    const dynamicSlider = document.getElementById('transDynamic');
    const artisticSlider = document.getElementById('transArtistic');

    totalSpan.textContent = total;
    totalDisplay.textContent = `(Total: ${total}%)`;

    if (total !== 100) {
        warningDiv.classList.add('show');
        totalDisplay.classList.add('error');
        gentleSlider.classList.add('error-slider');
        dynamicSlider.classList.add('error-slider');
        artisticSlider.classList.add('error-slider');
    } else {
        warningDiv.classList.remove('show');
        totalDisplay.classList.remove('error');
        gentleSlider.classList.remove('error-slider');
        dynamicSlider.classList.remove('error-slider');
        artisticSlider.classList.remove('error-slider');
    }
}

/**
 * Highlight tabs with validation errors
 */
function highlightInvalidTabs() {
    // Map fields to their tabs
    const fieldToTab = {
        'projectName': 'project',
        'imagesDir': 'paths',
        'audioDir': 'paths',
        'outputDir': 'paths',
        'specialPhoto': 'paths'
    };

    // Track which tabs have errors
    const invalidTabs = new Set();

    // Check required fields
    const requiredFields = ['projectName', 'imagesDir', 'audioDir', 'outputDir', 'specialPhoto'];
    requiredFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (!field.value.trim()) {
            const tabName = fieldToTab[fieldId];
            if (tabName) {
                invalidTabs.add(tabName);
            }
        }
    });

    // Check transition weights
    const gentle = parseInt(document.getElementById('transGentle').value);
    const dynamic = parseInt(document.getElementById('transDynamic').value);
    const artistic = parseInt(document.getElementById('transArtistic').value);
    if (gentle + dynamic + artistic !== 100) {
        invalidTabs.add('effects');
    }

    // Update tab styling
    document.querySelectorAll('.tab').forEach(tab => {
        const tabName = tab.dataset.tab;
        if (invalidTabs.has(tabName)) {
            tab.classList.add('invalid');
        } else {
            tab.classList.remove('invalid');
        }
    });
}

/**
 * Validate all required fields
 */
function validateAll() {
    const requiredFields = ['projectName', 'imagesDir', 'audioDir', 'outputDir', 'specialPhoto'];
    let valid = true;
    const errors = [];

    requiredFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (!validateField(field)) {
            valid = false;
            // Safe way to get field label with null check
            let fieldLabel = fieldId;
            const labelElement = field.previousElementSibling;
            if (labelElement && labelElement.textContent) {
                fieldLabel = labelElement.textContent.replace(' *', '');
            } else if (field.placeholder) {
                fieldLabel = field.placeholder;
            } else if (field.id) {
                fieldLabel = field.id;
            }
            errors.push(`${fieldLabel} is required`);
        }
    });

    // Validate transition weights sum to 100
    const gentle = parseInt(document.getElementById('transGentle').value);
    const dynamic = parseInt(document.getElementById('transDynamic').value);
    const artistic = parseInt(document.getElementById('transArtistic').value);

    if (gentle + dynamic + artistic !== 100) {
        valid = false;
        errors.push('Transition weights must sum to 100%');
    }

    const statusDiv = document.getElementById('validationStatus');
    if (!valid) {
        statusDiv.className = 'validation-status error';
        statusDiv.innerHTML = '<strong>⚠️ Validation Errors:</strong><ul>' +
            errors.map(e => `<li>${e}</li>`).join('') + '</ul>';
    } else {
        statusDiv.className = 'validation-status success';
        statusDiv.innerHTML = '✅ Configuration is valid! You can now download the YAML file.';
    }

    // Highlight invalid tabs
    highlightInvalidTabs();

    return valid;
}

/**
 * Validate and show summary modal
 */
function validateAndGenerate() {
    if (validateAll()) {
        updatePreview();
        showSummaryModal();
    }
}

/**
 * Show validation message
 */
function showValidation(message, type) {
    const statusDiv = document.getElementById('validationStatus');
    statusDiv.className = `validation-status ${type}`;
    statusDiv.textContent = message;
}
