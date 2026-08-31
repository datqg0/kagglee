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
  const elStatP0Grade = document.getElementById('stat-p0-grade');
  const elStatP1Grade = document.getElementById('stat-p1-grade');
  const elStatP0Archetype = document.getElementById('stat-p0-archetype');
  const elStatP1Archetype = document.getElementById('stat-p1-archetype');
  const elStatP0Money = document.getElementById('stat-p0-money');
  const elStatP1Money = document.getElementById('stat-p1-money');
  const elStatP0PeakMoney = document.getElementById('stat-p0-peak-money');
  const elStatP1PeakMoney = document.getElementById('stat-p1-peak-money');
  const elStatP0Spend = document.getElementById('stat-p0-spend');
  const elStatP1Spend = document.getElementById('stat-p1-spend');
  const elStatP0Roi = document.getElementById('stat-p0-roi');
  const elStatP1Roi = document.getElementById('stat-p1-roi');
  const elStatP0RevTurn = document.getElementById('stat-p0-rev-turn');
  const elStatP1RevTurn = document.getElementById('stat-p1-rev-turn');
  const elStatP0Quads = document.getElementById('stat-p0-quads');
  const elStatP1Quads = document.getElementById('stat-p1-quads');
  const elStatP0Plants = document.getElementById('stat-p0-plants');
  const elStatP1Plants = document.getElementById('stat-p1-plants');
  const elStatP0Waters = document.getElementById('stat-p0-waters');
  const elStatP1Waters = document.getElementById('stat-p1-waters');
  const elStatP0Harvests = document.getElementById('stat-p0-harvests');
  const elStatP1Harvests = document.getElementById('stat-p1-harvests');
  const elStatP0Fertilizes = document.getElementById('stat-p0-fertilizes');
  const elStatP1Fertilizes = document.getElementById('stat-p1-fertilizes');
  const elStatP0Digs = document.getElementById('stat-p0-digs');
  const elStatP1Digs = document.getElementById('stat-p1-digs');
  const elStatP0AnimalsBought = document.getElementById('stat-p0-animals-bought');
  const elStatP1AnimalsBought = document.getElementById('stat-p1-animals-bought');
  const elStatP0Feeds = document.getElementById('stat-p0-feeds');
  const elStatP1Feeds = document.getElementById('stat-p1-feeds');
  const elStatP0Cares = document.getElementById('stat-p0-cares');
  const elStatP1Cares = document.getElementById('stat-p1-cares');
  const elStatP0FertilizerCollected = document.getElementById('stat-p0-fertilizer-collected');
  const elStatP1FertilizerCollected = document.getElementById('stat-p1-fertilizer-collected');
  const elStatP0Orders = document.getElementById('stat-p0-orders');
  const elStatP1Orders = document.getElementById('stat-p1-orders');
  const elStatP0Hires = document.getElementById('stat-p0-hires');
  const elStatP1Hires = document.getElementById('stat-p1-hires');
  const elStatP0Efficiency = document.getElementById('stat-p0-efficiency');
  const elStatP1Efficiency = document.getElementById('stat-p1-efficiency');
  const elStatP0ActionSplit = document.getElementById('stat-p0-action-split');
  const elStatP1ActionSplit = document.getElementById('stat-p1-action-split');
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
    if (presets.v4) {
      elP0Code.value = presets.v4;
      elP0Name.value = 'Apex V4 (Grandmaster)';
    } else if (presets.v3) {
      elP0Code.value = presets.v3;
      elP0Name.value = 'Submission V3';
    } else if (presets.dg) {
      elP0Code.value = presets.dg;
      elP0Name.value = 'DG Agent';
    } else if (presets.rlv2) {
      elP0Code.value = presets.rlv2;
      elP0Name.value = 'RL Policy V2';
    } else if (presets.miss) {
      elP0Code.value = presets.miss;
      elP0Name.value = 'Miss Agent';
    } else if (presets.edf) {
      elP0Code.value = presets.edf;
      elP0Name.value = 'EDF Agent';
    } else if (presets.rl) {
      elP0Code.value = presets.rl;
      elP0Name.value = 'RL Agent';
    } else if (presets.main) {
      elP0Code.value = presets.main;
    }
    if (presets.v3) {
      elP1Code.value = presets.v3;
      elP1Name.value = 'Submission V3';
    } else if (presets.submission) {
      elP1Code.value = presets.submission;
      elP1Name.value = 'Baseline';
    } else if (presets.miss) {
      elP1Code.value = presets.miss;
      elP1Name.value = 'Miss Agent';
    } else if (presets.rlv2) {
      elP1Code.value = presets.rlv2;
      elP1Name.value = 'RL Policy V2';
    } else if (presets.main) {
      elP1Code.value = presets.main;
      elP1Name.value = 'Grandmaster Agent';
    } else if (presets.starter) {
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
        } else if (msg.type === 'MATCH_COMPLETE' || msg.type === 'COMPLETE') {
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
        runnerPy: window.KAGGRICULTURE_RUNNER_CORE_PY || window.RUNNER_CORE_PY || ''
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
    elBtnRandomSeed.addEventListener('click', (e) => {
      e.preventDefault();
      const newSeed = Math.floor(Math.random() * 90000000) + 10000000;
      elSeedInput.value = newSeed;
      elBtnRandomSeed.style.transform = 'rotate(360deg)';
      elBtnRandomSeed.style.transition = 'transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)';
      setTimeout(() => {
        elBtnRandomSeed.style.transform = '';
        elBtnRandomSeed.style.transition = '';
      }, 300);
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
      elBtnFullscreen.textContent = elVisFrameContainer.classList.contains('fullscreen') ? '✕ Exit Fullscreen' : '⛶ Fullscreen';
    });
  }

  function handlePresetChange(val, elName, elCode, elDropzone, elFilename, playerIdx) {
    const presets = window.AGENT_PRESETS || {};
    delete elCode.dataset.archivePayload;
    if (val === 'upload') {
      elDropzone.style.display = 'block';
    } else {
      elDropzone.style.display = 'none';
      elFilename.textContent = '';
      if (presets[val]) {
        elCode.value = presets[val];
        if (val === 'v4' || val === 'apex') elName.value = 'Apex V4 (Grandmaster)';
        else if (val === 'v3') elName.value = 'Submission V3';
        else if (val === 'dg') elName.value = 'DG Agent';
        else if (val === 'submission') elName.value = 'Baseline';
        else if (val === 'rlv2') elName.value = 'RL Policy V2';
        else if (val === 'miss') elName.value = 'Miss Agent';
        else if (val === 'edf') elName.value = 'EDF Agent';
        else if (val === 'rl') elName.value = 'RL Agent';
        else if (val === 'main') elName.value = 'Grandmaster';
        else if (val === 'abc') elName.value = 'ABC Agent';
        else if (val === 'starter') elName.value = 'Starter';
        else if (val === 'random') elName.value = 'Random';
        else if (val === 'pass') elName.value = 'Pass';
      }
    }
  }

  function setupDropzone(dropzone, fileInput, filenameDisplay, nameInput, codeTextarea) {
    codeTextarea.addEventListener('input', () => {
      delete codeTextarea.dataset.archivePayload;
    });

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
    const isArchive = /\.(tar\.gz|tgz|tar|zip)$/i.test(file.name);

    if (isArchive) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const dataUrl = e.target.result;
        const b64 = dataUrl.split(',')[1] || '';
        const payload = `__ARCHIVE_BASE64__:${file.name}:${b64}`;
        codeTextarea.dataset.archivePayload = payload;
        codeTextarea.value = `# =====================================================================\n# 📦 ARCHIVE PACKAGE LOADED: ${file.name}\n# Size: ${(file.size / 1024).toFixed(1)} KB\n# =====================================================================\n# Multi-file Python Package (.tar.gz / .zip)\n#\n# The simulation engine will automatically:\n# 1. Unpack all Python source files and submodules.\n# 2. Add package directories to sys.path.\n# 3. Locate the entry point: checks main.py / agent.py or any .py with agent(obs) / main(obs).\n# 4. Execute the match in full 720 turns!\n# =====================================================================`;
        filenameDisplay.textContent = '✓ ' + file.name;
        nameInput.value = file.name.replace(/\.(tar\.gz|tgz|tar|zip)$/i, '');
      };
      reader.readAsDataURL(file);
    } else {
      delete codeTextarea.dataset.archivePayload;
      const reader = new FileReader();
      reader.onload = (e) => {
        codeTextarea.value = e.target.result;
        filenameDisplay.textContent = '✓ ' + file.name;
        nameInput.value = file.name.replace(/\.py$/i, '');
      };
      reader.readAsText(file);
    }
  }

  // --- SIMULATION EXECUTION ---
  function startSimulation() {
    if (isSimulating) return;

    const agent0Code = elP0Code.dataset.archivePayload || elP0Code.value.trim();
    const agent1Code = elP1Code.dataset.archivePayload || elP1Code.value.trim();

    if (!agent0Code) {
      alert('Please select or provide Python code for Player 0!');
      return;
    }
    if (!agent1Code) {
      alert('Please select or provide Python code for Player 1!');
      return;
    }

    const p0Name = elP0Name.value.trim() || 'Player 1';
    const p1Name = elP1Name.value.trim() || 'Player 2';
    const seed = elSeedInput.value ? parseInt(elSeedInput.value) : Math.floor(Math.random() * 90000000) + 10000000;
    const steps = parseInt(elTurnsSelect.value) || 720;

    isSimulating = true;
    elBtnStart.disabled = true;
    elBtnStart.innerHTML = '<span class="spinner"></span> SIMULATING...';

    // Show Progress
    elProgressCard.style.display = 'block';
    elProgressBar.style.width = '0%';
    elProgressStatusText.textContent = 'Initializing Kaggriculture simulation...';
    elPreviewP0Name.textContent = p0Name;
    elPreviewP1Name.textContent = p1Name;
    elPreviewP0Money.textContent = '$3,000';
    elPreviewP1Money.textContent = '$3,000';

    simWorker.postMessage({
      type: 'RUN_MATCH',
      enginePy: window.KAGGRICULTURE_ENGINE_PY || window.ENGINE_PY || '',
      runnerPy: window.KAGGRICULTURE_RUNNER_CORE_PY || window.RUNNER_CORE_PY || '',
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
    elProgressDayTag.textContent = `Day ${String(data.day).padStart(2, '0')}/30`;
    elProgressTurnTag.textContent = `Turn ${data.step}/${data.total}`;
    elPreviewP0Money.textContent = '$' + Math.round(data.m0).toLocaleString();
    elPreviewP1Money.textContent = '$' + Math.round(data.m1).toLocaleString();
    elProgressStatusText.textContent = `Simulating Day ${data.day} (${data.percent}%)...`;
  }

  function handleMatchComplete(result) {
    isSimulating = false;
    elBtnStart.disabled = false;
    elBtnStart.innerHTML = '<span class="btn-icon-play">⚔️</span> START BATTLE (SIMULATE)';
    elProgressBar.style.width = '100%';
    elProgressStatusText.textContent = 'Match simulation complete!';

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
    elBtnStart.innerHTML = '<span class="btn-icon-play">⚔️</span> START BATTLE (SIMULATE)';
    elProgressCard.style.display = 'none';
    alert('Simulation error: ' + error);
  }

  // --- DISPLAY RESULTS & ANALYTICS ---
  function displayResults(summary) {
    elResultsCard.style.display = 'block';

    const p0 = summary.agent0;
    const p1 = summary.agent1;

    // Winner Banner
    if (summary.winner === 'P0') {
      elWinnerTitle.textContent = `🎉 ${p0.name} Victorious!`;
      elWinnerMargin.textContent = `Margin: +$${Math.round(summary.difference).toLocaleString()} gold • Runtime: ${summary.execution_time_sec}s`;
    } else if (summary.winner === 'P1') {
      elWinnerTitle.textContent = `🎉 ${p1.name} Victorious!`;
      elWinnerMargin.textContent = `Margin: +$${Math.round(summary.difference).toLocaleString()} gold • Runtime: ${summary.execution_time_sec}s`;
    } else {
      elWinnerTitle.textContent = `🤝 Draw Match!`;
      elWinnerMargin.textContent = `Both players tied at $${Math.round(p0.final_money).toLocaleString()} gold`;
    }

    elResP0Label.textContent = `P0 (${p0.name})`;
    elResP1Label.textContent = `P1 (${p1.name})`;
    elResP0Val.textContent = '$' + Math.round(p0.final_money).toLocaleString();
    elResP1Val.textContent = '$' + Math.round(p1.final_money).toLocaleString();

    elLegendP0Name.textContent = p0.name;
    elLegendP1Name.textContent = p1.name;

    // In-Depth Quant Table Stats
    elThP0.textContent = p0.name;
    elThP1.textContent = p1.name;

    const s0 = p0.stats || {};
    const s1 = p1.stats || {};

    if (elStatP0Grade) elStatP0Grade.textContent = s0.quant_grade || 'A';
    if (elStatP1Grade) elStatP1Grade.textContent = s1.quant_grade || 'A';

    if (elStatP0Archetype) elStatP0Archetype.textContent = s0.archetype || '🚜 Generalist Farmer';
    if (elStatP1Archetype) elStatP1Archetype.textContent = s1.archetype || '🚜 Generalist Farmer';

    elStatP0Money.textContent = '$' + Math.round(p0.final_money).toLocaleString();
    elStatP1Money.textContent = '$' + Math.round(p1.final_money).toLocaleString();

    if (elStatP0PeakMoney) elStatP0PeakMoney.textContent = '$' + Math.round(s0.peak_money || p0.final_money).toLocaleString();
    if (elStatP1PeakMoney) elStatP1PeakMoney.textContent = '$' + Math.round(s1.peak_money || p1.final_money).toLocaleString();

    if (elStatP0Spend) elStatP0Spend.textContent = '$' + Math.round(s0.total_spend || 0).toLocaleString();
    if (elStatP1Spend) elStatP1Spend.textContent = '$' + Math.round(s1.total_spend || 0).toLocaleString();

    if (elStatP0Roi) elStatP0Roi.textContent = `${s0.roi_pct > 0 ? '+' : ''}${s0.roi_pct ?? 0}%`;
    if (elStatP1Roi) elStatP1Roi.textContent = `${s1.roi_pct > 0 ? '+' : ''}${s1.roi_pct ?? 0}%`;

    if (elStatP0RevTurn) elStatP0RevTurn.textContent = `$${(s0.revenue_per_worker_turn || 0).toFixed(2)} / turn`;
    if (elStatP1RevTurn) elStatP1RevTurn.textContent = `$${(s1.revenue_per_worker_turn || 0).toFixed(2)} / turn`;

    elStatP0Quads.textContent = `${s0.quadrants || 1} / 4`;
    elStatP1Quads.textContent = `${s1.quadrants || 1} / 4`;

    if (elStatP0Plants) elStatP0Plants.textContent = (s0.plants || 0).toLocaleString();
    if (elStatP1Plants) elStatP1Plants.textContent = (s1.plants || 0).toLocaleString();

    if (elStatP0Waters) elStatP0Waters.textContent = (s0.waters || 0).toLocaleString();
    if (elStatP1Waters) elStatP1Waters.textContent = (s1.waters || 0).toLocaleString();

    elStatP0Harvests.textContent = (s0.harvests || 0).toLocaleString();
    elStatP1Harvests.textContent = (s1.harvests || 0).toLocaleString();

    if (elStatP0Fertilizes) elStatP0Fertilizes.textContent = (s0.fertilizes || 0).toLocaleString();
    if (elStatP1Fertilizes) elStatP1Fertilizes.textContent = (s1.fertilizes || 0).toLocaleString();

    if (elStatP0Digs) elStatP0Digs.textContent = (s0.digs || 0).toLocaleString();
    if (elStatP1Digs) elStatP1Digs.textContent = (s1.digs || 0).toLocaleString();

    if (elStatP0AnimalsBought) elStatP0AnimalsBought.textContent = (s0.animals_bought || 0).toLocaleString();
    if (elStatP1AnimalsBought) elStatP1AnimalsBought.textContent = (s1.animals_bought || 0).toLocaleString();

    if (elStatP0Feeds) elStatP0Feeds.textContent = (s0.feeds || 0).toLocaleString();
    if (elStatP1Feeds) elStatP1Feeds.textContent = (s1.feeds || 0).toLocaleString();

    if (elStatP0Cares) elStatP0Cares.textContent = (s0.cares || 0).toLocaleString();
    if (elStatP1Cares) elStatP1Cares.textContent = (s1.cares || 0).toLocaleString();

    if (elStatP0FertilizerCollected) elStatP0FertilizerCollected.textContent = (s0.fertilizer_collected || 0).toLocaleString();
    if (elStatP1FertilizerCollected) elStatP1FertilizerCollected.textContent = (s1.fertilizer_collected || 0).toLocaleString();

    elStatP0Orders.textContent = (s0.market_orders || 0).toLocaleString();
    elStatP1Orders.textContent = (s1.market_orders || 0).toLocaleString();

    elStatP0Hires.textContent = (s0.hires || 0).toLocaleString();
    elStatP1Hires.textContent = (s1.hires || 0).toLocaleString();

    if (elStatP0Efficiency) elStatP0Efficiency.textContent = `${s0.worker_efficiency ?? 0}%`;
    if (elStatP1Efficiency) elStatP1Efficiency.textContent = `${s1.worker_efficiency ?? 0}%`;

    function formatActionSplit(st) {
      const tot = st.total_worker_turns || 1;
      const walk = Math.round((st.movement_turns || 0) / tot * 100);
      const farm = Math.round((st.farming_turns || 0) / tot * 100);
      const ranch = Math.round((st.ranching_turns || 0) / tot * 100);
      const idle = Math.round((st.idle_turns || 0) / tot * 100);
      return `🚶${walk}% • 🌾${farm}% • 🐄${ranch}% • 💤${idle}%`;
    }

    if (elStatP0ActionSplit) elStatP0ActionSplit.textContent = formatActionSplit(s0);
    if (elStatP1ActionSplit) elStatP1ActionSplit.textContent = formatActionSplit(s1);

    elStatP0Errors.textContent = p0.errors.length > 0 ? `${p0.errors.length} error(s)` : '0';
    elStatP1Errors.textContent = p1.errors.length > 0 ? `${p1.errors.length} error(s)` : '0';

    // Draw Wealth Timeline
    requestAnimationFrame(() => {
      drawWealthChart(summary.timeline, p0.name, p1.name);
    });
  }

  function extractTimelineFromReplay(replay) {
    if (!replay || !replay.steps || replay.steps.length === 0) return [];
    const timeline = [];
    const steps = replay.steps;
    const totalSteps = steps.length;
    for (let s = 0; s < totalSteps; s += 24) {
      const stepData = steps[s];
      const day = Math.floor(s / 24);
      let m0 = 3000, m1 = 3000;
      if (stepData && stepData[0] && stepData[0].observation && stepData[0].observation.farms) {
        m0 = stepData[0].observation.farms[0]?.money ?? 3000;
        m1 = stepData[0].observation.farms[1]?.money ?? 3000;
      }
      timeline.push({ day, p0_money: Math.round(m0), p1_money: Math.round(m1) });
    }
    // Add final step if not on boundary
    if (totalSteps > 0 && (totalSteps - 1) % 24 !== 0) {
      const lastStep = steps[totalSteps - 1];
      const day = Math.floor((totalSteps - 1) / 24);
      let m0 = 3000, m1 = 3000;
      if (lastStep && lastStep[0] && lastStep[0].observation && lastStep[0].observation.farms) {
        m0 = lastStep[0].observation.farms[0]?.money ?? 3000;
        m1 = lastStep[0].observation.farms[1]?.money ?? 3000;
      }
      timeline.push({ day, p0_money: Math.round(m0), p1_money: Math.round(m1) });
    }
    return timeline;
  }

  function drawWealthChart(timeline, p0Name, p1Name) {
    if (!wealthCanvas) return;
    if (!timeline || timeline.length === 0) {
      timeline = extractTimelineFromReplay(currentReplay);
    }
    if (!timeline || timeline.length === 0) return;

    const rect = wealthCanvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const displayWidth = rect.width > 0 ? rect.width : 700;
    const displayHeight = rect.height > 0 ? rect.height : 260;

    wealthCanvas.width = displayWidth * dpr;
    wealthCanvas.height = displayHeight * dpr;

    const ctx = wealthCanvas.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, displayWidth, displayHeight);

    const padding = { top: 25, right: 25, bottom: 35, left: 55 };
    const chartW = displayWidth - padding.left - padding.right;
    const chartH = displayHeight - padding.top - padding.bottom;

    // Find max money with nice ceiling
    let maxMoney = 3000;
    timeline.forEach(pt => {
      if (pt.p0_money > maxMoney) maxMoney = pt.p0_money;
      if (pt.p1_money > maxMoney) maxMoney = pt.p1_money;
    });
    maxMoney = Math.ceil(maxMoney * 1.15 / 1000) * 1000;

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
    const stepX = chartW / Math.max(1, numPoints - 1);

    for (let i = 0; i < numPoints; i += Math.max(1, Math.floor(numPoints / 6))) {
      const x = padding.left + i * stepX;
      ctx.fillText(`D${timeline[i].day + 1}`, x, displayHeight - 12);
    }

    // Draw Curve with Area Gradient
    function drawLine(key, color, glowColor, gradientStart) {
      if (numPoints <= 0) return;
      ctx.save();

      // Area fill gradient
      const grad = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartH);
      grad.addColorStop(0, gradientStart);
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

      ctx.beginPath();
      timeline.forEach((pt, idx) => {
        const x = padding.left + idx * stepX;
        const y = padding.top + chartH - ((pt[key] || 0) / maxMoney) * chartH;
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.lineTo(padding.left + (numPoints - 1) * stepX, padding.top + chartH);
      ctx.lineTo(padding.left, padding.top + chartH);
      ctx.closePath();
      ctx.fillStyle = grad;
      ctx.fill();

      // Line stroke
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.5;
      ctx.shadowColor = glowColor;
      ctx.shadowBlur = 8;
      ctx.beginPath();

      timeline.forEach((pt, idx) => {
        const x = padding.left + idx * stepX;
        const y = padding.top + chartH - ((pt[key] || 0) / maxMoney) * chartH;
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();

      // Key Points
      ctx.fillStyle = color;
      ctx.shadowBlur = 0;
      timeline.forEach((pt, idx) => {
        if (idx % 5 === 0 || idx === numPoints - 1) {
          const x = padding.left + idx * stepX;
          const y = padding.top + chartH - ((pt[key] || 0) / maxMoney) * chartH;
          ctx.beginPath();
          ctx.arc(x, y, 4, 0, Math.PI * 2);
          ctx.fill();
        }
      });
      ctx.restore();
    }

    // Draw P0 (Blue) and P1 (Red)
    drawLine('p0_money', '#388bfd', 'rgba(56, 139, 253, 0.5)', 'rgba(56, 139, 253, 0.25)');
    drawLine('p1_money', '#f85149', 'rgba(248, 81, 73, 0.5)', 'rgba(248, 81, 73, 0.25)');
  }

  // Redraw chart on window resize
  window.addEventListener('resize', () => {
    if (currentSummary && elResultsCard.style.display !== 'none') {
      drawWealthChart(currentSummary.timeline, currentSummary.agent0?.name, currentSummary.agent1?.name);
    }
  });

  function buildKagglePayload(replayData) {
    if (replayData && replayData.environment) {
      return {
        debug: true,
        playing: true,
        step: 0,
        controls: true,
        ...replayData
      };
    }
    return {
      debug: true,
      playing: true,
      step: 0,
      controls: true,
      environment: {
        id: "kaggriculture-arena-match",
        name: "kaggriculture",
        title: "Kaggriculture",
        description: "Advanced farming simulation: two players each tend a 10x10 farm of four 5x5 quadrants.",
        version: "0.1.0",
        module_version: "1.32.7",
        configuration: (replayData && replayData.configuration) ? replayData.configuration : {},
        specification: (replayData && replayData.specification) ? replayData.specification : {},
        steps: (replayData && replayData.steps) ? replayData.steps : []
      }
    };
  }

  // --- VISUALIZER RENDERER ---
  let currentIframeBlobUrl = null;

  function renderVisualizer(replayData) {
    if (!elVisIframe || !replayData) return;

    elVisCard.style.display = 'block';
    const seed = replayData.configuration?.seed ?? (replayData.environment?.configuration?.seed ?? 42);
    elVisSeedBadge.textContent = `Seed: ${seed}`;

    const header = window.VISUALIZER_HEADER || '';
    const footer = window.VISUALIZER_FOOTER || '';

    const kaggleObj = buildKagglePayload(replayData);
    const fullHtml = header + `\n<script>window.kaggle = ${JSON.stringify(kaggleObj)};</script>\n` + footer;

    // Use Blob URL for instant streaming load to eliminate main thread freeze
    if (currentIframeBlobUrl) {
      URL.revokeObjectURL(currentIframeBlobUrl);
    }
    const blob = new Blob([fullHtml], { type: 'text/html;charset=utf-8' });
    currentIframeBlobUrl = URL.createObjectURL(blob);
    elVisIframe.src = currentIframeBlobUrl;
  }

  // --- REPLAY EXPORT & IMPORT ---
  function downloadReplayHtml() {
    if (!currentReplay) {
      alert('No match data available to download!');
      return;
    }

    const header = window.VISUALIZER_HEADER || '';
    const footer = window.VISUALIZER_FOOTER || '';
    const kaggleObj = buildKagglePayload(currentReplay);
    const fullHtml = header + `\n<script>window.kaggle = ${JSON.stringify(kaggleObj)};</script>\n` + footer;

    const blob = new Blob([fullHtml], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const seed = currentReplay.configuration?.seed ?? (kaggleObj.environment?.configuration?.seed ?? 'match');
    a.href = url;
    a.download = `kaggriculture_replay_seed${seed}.html`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function downloadReplayJson() {
    if (!currentReplay) {
      alert('No match data available to download!');
      return;
    }

    const kaggleObj = buildKagglePayload(currentReplay);
    const blob = new Blob([JSON.stringify(kaggleObj, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const seed = currentReplay.configuration?.seed ?? (kaggleObj.environment?.configuration?.seed ?? 'match');
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
            throw new Error('No replay data found in HTML file');
          }
        }

        if (replayData) {
          currentReplay = replayData;
          renderVisualizer(replayData);
          elVisCard.scrollIntoView({ behavior: 'smooth' });
          alert(`Successfully loaded replay: ${file.name}`);
        }
      } catch (err) {
        alert('Error reading replay file: ' + err.message);
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
