/**
 * API Module
 * Handles backend communication for video generation
 */

const API_BASE_URL = 'http://localhost:5000';

/**
 * Generate video via backend API
 */
function generateVideoNow() {
    // Close summary modal
    closeSummaryModal();

    // Show progress modal
    showProgressModal();

    // Get config
    const config = buildConfig();
    const yaml = generateYAML(config);
    const filename = (config.project.name || 'slideshow').replace(/\s+/g, '_').toLowerCase() + '.yaml';

    // Try to call backend API
    fetch(`${API_BASE_URL}/api/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            yaml_content: yaml,
            filename: filename,
            output_dir: config.paths.output_file.substring(0, config.paths.output_file.lastIndexOf('/'))
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showProgressSuccess(data.output_file, data.log_file);
        } else {
            showProgressError(data.error || 'Unknown error occurred');
        }
    })
    .catch(error => {
        // Backend not available - show manual instructions
        console.log('Backend not available, showing manual instructions:', error);
        showProgressManual(yaml, filename);
    });
}

/**
 * Check backend server health
 */
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        const data = await response.json();
        return data.status === 'healthy';
    } catch (error) {
        return false;
    }
}
