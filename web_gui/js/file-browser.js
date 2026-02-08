/**
 * Folder Browser Module
 * Provides folder browsing functionality with backend API integration
 */

// Global state for folder browser
const folderBrowser = {
    currentPath: '',
    targetFieldId: '',
    quickPaths: [],
    defaultPath: 'C:/Users/RAZ/Desktop/Raz-Technologies/Presentation_application',
    fileMode: false  // When true, shows image files and allows selecting them
};

/**
 * Open folder browser modal for a specific input field
 * @param {string} targetFieldId - ID of the input field to populate with selected path
 */
async function openFolderBrowser(targetFieldId) {
    folderBrowser.targetFieldId = targetFieldId;
    folderBrowser.fileMode = false;

    // Show modal
    const modal = document.getElementById('folderBrowserModal');
    if (!modal) {
        console.error('Folder browser modal not found');
        return;
    }
    modal.classList.add('active');

    // Update modal UI for folder mode
    const selectBtn = document.querySelector('#folderBrowserModal .modal-footer .btn-primary');
    if (selectBtn) selectBtn.textContent = 'Select This Folder';

    // Load quick paths
    await loadQuickPaths();

    // Determine starting path:
    // 1. If the target field already has a value, start there
    // 2. Otherwise, start at the application default path
    const targetField = document.getElementById(targetFieldId);
    const existingValue = targetField ? targetField.value.trim().replace(/\\/g, '/') : '';

    if (existingValue) {
        await browseFolderPath(existingValue);
    } else {
        await browseFolderPath(folderBrowser.defaultPath);
    }
}

/**
 * Open file browser modal - like folder browser but also shows image files
 * @param {string} targetFieldId - ID of the input field to populate with selected file path
 */
async function openFileBrowser(targetFieldId) {
    folderBrowser.targetFieldId = targetFieldId;
    folderBrowser.fileMode = true;

    // Show modal
    const modal = document.getElementById('folderBrowserModal');
    if (!modal) {
        console.error('Folder browser modal not found');
        return;
    }
    modal.classList.add('active');

    // Update modal UI for file mode - hide "Select This Folder" since user should click a file
    const selectBtn = document.querySelector('#folderBrowserModal .modal-footer .btn-primary');
    if (selectBtn) selectBtn.textContent = 'Select This Folder';

    // Load quick paths
    await loadQuickPaths();

    // Determine starting path:
    // 1. If the target field has a full file path, start in its parent directory
    // 2. If images directory is set, start there (special photo is usually in images dir)
    // 3. Otherwise, start at the application default path
    const targetField = document.getElementById(targetFieldId);
    const existingValue = targetField ? targetField.value.trim().replace(/\\/g, '/') : '';
    const imagesDirValue = document.getElementById('imagesDir') ?
        document.getElementById('imagesDir').value.trim().replace(/\\/g, '/') : '';

    if (existingValue && existingValue.includes('/')) {
        // Full path - start in parent directory
        const parentDir = existingValue.substring(0, existingValue.lastIndexOf('/'));
        await browseFolderPath(parentDir);
    } else if (imagesDirValue) {
        // Start in images directory
        await browseFolderPath(imagesDirValue);
    } else {
        await browseFolderPath(folderBrowser.defaultPath);
    }
}

/**
 * Close folder browser modal
 */
function closeFolderBrowser() {
    const modal = document.getElementById('folderBrowserModal');
    if (modal) {
        modal.classList.remove('active');
    }
    folderBrowser.fileMode = false;
}

/**
 * Load quick access paths from backend
 */
async function loadQuickPaths() {
    try {
        showBrowserLoading(true);

        const response = await fetch('http://localhost:5000/api/browse/quick-paths', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success && data.paths) {
            folderBrowser.quickPaths = data.paths;
            renderQuickPaths();
        } else {
            console.error('Failed to load quick paths:', data.error);
        }

        showBrowserLoading(false);
    } catch (error) {
        console.error('Error loading quick paths:', error);
        showBrowserLoading(false);
    }
}

/**
 * Render quick access paths in sidebar
 */
function renderQuickPaths() {
    const sidebar = document.getElementById('quickPathsList');
    if (!sidebar) return;

    sidebar.innerHTML = '';

    folderBrowser.quickPaths.forEach(pathObj => {
        const button = document.createElement('button');
        button.className = 'quick-path-item';
        button.textContent = pathObj.name;
        button.onclick = () => browseFolderPath(pathObj.path);
        sidebar.appendChild(button);
    });
}

/**
 * Browse folder at specified path
 * @param {string} path - Folder path to browse
 */
