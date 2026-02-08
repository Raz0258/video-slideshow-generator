/**
 * Modals Module
 * Handles all modal dialogs (summary, progress, etc.)
 */

/**
 * Show configuration summary modal
 */
function showSummaryModal() {
    const config = buildConfig();

    // Populate summary
    document.getElementById('sum-project-name').textContent = config.project.name || 'Untitled';
    document.getElementById('sum-project-desc').textContent = config.project.description || 'No description';
    document.getElementById('sum-image-count').textContent = fileValidation.imageCount > 0 ? fileValidation.imageCount : 'Unknown (browse folder to detect)';

    const audioFileName = fileValidation.audioFiles.length > 0 ? fileValidation.audioFiles[0].name : 'Unknown (browse folder to detect)';
    document.getElementById('sum-audio-file').textContent = audioFileName;

    document.getElementById('sum-images-dir').textContent = config.paths.images_dir || '-';
    document.getElementById('sum-audio-dir').textContent = config.paths.audio_dir || '-';

    const res = config.video_settings.resolution;
    document.getElementById('sum-resolution').textContent = `${res[0]}×${res[1]}`;
    document.getElementById('sum-fps').textContent = `${config.video_settings.fps} FPS`;

    // Calculate estimated duration
    const imageCount = fileValidation.imageCount > 0 ? fileValidation.imageCount : 10; // Default estimate
    const imageDuration = config.sequences.images.duration_per_image;
    const openingDuration = config.sequences.opening.part1_duration + config.sequences.opening.part2_duration;
    const closingDuration = config.sequences.closing.min_duration;
    const totalSeconds = openingDuration + (imageCount * imageDuration) + closingDuration;
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = Math.floor(totalSeconds % 60);
    document.getElementById('sum-duration').textContent = `~${minutes}:${seconds.toString().padStart(2, '0')}`;

    document.getElementById('sum-output').textContent = config.paths.output_file;

    // Show modal
    document.getElementById('summaryModal').classList.add('active');
}

/**
 * Close configuration summary modal
 */
function closeSummaryModal() {
    document.getElementById('summaryModal').classList.remove('active');
}

/**
 * Show progress modal with loading state
 */
function showProgressModal() {
    document.getElementById('progress-title').textContent = '🎬 Generating Video';
    document.getElementById('progressContent').innerHTML = `
        <div class="spinner"></div>
        <div class="progress-message">Preparing video generation...</div>
        <div class="progress-details">This may take several minutes depending on video length and quality settings</div>
    `;
    document.getElementById('progressFooter').style.display = 'none';
    document.getElementById('progressModal').classList.add('active');
}

/**
 * Show progress modal with success state
 */
function showProgressSuccess(outputFile, logFile) {
    document.getElementById('progress-title').textContent = '✅ Video Created Successfully!';
    document.getElementById('progressContent').innerHTML = `
        <div class="status-icon">✅</div>
        <div class="progress-message">Your video has been created!</div>
        <div class="progress-details">
            <strong>Video location:</strong><br>
            ${outputFile}<br><br>
            <strong>Log file:</strong><br>
            ${logFile}
        </div>
    `;
    document.getElementById('progressFooter').style.display = 'flex';
    document.getElementById('progressFooter').innerHTML = `
        <button class="btn btn-secondary" onclick="closeProgressModal()">Close</button>
        <button class="btn btn-primary" onclick="openOutputFolder()">📁 Open Folder</button>
    `;
}

/**
 * Show progress modal with error state
 */
function showProgressError(errorMsg) {
    document.getElementById('progress-title').textContent = '❌ Error';
    document.getElementById('progressContent').innerHTML = `
        <div class="status-icon">❌</div>
        <div class="progress-message">Video generation failed</div>
        <div class="progress-details" style="color: #e74c3c;">
            ${errorMsg}
        </div>
    `;
    document.getElementById('progressFooter').style.display = 'flex';
    document.getElementById('progressFooter').innerHTML = `
        <button class="btn btn-primary" onclick="closeProgressModal()">Close</button>
    `;
}

/**
 * Show progress modal with manual instructions (server offline)
 */
function showProgressManual(yaml, filename) {
    document.getElementById('progress-title').textContent = '📥 Manual Generation Required';
    document.getElementById('progressContent').innerHTML = `
        <div class="status-icon">ℹ️</div>
        <div class="progress-message">Backend server not available</div>
        <div class="progress-details" style="text-align: left;">
            <p>To generate your video manually:</p>
            <ol style="margin: 15px 0; padding-left: 20px;">
                <li>Download the YAML configuration using the button below</li>
                <li>Save it to your project folder</li>
                <li>Open a command prompt in your project folder</li>
                <li>Run: <code style="background: #f0f0f0; padding: 2px 6px;">python create_slideshow_enhanced.py --config ${filename}</code></li>
            </ol>
            <p><strong>To enable automatic generation:</strong><br>
            Run the backend server: <code style="background: #f0f0f0; padding: 2px 6px;">python web_gui/server.py</code></p>
        </div>
    `;
    document.getElementById('progressFooter').style.display = 'flex';
    document.getElementById('progressFooter').innerHTML = `
        <button class="btn btn-secondary" onclick="closeProgressModal()">Close</button>
        <button class="btn btn-primary" onclick="downloadYAMLFromProgress('${filename}', \`${yaml.replace(/`/g, '\\`')}\`)">💾 Download YAML</button>
    `;
}

/**
 * Close progress modal
 */
function closeProgressModal() {
    document.getElementById('progressModal').classList.remove('active');
}

/**
 * Open output folder (browser limitation - shows alert)
 */
function openOutputFolder() {
    const config = buildConfig();
    const outputDir = config.paths.output_file.substring(0, config.paths.output_file.lastIndexOf('/'));
    alert(`Please open this folder manually:\n${outputDir}\n\n(Browser security prevents automatic folder opening)`);
}
