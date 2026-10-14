/**
 * Vortex Media Studio - Interactive Frontend Engine
 */

document.addEventListener('DOMContentLoaded', () => {
  // --- DOM Elements ---
  const modeSwitcher = document.getElementById('modeSwitcher');
  const modeBtnVideo = document.getElementById('modeBtnVideo');
  const modeBtnAudio = document.getElementById('modeBtnAudio');

  const heroSection = document.getElementById('heroSection');
  const cardSelectVideo = document.getElementById('cardSelectVideo');
  const cardSelectAudio = document.getElementById('cardSelectAudio');

  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const dropzoneTargetText = document.getElementById('dropzoneTargetText');
  const uploadProgressCard = document.getElementById('uploadProgressCard');
  const uploadFileName = document.getElementById('uploadFileName');
  const uploadPercentage = document.getElementById('uploadPercentage');
  const uploadProgressBar = document.getElementById('uploadProgressBar');

  const workspaceSection = document.getElementById('workspaceSection');
  const mediaTypeBadge = document.getElementById('mediaTypeBadge');
  const metaFilename = document.getElementById('metaFilename');
  const metaDuration = document.getElementById('metaDuration');
  const metaSize = document.getElementById('metaSize');
  const metaResolution = document.getElementById('metaResolution');
  const metaCodec = document.getElementById('metaCodec');
  const btnReplaceFile = document.getElementById('btnReplaceFile');

  const videoPlayerWrap = document.getElementById('videoPlayerWrap');
  const audioPlayerWrap = document.getElementById('audioPlayerWrap');
  const videoElement = document.getElementById('videoElement');
  const audioElement = document.getElementById('audioElement');

  const currentTimecode = document.getElementById('currentTimecode');
  const rangeSliderStart = document.getElementById('rangeSliderStart');
  const rangeSliderEnd = document.getElementById('rangeSliderEnd');
  const rangeSelectedBar = document.getElementById('rangeSelectedBar');
  const inputStartTime = document.getElementById('inputStartTime');
  const inputEndTime = document.getElementById('inputEndTime');
  const btnSetStart = document.getElementById('btnSetStart');
  const btnSetEnd = document.getElementById('btnSetEnd');
  const selectedDurationVal = document.getElementById('selectedDurationVal');
  const btnPreviewSelection = document.getElementById('btnPreviewSelection');

  const opsTabsNav = document.getElementById('opsTabsNav');
  const paneVideoTrim = document.getElementById('paneVideoTrim');
  const paneVideoConvert = document.getElementById('paneVideoConvert');
  const paneVideoExtract = document.getElementById('paneVideoExtract');
  const paneAudioTrim = document.getElementById('paneAudioTrim');
  const paneAudioConvert = document.getElementById('paneAudioConvert');

  // Video Options Elements
  const videoTrimFormat = document.getElementById('videoTrimFormat');
  const btnExecuteVideoTrim = document.getElementById('btnExecuteVideoTrim');
  const videoTargetFormats = document.getElementById('videoTargetFormats');
  const videoResolution = document.getElementById('videoResolution');
  const videoCrf = document.getElementById('videoCrf');
  const crfValueDisplay = document.getElementById('crfValueDisplay');
  const btnExecuteVideoConvert = document.getElementById('btnExecuteVideoConvert');

  // Extract Audio Elements
  const extractAudioFormats = document.getElementById('extractAudioFormats');
  const extractBitrate = document.getElementById('extractBitrate');
  const extractTrimCheckbox = document.getElementById('extractTrimCheckbox');
  const extractStartDisp = document.getElementById('extractStartDisp');
  const extractEndDisp = document.getElementById('extractEndDisp');
  const btnExecuteExtractAudio = document.getElementById('btnExecuteExtractAudio');

  // Audio Options Elements
  const audioFadeIn = document.getElementById('audioFadeIn');
  const audioFadeOut = document.getElementById('audioFadeOut');
  const btnExecuteAudioTrim = document.getElementById('btnExecuteAudioTrim');
  const audioTargetFormats = document.getElementById('audioTargetFormats');
  const audioConvertBitrate = document.getElementById('audioConvertBitrate');
  const audioConvertSampleRate = document.getElementById('audioConvertSampleRate');
  const btnExecuteAudioConvert = document.getElementById('btnExecuteAudioConvert');

  // Results & Outputs
  const resultSection = document.getElementById('resultSection');
  const resultFilename = document.getElementById('resultFilename');
  const resultMeta = document.getElementById('resultMeta');
  const resultPreviewWrap = document.getElementById('resultPreviewWrap');
  const btnDownloadResult = document.getElementById('btnDownloadResult');
  const btnOpenFolderFromResult = document.getElementById('btnOpenFolderFromResult');

  const btnOpenFolder = document.getElementById('btnOpenFolder');
  const btnToggleOutputs = document.getElementById('btnToggleOutputs');
  const outputCountBadge = document.getElementById('outputCountBadge');
  const outputsDrawer = document.getElementById('outputsDrawer');
  const btnCloseDrawer = document.getElementById('btnCloseDrawer');
  const outputsListContainer = document.getElementById('outputsListContainer');
  const btnOpenDrawerFolder = document.getElementById('btnOpenDrawerFolder');

  const processingModal = document.getElementById('processingModal');
  const processingStatusText = document.getElementById('processingStatusText');
  const toastContainer = document.getElementById('toastContainer');

  // --- State ---
  let currentMode = 'video'; // 'video' | 'audio'
  let uploadedData = null;
  let duration = 0;
  let startTime = 0;
  let endTime = 0;
  let selectedVideoTargetFormat = 'mp4';
  let selectedExtractAudioFormat = 'mp3';
  let selectedAudioTargetFormat = 'mp3';
  let isPreviewingRange = false;

  // --- Helper Functions ---
  function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = document.createElement('span');
    icon.textContent = type === 'success' ? '✅' : '❌';
    const text = document.createElement('span');
    text.textContent = message;
    toast.append(icon, text);
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  function formatTimecode(seconds) {
    if (isNaN(seconds) || seconds < 0) seconds = 0;
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);
    return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
  }

  function parseTimecode(tc) {
    if (!tc) return 0;
    tc = tc.trim();
    if (tc.includes(':')) {
      const parts = tc.split(':');
      if (parts.length === 3) {
        return parseFloat(parts[0]) * 3600 + parseFloat(parts[1]) * 60 + parseFloat(parts[2]);
      } else if (parts.length === 2) {
        return parseFloat(parts[0]) * 60 + parseFloat(parts[1]);
      }
    }
    return parseFloat(tc) || 0;
  }

  function getActivePlayer() {
    return currentMode === 'video' ? videoElement : audioElement;
  }

  // --- Mode Switching ---
  function setMode(mode) {
    currentMode = mode;
    if (mode === 'video') {
      modeBtnVideo.classList.add('active');
      modeBtnAudio.classList.remove('active');
      dropzoneTargetText.textContent = 'Video';
      fileInput.accept = 'video/*,video/mp4,video/x-matroska,video/quicktime,video/webm';
    } else {
      modeBtnAudio.classList.add('active');
      modeBtnVideo.classList.remove('active');
      dropzoneTargetText.textContent = 'Audio';
      fileInput.accept = 'audio/*,audio/mpeg,audio/wav,audio/aac,audio/flac,audio/ogg';
    }
    updateOperationsNav();
  }

  modeBtnVideo.addEventListener('click', () => setMode('video'));
  modeBtnAudio.addEventListener('click', () => setMode('audio'));
  if (cardSelectVideo) cardSelectVideo.addEventListener('click', () => { setMode('video'); fileInput.click(); });
  if (cardSelectAudio) cardSelectAudio.addEventListener('click', () => { setMode('audio'); fileInput.click(); });

  // Update tabs for operations panel based on mode
  function updateOperationsNav() {
    opsTabsNav.innerHTML = '';

    if (currentMode === 'video') {
      opsTabsNav.innerHTML = `
        <button class="op-tab-btn active" data-pane="paneVideoTrim">✂️ Trim Video</button>
        <button class="op-tab-btn" data-pane="paneVideoConvert">🔄 Convert Video</button>
        <button class="op-tab-btn" data-pane="paneVideoExtract">🎧 Extract Audio</button>
      `;
      showPane(paneVideoTrim);
    } else {
      opsTabsNav.innerHTML = `
        <button class="op-tab-btn active" data-pane="paneAudioTrim">✂️ Trim Audio</button>
        <button class="op-tab-btn" data-pane="paneAudioConvert">🔄 Convert Audio</button>
      `;
      showPane(paneAudioTrim);
    }

    // Attach click listeners to tabs
    opsTabsNav.querySelectorAll('.op-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        opsTabsNav.querySelectorAll('.op-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const targetId = btn.getAttribute('data-pane');
        showPane(document.getElementById(targetId));
      });
    });
  }

  function showPane(paneToShow) {
    [paneVideoTrim, paneVideoConvert, paneVideoExtract, paneAudioTrim, paneAudioConvert].forEach(p => {
      if (p) p.classList.add('hidden');
    });
    if (paneToShow) paneToShow.classList.remove('hidden');
  }

  // --- Dropzone & Upload ---
  dropzone.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('drag-active');
  });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-active'));
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('drag-active');
    if (e.dataTransfer.files.length) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
      handleFileUpload(fileInput.files[0]);
    }
  });

  btnReplaceFile.addEventListener('click', () => fileInput.click());

  function handleFileUpload(file) {
    uploadProgressCard.classList.remove('hidden');
    uploadFileName.textContent = `Uploading: ${file.name}`;
    uploadPercentage.textContent = '0%';
    uploadProgressBar.style.width = '0%';

    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload', true);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100);
        uploadPercentage.textContent = `${percent}%`;
        uploadProgressBar.style.width = `${percent}%`;
      }
    };

    xhr.onload = () => {
      uploadProgressCard.classList.add('hidden');
      if (xhr.status === 200) {
        try {
          const res = JSON.parse(xhr.responseText);
          if (res.success) {
            loadMediaWorkspace(res);
            showToast(`Loaded ${file.name} successfully!`);
          } else {
            showToast(res.error || 'Upload error', 'error');
          }
        } catch (err) {
          showToast('Failed to parse server response', 'error');
        }
      } else {
        showToast('Upload failed: ' + xhr.statusText, 'error');
      }
    };

    xhr.onerror = () => {
      uploadProgressCard.classList.add('hidden');
      showToast('Network error during upload', 'error');
    };

    xhr.send(formData);
  }

  function loadMediaWorkspace(res) {
    uploadedData = res;
    const info = res.info;
    duration = info.duration || 10;
    startTime = 0;
    endTime = duration;

    // Detect if media is video or audio
    if (info.has_video) {
      setMode('video');
      videoPlayerWrap.classList.remove('hidden');
      audioPlayerWrap.classList.add('hidden');
      videoElement.src = res.stream_url;
      videoElement.load();
    } else {
      setMode('audio');
      videoPlayerWrap.classList.add('hidden');
      audioPlayerWrap.classList.remove('hidden');
      audioElement.src = res.stream_url;
      audioElement.load();
    }

    // Populate Meta Info
    mediaTypeBadge.textContent = info.media_type.toUpperCase();
    mediaTypeBadge.style.background = info.has_video ? 'var(--primary)' : 'var(--accent)';
    metaFilename.textContent = res.original_filename;
    metaDuration.textContent = `⏱️ ${info.duration_formatted}`;
    metaSize.textContent = `📦 ${info.size_formatted}`;

    if (info.video) {
      metaResolution.textContent = `📐 ${info.video.width}x${info.video.height} (${info.video.fps} fps)`;
      metaCodec.textContent = `🎞️ ${info.video.codec.toUpperCase()}`;
      metaResolution.classList.remove('hidden');
      metaCodec.classList.remove('hidden');
    } else {
      metaResolution.classList.add('hidden');
      metaCodec.textContent = info.audio ? `🔊 ${info.audio.codec.toUpperCase()} (${info.audio.sample_rate}Hz)` : '';
    }

    // Setup Timeline Ranges
    rangeSliderStart.max = duration;
    rangeSliderEnd.max = duration;
    rangeSliderStart.value = 0;
    rangeSliderEnd.value = duration;

    updateRangeMarkersUI();

    heroSection.classList.add('hidden');
    workspaceSection.classList.remove('hidden');
    resultSection.classList.add('hidden');

    window.scrollTo({ top: workspaceSection.offsetTop - 80, behavior: 'smooth' });
  }

  // --- Timeline & Scrubber Handlers ---
  function updateRangeMarkersUI() {
    inputStartTime.value = formatTimecode(startTime);
    inputEndTime.value = formatTimecode(endTime);

    const dur = Math.max(0, endTime - startTime);
    selectedDurationVal.textContent = formatTimecode(dur);

    // Update extract range badges
    extractStartDisp.textContent = formatTimecode(startTime);
    extractEndDisp.textContent = formatTimecode(endTime);

    // Update visual range track bar
    if (duration > 0) {
      const leftPct = (startTime / duration) * 100;
      const rightPct = (endTime / duration) * 100;
      rangeSelectedBar.style.left = `${leftPct}%`;
      rangeSelectedBar.style.width = `${Math.max(0, rightPct - leftPct)}%`;
    }
  }

  rangeSliderStart.addEventListener('input', (e) => {
    let val = parseFloat(e.target.value);
    if (val >= endTime) {
      val = Math.max(0, endTime - 0.1);
      e.target.value = val;
    }
    startTime = val;
    getActivePlayer().currentTime = startTime;
    updateRangeMarkersUI();
  });

  rangeSliderEnd.addEventListener('input', (e) => {
    let val = parseFloat(e.target.value);
    if (val <= startTime) {
      val = Math.min(duration, startTime + 0.1);
      e.target.value = val;
    }
    endTime = val;
    getActivePlayer().currentTime = endTime;
    updateRangeMarkersUI();
  });

  inputStartTime.addEventListener('change', () => {
    const val = parseTimecode(inputStartTime.value);
    startTime = Math.max(0, Math.min(val, endTime - 0.1));
    rangeSliderStart.value = startTime;
    getActivePlayer().currentTime = startTime;
    updateRangeMarkersUI();
  });

  inputEndTime.addEventListener('change', () => {
    const val = parseTimecode(inputEndTime.value);
    endTime = Math.min(duration, Math.max(val, startTime + 0.1));
    rangeSliderEnd.value = endTime;
    getActivePlayer().currentTime = endTime;
    updateRangeMarkersUI();
  });

  btnSetStart.addEventListener('click', () => {
    const player = getActivePlayer();
    const curr = player.currentTime;
    startTime = Math.min(curr, endTime - 0.05);
    rangeSliderStart.value = startTime;
    updateRangeMarkersUI();
    showToast(`Start marked at ${formatTimecode(startTime)}`);
  });

  btnSetEnd.addEventListener('click', () => {
    const player = getActivePlayer();
    const curr = player.currentTime;
    endTime = Math.max(curr, startTime + 0.05);
    rangeSliderEnd.value = endTime;
    updateRangeMarkersUI();
    showToast(`End marked at ${formatTimecode(endTime)}`);
  });

  btnPreviewSelection.addEventListener('click', () => {
    const player = getActivePlayer();
    player.currentTime = startTime;
    isPreviewingRange = true;
    player.play();
  });

  // Player Time Update
  function handleTimeUpdate(e) {
    const player = e.target;
    currentTimecode.textContent = formatTimecode(player.currentTime);

    if (isPreviewingRange && player.currentTime >= endTime) {
      player.pause();
      isPreviewingRange = false;
    }
  }

  videoElement.addEventListener('timeupdate', handleTimeUpdate);
  audioElement.addEventListener('timeupdate', handleTimeUpdate);

  // --- Format Picker Pill Listeners ---
  function setupPills(container, onSelect) {
    if (!container) return;
    container.querySelectorAll('.fmt-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        container.querySelectorAll('.fmt-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        onSelect(btn.getAttribute('data-fmt'));
      });
    });
  }

  setupPills(videoTargetFormats, (fmt) => selectedVideoTargetFormat = fmt);
  setupPills(extractAudioFormats, (fmt) => selectedExtractAudioFormat = fmt);
  setupPills(audioTargetFormats, (fmt) => selectedAudioTargetFormat = fmt);

  videoCrf.addEventListener('input', (e) => {
    const val = e.target.value;
    let label = 'Balanced';
    if (val <= 18) label = 'Near Lossless';
    else if (val <= 21) label = 'High Quality';
    else if (val <= 24) label = 'Balanced';
    else label = 'Compact Size';
    crfValueDisplay.textContent = `${label} (${val})`;
  });

  // --- Processing Engine Execution ---
  async function executeMediaProcess(payload, statusText) {
    if (!uploadedData) {
      showToast('Please upload a file first', 'error');
      return;
    }

    processingStatusText.textContent = statusText || 'Processing media locally with FFmpeg...';
    processingModal.classList.remove('hidden');

    try {
      const response = await fetch('/api/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const res = await response.json();
      processingModal.classList.add('hidden');

      if (res.success) {
        showToast(res.message || 'Complete!');
        displayProcessingResult(res);
        loadOutputsList();
      } else {
        showToast(res.error || 'Failed to process media', 'error');
        if (res.details) {
          console.error('FFmpeg error details:', res.details);
        }
      }
    } catch (err) {
      processingModal.classList.add('hidden');
      showToast('Network error while processing media', 'error');
      console.error(err);
    }
  }

  function displayProcessingResult(res) {
    resultFilename.textContent = res.output_filename;
    resultMeta.textContent = `Size: ${res.output_size_formatted} • Finished in ${res.elapsed_seconds}s`;
    btnDownloadResult.href = res.download_url;

    // Render Preview Player
    resultPreviewWrap.innerHTML = '';
    const isVideo = res.output_filename.match(/\.(mp4|mkv|mov|webm|avi)$/i);
    const isAudio = res.output_filename.match(/\.(mp3|wav|aac|flac|ogg|m4a|opus)$/i);

    if (isVideo) {
      const v = document.createElement('video');
      v.controls = true;
      v.src = res.stream_url;
      resultPreviewWrap.appendChild(v);
    } else if (isAudio) {
      const a = document.createElement('audio');
      a.controls = true;
      a.className = 'w-full';
      a.src = res.stream_url;
      resultPreviewWrap.appendChild(a);
    }

    resultSection.classList.remove('hidden');
    resultSection.scrollIntoView({ behavior: 'smooth' });
  }

  // Action 1: Trim Video
  btnExecuteVideoTrim.addEventListener('click', () => {
    const mode = document.querySelector('input[name="videoTrimMode"]:checked').value;
    const format = videoTrimFormat.value;
    executeMediaProcess({
      filename: uploadedData.filename,
      action: 'trim_video',
      start_time: startTime,
      end_time: endTime,
      target_format: format,
      copy_streams: mode === 'fast'
    }, `Trimming video from ${formatTimecode(startTime)} to ${formatTimecode(endTime)}...`);
  });

  // Action 2: Convert Video
  btnExecuteVideoConvert.addEventListener('click', () => {
    executeMediaProcess({
      filename: uploadedData.filename,
      action: 'convert_video',
      target_format: selectedVideoTargetFormat,
      resolution: videoResolution.value,
      crf: videoCrf.value
    }, `Converting video to ${selectedVideoTargetFormat.toUpperCase()} (${videoResolution.value})...`);
  });

  // Action 3: Extract Audio from Video
  btnExecuteExtractAudio.addEventListener('click', () => {
    const doTrim = extractTrimCheckbox.checked;
    executeMediaProcess({
      filename: uploadedData.filename,
      action: 'extract_audio',
      target_format: selectedExtractAudioFormat,
      bitrate: extractBitrate.value,
      trim: doTrim,
      start_time: doTrim ? startTime : null,
      end_time: doTrim ? endTime : null
    }, `Extracting ${selectedExtractAudioFormat.toUpperCase()} audio track...`);
  });

  // Action 4: Trim Audio
  btnExecuteAudioTrim.addEventListener('click', () => {
    executeMediaProcess({
      filename: uploadedData.filename,
      action: 'trim_audio',
      start_time: startTime,
      end_time: endTime,
      fade_in: parseFloat(audioFadeIn.value),
      fade_out: parseFloat(audioFadeOut.value)
    }, `Trimming audio from ${formatTimecode(startTime)} to ${formatTimecode(endTime)}...`);
  });

  // Action 5: Convert Audio
  btnExecuteAudioConvert.addEventListener('click', () => {
    executeMediaProcess({
      filename: uploadedData.filename,
      action: 'convert_audio',
      target_format: selectedAudioTargetFormat,
      bitrate: audioConvertBitrate.value,
      sample_rate: audioConvertSampleRate.value
    }, `Converting audio to ${selectedAudioTargetFormat.toUpperCase()} at ${audioConvertBitrate.value}...`);
  });

  // --- Output Folder & Outputs Library ---
  async function triggerOpenFolder() {
    try {
      const res = await fetch('/api/open-folder', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showToast('Opened outputs folder in Windows Explorer!');
      } else {
        showToast(data.error || 'Failed to open folder', 'error');
      }
    } catch (e) {
      showToast('Error opening folder', 'error');
    }
  }

  btnOpenFolder.addEventListener('click', triggerOpenFolder);
  btnOpenDrawerFolder.addEventListener('click', triggerOpenFolder);
  btnOpenFolderFromResult.addEventListener('click', triggerOpenFolder);

  btnToggleOutputs.addEventListener('click', () => {
    outputsDrawer.classList.toggle('open');
    if (outputsDrawer.classList.contains('open')) {
      loadOutputsList();
    }
  });

  btnCloseDrawer.addEventListener('click', () => outputsDrawer.classList.remove('open'));

  async function loadOutputsList() {
    try {
      const res = await fetch('/api/outputs');
      const data = await res.json();
      if (data.success) {
        outputCountBadge.textContent = data.outputs.length;
        renderOutputsList(data.outputs);
      }
    } catch (e) {
      console.error('Error loading outputs:', e);
    }
  }

  function renderOutputsList(items) {
    if (!items || items.length === 0) {
      outputsListContainer.innerHTML = `
        <div class="empty-state">
          <p>No processed files yet.</p>
          <p class="text-xs text-muted">Trimmed clips and converted tracks will appear here.</p>
        </div>
      `;
      return;
    }

    outputsListContainer.innerHTML = '';
    items.forEach(item => {
      const el = document.createElement('div');
      el.className = 'output-item';
      const icon = item.is_video ? '🎬' : '🎵';
      const info = document.createElement('div');
      info.className = 'output-item-info';
      const iconEl = document.createElement('div');
      iconEl.className = 'output-item-icon';
      iconEl.textContent = icon;
      const details = document.createElement('div');
      details.className = 'output-item-details';
      const name = document.createElement('div');
      name.className = 'output-item-name';
      name.title = item.name;
      name.textContent = item.name;
      const meta = document.createElement('div');
      meta.className = 'output-item-meta';
      meta.textContent = `${item.size_formatted} • ${item.created_at_formatted}`;
      details.append(name, meta);
      info.append(iconEl, details);

      const actions = document.createElement('div');
      actions.className = 'output-item-actions';
      const download = document.createElement('a');
      download.href = item.download_url;
      download.className = 'btn btn-secondary btn-xs';
      download.download = '';
      download.textContent = '⬇ Download';
      const deleteButton = document.createElement('button');
      deleteButton.className = 'btn btn-ghost btn-xs text-danger btn-delete-output';
      deleteButton.textContent = '🗑';
      actions.append(download, deleteButton);
      el.append(info, actions);

      deleteButton.addEventListener('click', async () => {
        const fname = item.name;
        if (confirm(`Delete ${fname}?`)) {
          const dres = await fetch(`/api/output/${encodeURIComponent(fname)}`, { method: 'DELETE' });
          if ((await dres.json()).success) {
            showToast(`Deleted ${fname}`);
            loadOutputsList();
          }
        }
      });

      outputsListContainer.appendChild(el);
    });
  }

  // Initial load of output library
  setMode('video');
  loadOutputsList();
});
