// Kaggriculture Web Arena Application Controller

(function () {
  'use strict';

  // --- STATE ---
  let simWorker = null;
  let isSimulating = false;
  let currentReplay = null;
  let currentSummary = null;

  // --- DOM ELEMENTS ---
  const elStatus = document.getElementById('engine-status');
  const elBtnStart = document.getElementById('btn-start-match');
  const elSeedInput = document.getElementById('match-seed');
  const elBtnRandomSeed = document.getElementById('btn-random-seed');
  const elTurnsSelect = document.getElementById('match-turns');

  // Player 0 Elements
  const elP0Name = document.getElementById('p0-name');
  const elP0Preset = document.getElementById('p0-preset');
  const elP0Dropzone = document.getElementById('p0-dropzone');
  const elP0FileInput = document.getElementById('p0-file-input');
  const elP0Filename = document.getElementById('p0-filename');
  const elP0Code = document.getElementById('p0-code');
  const elP0ToggleEditor = document.getElementById('p0-toggle-editor');

  // Player 1 Elements
  const elP1Name = document.getElementById('p1-name');
  const elP1Preset = document.getElementById('p1-preset');
  const elP1Dropzone = document.getElementById('p1-dropzone');
  const elP1FileInput = document.getElementById('p1-file-input');
  const elP1Filename = document.getElementById('p1-filename');
  const elP1Code = document.getElementById('p1-code');
  const elP1ToggleEditor = document.getElementById('p1-toggle-editor');

  // Progress Section
  const elProgressCard = document.getElementById('progress-card');
  const elProgressStatusText = document.getElementById('progress-status-text');
  const elProgressBar = document.getElementById('progress-bar');
  const elProgressDayTag = document.getElementById('progress-day-tag');
  const elProgressTurnTag = document.getElementById('progress-turn-tag');
  const elPreviewP0Name = document.getElementById('preview-p0-name');
  const elPreviewP1Name = document.getElementById('preview-p1-name');
  const elPreviewP0Money = document.getElementById('preview-p0-money');
  const elPreviewP1Money = document.getElementById('preview-p1-money');

  // Results Section
  const elResultsCard = document.getElementById('results-card');
  const elWinnerTitle = document.getElementById('winner-title');
  const elWinnerMargin = document.getElementById('winner-margin');
  const elResP0Label = document.getElementById('res-p0-label');
  const elResP1Label = document.getElementById('res-p1-label');
  const elResP0Val = document.getElementById('res-p0-val');
  const elResP1Val = document.getElementById('res-p1-val');
  const elLegendP0Name = document.getElementById('legend-p0-name');
  const elLegendP1Name = document.getElementById('legend-p1-name');

  // Stats Table
  const elThP0 = document.getElementById('th-p0');
  const elThP1 = document.getElementById('th-p1');
  const elStatP0Money = document.getElementById('stat-p0-money');
  const elStatP1Money = document.getElementById('stat-p1-money');
  const elStatP0Quads = document.getElementById('stat-p0-quads');
  const elStatP1Quads = document.getElementById('stat-p1-quads');
  const elStatP0Harvests = document.getElementById('stat-p0-harvests');
  const elStatP1Harvests = document.getElementById('stat-p1-harvests');
  const elStatP0Orders = document.getElementById('stat-p0-orders');
  const elStatP1Orders = document.getElementById('stat-p1-orders');
  const elStatP0Hires = document.getElementById('stat-p0-hires');
  const elStatP1Hires = document.getElementById('stat-p1-hires');
  const elStatP0Errors = document.getElementById('stat-p0-errors');
  const elStatP1Errors = document.getElementById('stat-p1-errors');

  // Visualizer Section
  const elVisCard = document.getElementById('visualizer-card');
  const elVisIframe = document.getElementById('visualizer-iframe');
  const elVisFrameContainer = document.getElementById('vis-frame-container');
  const elVisSeedBadge = document.getElementById('vis-seed-badge');
  const elBtnDownloadHtml = document.getElementById('btn-download-html');
  const elBtnDownloadJson = document.getElementById('btn-download-json');
  const elBtnFullscreen = document.getElementById('btn-fullscreen');

  // Load Replay
  const elBtnLoadReplay = document.getElementById('btn-load-replay');
  const elReplayFileInput = document.getElementById('replay-file-input');

  // Canvas
  const wealthCanvas = document.getElementById('wealthCanvas');

  // --- INITIALIZATION ---
  function initApp() {
    loadPresetsIntoUI();
    setupEventListeners();
    initWorker();
  }

  function loadPresetsIntoUI() {
    const presets = window.AGENT_PRESETS || {};
    if (presets.main) {
      elP0Code.value = presets.main;
    }
    if (presets.starter) {
      elP1Code.value = presets.starter;
    }
  }

  function initWorker() {
    if (window.Worker) {
      updateStatus('Initializing WebAssembly...', 'loading');
      simWorker = new Worker('sim_worker.js');

      simWorker.onmessage = function (e) {
        const msg = e.data;
        if (msg.type === 'STATUS') {
          updateStatus(msg.message, 'loading');
        } else if (msg.type === 'READY') {
          updateStatus('Python Engine Ready', 'ready');
        } else if (msg.type === 'PROGRESS') {
          handleProgressUpdate(msg);
        } else if (msg.type === 'MATCH_COMPLETE') {
          handleMatchComplete(msg.result);
        } else if (msg.type === 'ERROR') {
          handleMatchError(msg.error);
        }
      };

      simWorker.onerror = function (err) {
        console.error('Worker error:', err);
        updateStatus('Worker Error', 'error');
        alert('Worker initialization failed: ' + err.message);
      };

      // Send engine and runner scripts into worker
      simWorker.postMessage({
        type: 'INIT',
        enginePy: window.KAGGRICULTURE_ENGINE_PY || '',
        runnerPy: window.RUNNER_CORE_PY || ''
      });
    } else {
      updateStatus('Web Workers Not Supported', 'error');
      alert('Your browser does not support Web Workers. Please use a modern browser.');
    }
  }

  function updateStatus(text, state) {
    if (!elStatus) return;
    const label = elStatus.querySelector('.status-label');
    if (label) label.textContent = text;
    elStatus.className = 'status-chip ' + (state || '');
  }

  // --- PRESET & UPLOAD HANDLERS ---
  function setupEventListeners() {
    // Random Seed
    elBtnRandomSeed.addEventListener('click', () => {
      elSeedInput.value = Math.floor(Math.random() * 90000000) + 10000000;
    });

    // P0 Preset change
    elP0Preset.addEventListener('change', (e) => {
      handlePresetChange(e.target.value, elP0Name, elP0Code, elP0Dropzone, elP0Filename, 0);
    });

    // P1 Preset change
    elP1Preset.addEventListener('change', (e) => {
      handlePresetChange(e.target.value, elP1Name, elP1Code, elP1Dropzone, elP1Filename, 1);
    });

    // Toggle Code Editor
    elP0ToggleEditor.addEventListener('click', () => {
      elP0Code.focus();
    });
    elP1ToggleEditor.addEventListener('click', () => {
      elP1Code.focus();
    });

    // Setup Drag-Drop and File Chooser for P0
    setupDropzone(elP0Dropzone, elP0FileInput, elP0Filename, elP0Name, elP0Code);
    setupDropzone(elP1Dropzone, elP1FileInput, elP1Filename, elP1Name, elP1Code);

    // Start Simulation
    elBtnStart.addEventListener('click', startSimulation);

    // Download Replay HTML
    elBtnDownloadHtml.addEventListener('click', downloadReplayHtml);

    // Download Replay JSON
    elBtnDownloadJson.addEventListener('click', downloadReplayJson);

    // Load Replay File
    elBtnLoadReplay.addEventListener('click', () => elReplayFileInput.click());
    elReplayFileInput.addEventListener('change', handleReplayFileUpload);

    // Fullscreen Toggle
    elBtnFullscreen.addEventListener('click', () => {
      elVisFrameContainer.classList.toggle('fullscreen');
      elBtnFullscreen.textContent = elVisFrameContainer.classList.contains('fullscreen') ? '✕ Thu nhỏ' : '⛶ Toàn màn hình';
    });
  }

  function handlePresetChange(val, elName, elCode, elDropzone, elFilename, playerIdx) {
    const presets = window.AGENT_PRESETS || {};
    if (val === 'upload') {
      elDropzone.style.display = 'block';
    } else {
      elDropzone.style.display = 'none';
      elFilename.textContent = '';
      if (presets[val]) {
        elCode.value = presets[val];
        if (val === 'main') elName.value = 'Grandmaster Agent';
        else if (val === 'abc') elName.value = 'Adaptive Liquidation Agent';
        else if (val === 'starter') elName.value = 'Starter Baseline';
        else if (val === 'random') elName.value = 'Random Explorer';
        else if (val === 'pass') elName.value = 'Pass Agent';
      }
    }
  }

  function setupDropzone(dropzone, fileInput, filenameDisplay, nameInput, codeTextarea) {
    dropzone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        readFile(e.target.files[0], filenameDisplay, nameInput, codeTextarea);
      }
    });

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        readFile(e.dataTransfer.files[0], filenameDisplay, nameInput, codeTextarea);
      }
    });
  }

  function readFile(file, filenameDisplay, nameInput, codeTextarea) {
    const reader = new FileReader();
    reader.onload = (e) => {
      codeTextarea.value = e.target.result;
      filenameDisplay.textContent = '✓ ' + file.name;
      nameInput.value = file.name.replace(/\.py$/i, '');
    };
    reader.readAsText(file);
  }

  // --- SIMULATION EXECUTION ---
  function startSimulation() {
    if (isSimulating) return;

    const agent0Code = elP0Code.value.trim();
    const agent1Code = elP1Code.value.trim();

    if (!agent0Code) {
      alert('Vui lòng chọn hoặc nhập mã nguồn cho Player 0!');
      return;
    }
    if (!agent1Code) {
      alert('Vui lòng chọn hoặc nhập mã nguồn cho Player 1!');
      return;
    }

    const p0Name = elP0Name.value.trim() || 'Player 1';
    const p1Name = elP1Name.value.trim() || 'Player 2';
    const seed = elSeedInput.value ? parseInt(elSeedInput.value) : Math.floor(Math.random() * 90000000) + 10000000;
    const steps = parseInt(elTurnsSelect.value) || 720;

    isSimulating = true;
    elBtnStart.disabled = true;
    elBtnStart.innerHTML = '<span class="spinner"></span> ĐANG MÔ PHỎNG...';

    // Show Progress
    elProgressCard.style.display = 'block';
    elProgressBar.style.width = '0%';
    elProgressStatusText.textContent = 'Đang khởi chạy mô phỏng Kaggriculture...';
    elPreviewP0Name.textContent = p0Name;
    elPreviewP1Name.textContent = p1Name;
    elPreviewP0Money.textContent = '$3,000';
    elPreviewP1Money.textContent = '$3,000';

    simWorker.postMessage({
      type: 'RUN_MATCH',
      enginePy: window.KAGGRICULTURE_ENGINE_PY || '',
      runnerPy: window.RUNNER_CORE_PY || '',
      agent0Code,
      agent1Code,
      agent0Name: p0Name,
      agent1Name: p1Name,
      seed,
      episodeSteps: steps,
      startingMoney: 3000,
      boardSize: 10
    });
  }

  function handleProgressUpdate(data) {
    elProgressBar.style.width = data.percent + '%';
    elProgressDayTag.textContent = `Ngày ${String(data.day).padStart(2, '0')}/30`;
    elProgressTurnTag.textContent = `Turn ${data.step}/${data.total}`;
    elPreviewP0Money.textContent = '$' + Math.round(data.m0).toLocaleString();
    elPreviewP1Money.textContent = '$' + Math.round(data.m1).toLocaleString();
    elProgressStatusText.textContent = `Mô phỏng ngày ${data.day} (${data.percent}%)...`;
  }

  function handleMatchComplete(result) {
    isSimulating = false;
    elBtnStart.disabled = false;
    elBtnStart.innerHTML = '<span class="btn-icon-play">⚔️</span> BẮT ĐẦU ĐẤU (SIMULATE)';
    elProgressBar.style.width = '100%';
    elProgressStatusText.textContent = 'Trận đấu hoàn tất!';

    currentSummary = result.summary;
    currentReplay = result.replay;

    displayResults(currentSummary);
    renderVisualizer(currentReplay);

    // Scroll to results
    elResultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function handleMatchError(error) {
    isSimulating = false;
    elBtnStart.disabled = false;
    elBtnStart.innerHTML = '<span class="btn-icon-play">⚔️</span> BẮT ĐẦU ĐẤU (SIMULATE)';
    elProgressCard.style.display = 'none';
    alert('Lỗi mô phỏng: ' + error);
  }

  // --- DISPLAY RESULTS & ANALYTICS ---
  function displayResults(summary) {
    elResultsCard.style.display = 'block';

    const p0 = summary.agent0;
    const p1 = summary.agent1;

    // Winner Banner
    if (summary.winner === 'P0') {
      elWinnerTitle.textContent = `🎉 ${p0.name} Chiến Thắng!`;
      elWinnerMargin.textContent = `Chênh lệch: +$${Math.round(summary.difference).toLocaleString()} vàng • Thời gian tính toán: ${summary.execution_time_sec}s`;
    } else if (summary.winner === 'P1') {
      elWinnerTitle.textContent = `🎉 ${p1.name} Chiến Thắng!`;
      elWinnerMargin.textContent = `Chênh lệch: +$${Math.round(summary.difference).toLocaleString()} vàng • Thời gian tính toán: ${summary.execution_time_sec}s`;
    } else {
      elWinnerTitle.textContent = `🤝 Kết Quả Hòa!`;
      elWinnerMargin.textContent = `Cả 2 cùng đạt $${Math.round(p0.final_money).toLocaleString()} vàng`;
    }

    elResP0Label.textContent = `P0 (${p0.name})`;
    elResP1Label.textContent = `P1 (${p1.name})`;
    elResP0Val.textContent = '$' + Math.round(p0.final_money).toLocaleString();
    elResP1Val.textContent = '$' + Math.round(p1.final_money).toLocaleString();

    elLegendP0Name.textContent = p0.name;
    elLegendP1Name.textContent = p1.name;

    // Table Stats
    elThP0.textContent = p0.name;
    elThP1.textContent = p1.name;

    elStatP0Money.textContent = '$' + Math.round(p0.final_money).toLocaleString();
    elStatP1Money.textContent = '$' + Math.round(p1.final_money).toLocaleString();

    elStatP0Quads.textContent = `${p0.stats.quadrants} / 4`;
    elStatP1Quads.textContent = `${p1.stats.quadrants} / 4`;

    elStatP0Harvests.textContent = p0.stats.harvests.toLocaleString();
    elStatP1Harvests.textContent = p1.stats.harvests.toLocaleString();

    elStatP0Orders.textContent = p0.stats.market_orders.toLocaleString();
    elStatP1Orders.textContent = p1.stats.market_orders.toLocaleString();

    elStatP0Hires.textContent = p0.stats.hires.toLocaleString();
    elStatP1Hires.textContent = p1.stats.hires.toLocaleString();

    elStatP0Errors.textContent = p0.errors.length > 0 ? `${p0.errors.length} lỗi` : '0';
    elStatP1Errors.textContent = p1.errors.length > 0 ? `${p1.errors.length} lỗi` : '0';

    // Draw Wealth Timeline
    drawWealthChart(summary.timeline, p0.name, p1.name);
  }

  function drawWealthChart(timeline, p0Name, p1Name) {
    if (!wealthCanvas || !timeline || timeline.length === 0) return;
    const ctx = wealthCanvas.getContext('2d');
    const width = wealthCanvas.width;
    const height = wealthCanvas.height;

    ctx.clearRect(0, 0, width, height);

    const padding = { top: 30, right: 30, bottom: 40, left: 60 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    // Find max money
    let maxMoney = 3000;
    timeline.forEach(pt => {
      if (pt.p0_money > maxMoney) maxMoney = pt.p0_money;
      if (pt.p1_money > maxMoney) maxMoney = pt.p1_money;
    });
    maxMoney = Math.ceil(maxMoney * 1.1 / 1000) * 1000; // Round up nice

    // Draw Grid Lines & Y Axis
    ctx.strokeStyle = 'rgba(240, 246, 252, 0.08)';
    ctx.fillStyle = '#8b949e';
    ctx.font = '11px Outfit, sans-serif';
    ctx.textAlign = 'right';

    const ySteps = 4;
    for (let i = 0; i <= ySteps; i++) {
      const val = (maxMoney / ySteps) * i;
      const y = padding.top + chartH - (val / maxMoney) * chartH;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(padding.left + chartW, y);
      ctx.stroke();
      ctx.fillText('$' + Math.round(val).toLocaleString(), padding.left - 8, y + 4);
    }

    // Draw X Axis (Days)
    ctx.textAlign = 'center';
    const numPoints = timeline.length;
    const stepX = chartW / (numPoints - 1);

    for (let i = 0; i < numPoints; i += 5) {
      const x = padding.left + i * stepX;
      ctx.fillText(`D${timeline[i].day + 1}`, x, height - 15);
    }

    // Draw Line helper
    function drawLine(key, color, glowColor) {
      ctx.save();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.5;
      ctx.shadowColor = glowColor;
      ctx.shadowBlur = 10;
      ctx.beginPath();

      timeline.forEach((pt, idx) => {
        const x = padding.left + idx * stepX;
        const y = padding.top + chartH - (pt[key] / maxMoney) * chartH;
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();

      // Points
      ctx.fillStyle = color;
      timeline.forEach((pt, idx) => {
        if (idx % 5 === 0 || idx === numPoints - 1) {
          const x = padding.left + idx * stepX;
          const y = padding.top + chartH - (pt[key] / maxMoney) * chartH;
          ctx.beginPath();
          ctx.arc(x, y, 4, 0, Math.PI * 2);
          ctx.fill();
        }
      });
      ctx.restore();
    }

    // Draw P0 (Blue) and P1 (Red)
    drawLine('p0_money', '#388bfd', 'rgba(56, 139, 253, 0.4)');
    drawLine('p1_money', '#f85149', 'rgba(248, 81, 73, 0.4)');
  }

  // --- VISUALIZER RENDERER ---
  function renderVisualizer(replayData) {
    if (!elVisIframe || !replayData) return;

    elVisCard.style.display = 'block';
    const seed = replayData.configuration?.seed ?? 42;
    elVisSeedBadge.textContent = `Seed: ${seed}`;

    const header = window.VISUALIZER_HEADER || '';
    const footer = window.VISUALIZER_FOOTER || '';

    // Build the standalone HTML document
    const fullHtml = header + `\n<script>window.kaggle = ${JSON.stringify(replayData)};</script>\n` + footer;

    elVisIframe.srcdoc = fullHtml;
  }

  // --- REPLAY EXPORT & IMPORT ---
  function downloadReplayHtml() {
    if (!currentReplay) {
      alert('Chưa có dữ liệu trận đấu để tải về!');
      return;
    }

    const header = window.VISUALIZER_HEADER || '';
    const footer = window.VISUALIZER_FOOTER || '';
    const fullHtml = header + `\n<script>window.kaggle = ${JSON.stringify(currentReplay)};</script>\n` + footer;

    const blob = new Blob([fullHtml], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const seed = currentReplay.configuration?.seed ?? 'match';
    a.href = url;
    a.download = `kaggriculture_replay_seed${seed}.html`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function downloadReplayJson() {
    if (!currentReplay) {
      alert('Chưa có dữ liệu trận đấu để tải về!');
      return;
    }

    const blob = new Blob([JSON.stringify(currentReplay, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const seed = currentReplay.configuration?.seed ?? 'match';
    a.href = url;
    a.download = `replay_seed${seed}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleReplayFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target.result;
        let replayData = null;

        if (file.name.endsWith('.json')) {
          replayData = JSON.parse(text);
        } else if (file.name.endsWith('.html')) {
          // Extract window.kaggle = { ... }
          const match = text.match(/window\.kaggle\s*=\s*(\{[\s\S]*?\});/);
          if (match && match[1]) {
            replayData = JSON.parse(match[1]);
          } else {
            throw new Error('Không tìm thấy dữ liệu replay trong file HTML');
          }
        }

        if (replayData) {
          currentReplay = replayData;
          renderVisualizer(replayData);
          elVisCard.scrollIntoView({ behavior: 'smooth' });
          alert(`Đã tải thành công replay: ${file.name}`);
        }
      } catch (err) {
        alert('Lỗi đọc file replay: ' + err.message);
      }
    };
    reader.readAsText(file);
  }

  // Start app on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
  } else {
    initApp();
  }
})();