async function browseFolderPath(path) {
    try {
        showBrowserLoading(true);

        const requestBody = { path };
        if (folderBrowser.fileMode) {
            requestBody.include_images = true;
        }

        const response = await fetch('http://localhost:5000/api/browse/folder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();

        if (data.success) {
            folderBrowser.currentPath = data.current_path;
            renderBreadcrumb(data.current_path, data.parent_path);
            renderFolders(data.folders, data.files || []);
        } else {
            showBrowserError(data.error || 'Failed to browse folder');
        }

        showBrowserLoading(false);
    } catch (error) {
        console.error('Error browsing folder:', error);
        showBrowserError('Network error: Failed to browse folder');
        showBrowserLoading(false);
    }
}

/**
 * Render breadcrumb navigation
 * @param {string} currentPath - Current folder path
 * @param {string|null} parentPath - Parent folder path
 */
function renderBreadcrumb(currentPath, parentPath) {
    const breadcrumb = document.getElementById('browserBreadcrumb');
    if (!breadcrumb) return;

    breadcrumb.innerHTML = '';

    // Add "Up" button if not at root
    if (parentPath) {
        const upButton = document.createElement('button');
        upButton.className = 'breadcrumb-up';
        upButton.textContent = '← Up';
        upButton.onclick = () => browseFolderPath(parentPath);
        breadcrumb.appendChild(upButton);
    }

    // Add current path
    const pathSpan = document.createElement('span');
    pathSpan.className = 'breadcrumb-path';
    pathSpan.textContent = currentPath;
    breadcrumb.appendChild(pathSpan);
}

/**
 * Render folder list and optionally image files
 * @param {Array} folders - Array of folder objects {name, path}
 * @param {Array} files - Array of file objects {name, path} (image files in file mode)
 */
function renderFolders(folders, files) {
    const grid = document.getElementById('folderGrid');
    if (!grid) return;

    grid.innerHTML = '';

    if (folders.length === 0 && (!files || files.length === 0)) {
        grid.innerHTML = '<div class="no-folders">No subfolders' +
            (folderBrowser.fileMode ? ' or image files' : '') + ' found</div>';
        return;
    }

    // Render folders first
    folders.forEach(folder => {
        const folderDiv = document.createElement('div');
        folderDiv.className = 'folder-item';
        folderDiv.innerHTML = `
            <div class="folder-icon">📁</div>
            <div class="folder-name">${escapeHtml(folder.name)}</div>
        `;
        folderDiv.onclick = () => browseFolderPath(folder.path);
        grid.appendChild(folderDiv);
    });

    // Render image files (only in file mode)
    if (files && files.length > 0) {
        files.forEach(file => {
            const fileDiv = document.createElement('div');
            fileDiv.className = 'folder-item file-item';
            fileDiv.innerHTML = `
                <div class="folder-icon">🖼️</div>
                <div class="folder-name">${escapeHtml(file.name)}</div>
            `;
            fileDiv.onclick = () => selectFile(file.path);
            grid.appendChild(fileDiv);
        });
    }
}

/**
 * Select a file and close browser (used in file mode)
 * @param {string} filePath - Full path to the selected file
 */
function selectFile(filePath) {
    if (!folderBrowser.targetFieldId) {
        console.error('No target field ID set');
        return;
    }

    const targetField = document.getElementById(folderBrowser.targetFieldId);
    if (!targetField) {
        console.error('Target field not found:', folderBrowser.targetFieldId);
        return;
    }

    // Set the file path (already normalized with forward slashes from backend)
    targetField.value = filePath;

    // Trigger change event to update preview
    const event = new Event('input', { bubbles: true });
    targetField.dispatchEvent(event);

    // Close modal
    closeFolderBrowser();

    // Call updatePreview if it exists
    if (typeof updatePreview === 'function') {
        updatePreview();
    }
}

/**
 * Select current folder and close browser
 */
function selectCurrentFolder() {
    if (!folderBrowser.currentPath) {
        showBrowserError('No folder selected');
        return;
    }

    if (!folderBrowser.targetFieldId) {
        console.error('No target field ID set');
        return;
    }

    const targetField = document.getElementById(folderBrowser.targetFieldId);
    if (!targetField) {
        console.error('Target field not found:', folderBrowser.targetFieldId);
        return;
    }

    // Set the path (already normalized with forward slashes from backend)
    targetField.value = folderBrowser.currentPath;

    // Trigger change event to update preview
    const event = new Event('input', { bubbles: true });
    targetField.dispatchEvent(event);

    // Close modal
    closeFolderBrowser();

    // Call updatePreview if it exists
    if (typeof updatePreview === 'function') {
        updatePreview();
    }
}

/**
 * Show/hide loading spinner
 * @param {boolean} show - Whether to show loading spinner
 */
function showBrowserLoading(show) {
    const loading = document.getElementById('browserLoading');
    const content = document.getElementById('browserContent');

    if (loading) {
        loading.style.display = show ? 'flex' : 'none';
    }
    if (content) {
        content.style.display = show ? 'none' : 'block';
    }
}

/**
 * Show error message in browser
 * @param {string} message - Error message to display
 */
function showBrowserError(message) {
    const errorDiv = document.getElementById('browserError');
    if (!errorDiv) return;

    errorDiv.textContent = message;
    errorDiv.style.display = 'block';

    // Hide after 5 seconds
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal when clicking outside
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('folderBrowserModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeFolderBrowser();
            }
        });
    }
});
