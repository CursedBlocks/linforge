/**
 * LinForge - Reactive Frontend Controller & Theme Engine
 * Manages REST API communication, SSE terminal streaming, live telemetry Chart.js charts,
 * multi-theme switcher, quick presets wizard, app detail modal, and batch installer.
 */

const LinForge = {
  activeTab: 'dashboard',
  selectedApps: new Set(),
  cachedApps: [],
  cachedTweaks: [],
  cachedPresets: [],
  sseSource: null,
  autoScrollTerminal: true,
  currentTheme: 'theme-cyber',
  telemetryHistory: {
    labels: [],
    cpu: [],
    ram: []
  },
  chartInstance: null,
  allLogs: [],
  currentLogFilter: 'all',
  currentLogSearch: '',

  init() {
    this.initTheme();
    this.setupTabs();
    this.setupSearch();
    this.setupKeyboardShortcuts();
    this.setupTerminalControls();
    this.initChart();
    this.initSSE();

    // Data Loaders
    this.loadSystemData();
    this.loadPresets();
    this.loadApps();
    this.loadTweaks();
    this.loadTroubleshooters();

    // Live Telemetry Polling (every 2 seconds)
    setInterval(() => this.pollMetrics(), 2000);

    if (window.lucide) {
      lucide.createIcons();
    }
  },

  // --- THEME ENGINE ---
  initTheme() {
    const savedTheme = localStorage.getItem('linforge_theme') || 'theme-cyber';
    this.setTheme(savedTheme);

    const themeBtn = document.getElementById('theme-btn');
    const themeMenu = document.getElementById('theme-menu');

    if (themeBtn && themeMenu) {
      themeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        themeMenu.classList.toggle('show');
      });

      document.addEventListener('click', () => {
        themeMenu.classList.remove('show');
      });

      document.querySelectorAll('.theme-option').forEach(opt => {
        opt.addEventListener('click', () => {
          const themeName = opt.getAttribute('data-theme');
          this.setTheme(themeName);
          themeMenu.classList.remove('show');
        });
      });
    }
  },

  setTheme(themeName) {
    this.currentTheme = themeName;
    document.body.className = themeName;
    localStorage.setItem('linforge_theme', themeName);

    const labelMap = {
      'theme-cyber': 'Cyber Neon',
      'theme-plasma': 'Plasma KDE Indigo',
      'theme-midnight': 'Midnight Dark',
      'theme-ubuntu': 'Ubuntu Warmth',
      'theme-emerald': 'Emerald Matrix'
    };

    const labelEl = document.getElementById('current-theme-label');
    if (labelEl) {
      labelEl.textContent = labelMap[themeName] || 'Cyber Neon';
    }

    document.querySelectorAll('.theme-option').forEach(opt => {
      opt.classList.toggle('active', opt.getAttribute('data-theme') === themeName);
    });

    this.showToast(`Theme switched to ${labelMap[themeName]}`, 'info');
  },

  // --- TAB NAVIGATION ---
  setupTabs() {
    document.querySelectorAll('.nav-item').forEach(btn => {
      btn.addEventListener('click', () => {
        const tabId = btn.getAttribute('data-tab');
        this.switchTab(tabId);
      });
    });
  },

  switchTab(tabId) {
    this.activeTab = tabId;
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    const activeNav = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
    const activePane = document.getElementById(`tab-${tabId}`);

    if (activeNav) activeNav.classList.add('active');
    if (activePane) activePane.classList.add('active');

    if (window.lucide) {
      lucide.createIcons();
    }
  },

  // --- REAL-TIME CHART.JS TELEMETRY ---
  initChart() {
    const canvas = document.getElementById('telemetry-chart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const initialLabels = Array.from({ length: 15 }, () => '');
    const initialData = Array.from({ length: 15 }, () => 0);

    this.chartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: initialLabels,
        datasets: [
          {
            label: 'CPU Usage %',
            data: [...initialData],
            borderColor: '#00e5ff',
            backgroundColor: 'rgba(0, 229, 255, 0.15)',
            borderWidth: 2,
            tension: 0.4,
            fill: true,
            pointRadius: 0
          },
          {
            label: 'RAM Usage %',
            data: [...initialData],
            borderColor: '#6366f1',
            backgroundColor: 'rgba(99, 102, 241, 0.15)',
            borderWidth: 2,
            tension: 0.4,
            fill: true,
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        scales: {
          y: {
            min: 0,
            max: 100,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#64748b', font: { size: 10 } }
          },
          x: {
            grid: { display: false },
            ticks: { display: false }
          }
        },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: { color: '#94a3b8', boxWidth: 12, font: { size: 11, weight: 'bold' } }
          }
        }
      }
    });
  },

  updateChart(cpuPct, ramPct) {
    if (!this.chartInstance) return;

    const ds = this.chartInstance.data.datasets;
    ds[0].data.push(cpuPct);
    ds[0].data.shift();

    ds[1].data.push(ramPct);
    ds[1].data.shift();

    this.chartInstance.update('none');
  },

  // --- LIVE SSE LOG STREAMING & TASK RESULTS ---
  initSSE() {
    try {
      this.sseSource = new EventSource('/api/logs/stream');

      this.sseSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'task_result') {
            this.handleTaskResult(data.task_name || 'Task', data.result || {});
            return;
          }

          if (data.message) {
            this.appendLog(data.type || 'stdout', data.message);
          }
        } catch (e) {
          this.appendLog('stdout', event.data);
        }
      };

      this.sseSource.onerror = () => {
        const pulse = document.getElementById('term-pulse');
        if (pulse) pulse.style.background = '#f43f5e';
      };

      this.sseSource.onopen = () => {
        const pulse = document.getElementById('term-pulse');
        if (pulse) pulse.style.background = '#00e5ff';
      };
    } catch (e) {
      console.warn('SSE Connection warning:', e);
    }
  },

  handleTaskResult(taskName, result) {
    if (result.success) {
      this.showToast(`${taskName} finished successfully!`, 'success');
      // Refresh apps and system status
      this.loadApps(true);
      this.loadSystemData();
    } else {
      const code = result.error_code || `ERR_EXIT_${result.exit_code || 1}`;
      const title = result.error_title || `${taskName} Failed`;
      const suggestion = result.error_suggestion || 'Review the console diagnostics or retry with alternative source.';
      const stderr = result.stderr || result.stdout || 'Process returned a non-zero exit status.';

      this.showToast(`${title} (${code})`, 'error');

      this.showDialog({
        title,
        code,
        message: `An error occurred while executing ${taskName}. Exit code: ${result.exit_code}.`,
        suggestion,
        stderr,
        status: 'error',
        autoFixAction: (code === 'ERR_DPKG_LOCKED') ? () => this.runAction('troubleshoot', 'fix_apt_locks') : null
      });
    }
  },

  // --- DIAGNOSTIC ERROR & WARNING MODAL ---
  showDialog({ title, code, message, suggestion, stderr, status = 'error', autoFixAction = null, onConfirm = null }) {
    const modal = document.getElementById('dialog-modal');
    const card = document.getElementById('dialog-card-inner');
    if (!modal) return;

    card.className = `modal-card dialog-card status-${status}`;
    document.getElementById('dialog-title').textContent = title || 'Operation Notice';
    document.getElementById('dialog-code').textContent = code || (status === 'error' ? 'ERR_FAILED' : 'INFO');
    document.getElementById('dialog-desc').textContent = message || '';

    const suggBox = document.getElementById('dialog-suggestion-container');
    const suggEl = document.getElementById('dialog-suggestion');
    if (suggestion) {
      suggEl.textContent = suggestion;
      suggBox.style.display = 'block';
    } else {
      suggBox.style.display = 'none';
    }

    const stderrBox = document.getElementById('dialog-stderr-container');
    const stderrEl = document.getElementById('dialog-stderr');
    if (stderr && stderr.trim()) {
      stderrEl.textContent = stderr;
      stderrBox.style.display = 'block';
    } else {
      stderrBox.style.display = 'none';
    }

    const footer = document.getElementById('dialog-footer-actions');
    footer.innerHTML = '';

    if (autoFixAction) {
      const fixBtn = document.createElement('button');
      fixBtn.className = 'btn btn-primary';
      fixBtn.innerHTML = '<i data-lucide="wrench"></i> Auto-Fix with Troubleshooter';
      fixBtn.onclick = () => {
        this.closeDialog();
        autoFixAction();
      };
      footer.appendChild(fixBtn);
    }

    if (onConfirm) {
      const confirmBtn = document.createElement('button');
      confirmBtn.className = 'btn btn-danger';
      confirmBtn.textContent = 'Confirm Action';
      confirmBtn.onclick = () => {
        this.closeDialog();
        onConfirm();
      };
      footer.appendChild(confirmBtn);
    }

    const dismissBtn = document.createElement('button');
    dismissBtn.className = 'btn btn-secondary';
    dismissBtn.textContent = 'Dismiss';
    dismissBtn.onclick = () => this.closeDialog();
    footer.appendChild(dismissBtn);

    modal.classList.add('show');
    if (window.lucide) lucide.createIcons();
  },

  closeDialog() {
    const modal = document.getElementById('dialog-modal');
    if (modal) modal.classList.remove('show');
  },

  copyDialogStderr() {
    const stderrEl = document.getElementById('dialog-stderr');
    if (stderrEl) {
      navigator.clipboard.writeText(stderrEl.textContent).then(() => {
        this.showToast('Diagnostic log copied!', 'success');
      });
    }
  },

  appendLog(streamType, message) {
    const entry = { type: streamType, message, id: Date.now() + Math.random() };
    this.allLogs.push(entry);

    if (this.allLogs.length > 2000) {
      this.allLogs.shift();
    }

    if (this.matchesLogFilter(entry)) {
      this.renderLogLine(entry);
    }
  },

  matchesLogFilter(entry) {
    if (this.currentLogFilter !== 'all' && entry.type !== this.currentLogFilter) {
      return false;
    }
    if (this.currentLogSearch) {
      return entry.message.toLowerCase().includes(this.currentLogSearch.toLowerCase());
    }
    return true;
  },

  renderLogLine(entry) {
    const termBody = document.getElementById('terminal-output');
    if (!termBody) return;

    const line = document.createElement('div');
    line.className = `term-line term-${entry.type}`;
    line.textContent = entry.message;
    termBody.appendChild(line);

    if (this.autoScrollTerminal) {
      termBody.scrollTop = termBody.scrollHeight;
    }
  },

  refreshTerminalOutput() {
    const termBody = document.getElementById('terminal-output');
    if (!termBody) return;
    termBody.innerHTML = '';

    const filtered = this.allLogs.filter(e => this.matchesLogFilter(e));
    filtered.forEach(e => {
      const line = document.createElement('div');
      line.className = `term-line term-${e.type}`;
      line.textContent = e.message;
      termBody.appendChild(line);
    });

    if (this.autoScrollTerminal) {
      termBody.scrollTop = termBody.scrollHeight;
    }
  },

  setupTerminalControls() {
    document.querySelectorAll('.term-tab').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.term-tab').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentLogFilter = btn.getAttribute('data-filter');
        this.refreshTerminalOutput();
      });
    });

    const searchInput = document.getElementById('term-filter-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.currentLogSearch = e.target.value;
        this.refreshTerminalOutput();
      });
    }

    const btnToggleTerm = document.getElementById('btn-toggle-terminal');
    if (btnToggleTerm) {
      btnToggleTerm.addEventListener('click', () => this.toggleTerminal());
    }
  },

  toggleTerminal() {
    const drawer = document.getElementById('terminal-drawer');
    if (drawer) {
      drawer.classList.toggle('collapsed');
    }
  },

  toggleTerminalFullscreen() {
    const drawer = document.getElementById('terminal-drawer');
    const icon = document.getElementById('term-max-icon');
    if (drawer) {
      drawer.classList.toggle('fullscreen');
      if (icon) {
        icon.setAttribute('data-lucide', drawer.classList.contains('fullscreen') ? 'minimize-2' : 'maximize-2');
        if (window.lucide) lucide.createIcons();
      }
    }
  },

  clearTerminal() {
    this.allLogs = [];
    const termBody = document.getElementById('terminal-output');
    if (termBody) {
      termBody.innerHTML = '<div class="term-line term-system">✨ Console cleared.</div>';
    }
  },

  copyTerminalLogs() {
    const text = this.allLogs.map(e => `[${e.type}] ${e.message}`).join('\n');
    navigator.clipboard.writeText(text).then(() => {
      this.showToast('Terminal logs copied to clipboard!', 'success');
    }).catch(() => {
      this.showToast('Failed to copy logs', 'error');
    });
  },

  async cancelCurrentTask() {
    try {
      const res = await fetch('/api/cancel', { method: 'POST' });
      const data = await res.json();
      if (data.cancelled) {
        this.showToast('Cancellation signal sent.', 'info');
      }
    } catch (e) {
      this.showToast(`Cancel failed: ${e.message}`, 'error');
    }
  },

  // --- KEYBOARD SHORTCUTS ---
  setupKeyboardShortcuts() {
    window.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        if (e.key === 'Escape') {
          e.target.blur();
        }
        return;
      }

      const tabKeys = ['dashboard', 'presets', 'apps', 'tweaks', 'drivers', 'cleanup', 'troubleshoot', 'developer', 'maintenance'];
      const num = parseInt(e.key);
      if (!isNaN(num) && num >= 1 && num <= tabKeys.length) {
        this.switchTab(tabKeys[num - 1]);
        return;
      }

      if (e.key === '/') {
        e.preventDefault();
        const search = document.getElementById('global-search');
        if (search) search.focus();
      } else if (e.key.toLowerCase() === 't') {
        this.toggleTerminal();
      } else if (e.key === '?') {
        this.openShortcutsModal();
      } else if (e.key === 'Escape') {
        this.closeAppModal();
        this.closeShortcutsModal();
      }
    });
  },

  setupSearch() {
    const searchInput = document.getElementById('global-search');
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase().trim();
      if (this.activeTab !== 'apps' && term.length > 0) {
        this.switchTab('apps');
      }
      this.renderApps(term);
    });
  },

  // --- MODALS ---
  openShortcutsModal() {
    const modal = document.getElementById('shortcuts-modal');
    if (modal) modal.classList.add('show');
  },

  closeShortcutsModal() {
    const modal = document.getElementById('shortcuts-modal');
    if (modal) modal.classList.remove('show');
  },

  openAppModal(appId) {
    const app = this.cachedApps.find(a => a.id === appId);
    if (!app) return;

    const modal = document.getElementById('app-modal');
    if (!modal) return;

    document.getElementById('modal-app-name').textContent = app.name;
    document.getElementById('modal-app-category').textContent = app.category.toUpperCase();
    document.getElementById('modal-app-desc').textContent = app.description;

    const pillEl = document.getElementById('modal-app-installed-pill');
    if (pillEl) {
      if (app.is_installed) {
        pillEl.textContent = `✓ Installed (${app.installed_source || 'native'})`;
        pillEl.className = 'modal-installed-badge';
      } else {
        pillEl.textContent = 'Not Installed';
        pillEl.className = 'modal-installed-badge not-installed';
      }
    }

    const statusEl = document.getElementById('modal-app-status');
    if (statusEl) {
      statusEl.textContent = app.is_installed
        ? `Installed via ${app.installed_source || 'system'}`
        : 'Available for one-click installation';
      statusEl.className = app.is_installed ? 'val text-emerald' : 'val text-muted';
    }

    const sourceContainer = document.getElementById('modal-source-options');
    let selectedSource = app.default_source || 'native_deb';

    if (sourceContainer) {
      sourceContainer.innerHTML = '';
      const sources = app.sources || {};
      selectedSource = app.default_source || Object.keys(sources)[0] || 'native_deb';

      for (const srcKey of Object.keys(sources)) {
        const btn = document.createElement('button');
        btn.className = `btn-source-opt ${srcKey === selectedSource ? 'active' : ''}`;
        btn.textContent = srcKey.replace('_', ' ').toUpperCase();
        btn.onclick = () => {
          document.querySelectorAll('.btn-source-opt').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          selectedSource = srcKey;
        };
        sourceContainer.appendChild(btn);
      }
    }

    const actionContainer = document.getElementById('modal-app-actions');
    if (actionContainer) {
      actionContainer.innerHTML = `
        <button class="btn btn-secondary" onclick="LinForge.closeAppModal()">Close</button>
      `;

      if (app.is_installed) {
        const reinstallBtn = document.createElement('button');
        reinstallBtn.className = 'btn btn-outline';
        reinstallBtn.innerHTML = '<i data-lucide="refresh-cw"></i> Reinstall / Update';
        reinstallBtn.onclick = () => {
          this.installSingleApp(app.id, selectedSource, true);
          this.closeAppModal();
        };
        actionContainer.appendChild(reinstallBtn);

        const uninstallBtn = document.createElement('button');
        uninstallBtn.className = 'btn btn-danger';
        uninstallBtn.innerHTML = '<i data-lucide="trash-2"></i> Uninstall';
        uninstallBtn.onclick = () => {
          this.uninstallApp(app.id);
          this.closeAppModal();
        };
        actionContainer.appendChild(uninstallBtn);
      } else {
        const installBtn = document.createElement('button');
        installBtn.className = 'btn btn-primary';
        installBtn.innerHTML = '<i data-lucide="download"></i> Install Now';
        installBtn.onclick = () => {
          this.installSingleApp(app.id, selectedSource, false);
          this.closeAppModal();
        };
        actionContainer.appendChild(installBtn);
      }
    }

    modal.classList.add('show');
    if (window.lucide) lucide.createIcons();
  },

  closeAppModal() {
    const modal = document.getElementById('app-modal');
    if (modal) modal.classList.remove('show');
  },

  // --- PRESETS LOADER & HANDLER ---
  async loadPresets() {
    try {
      const res = await fetch('/api/presets');
      const data = await res.json();
      this.cachedPresets = data.presets || [];
      this.renderPresets();
    } catch (e) {
      console.error('Error loading presets:', e);
    }
  },

  renderPresets() {
    const container = document.getElementById('presets-container');
    if (!container) return;

    if (!this.cachedPresets.length) {
      container.innerHTML = '<div class="loading-placeholder">No presets configured.</div>';
      return;
    }

    container.innerHTML = '';
    this.cachedPresets.forEach(p => {
      const card = document.createElement('div');
      card.className = 'preset-card';
      card.innerHTML = `
        <div>
          <span class="preset-badge">${p.badge || 'Preset Profile'}</span>
          <div class="preset-header">
            <div class="metric-icon bg-${p.color || 'cyan'}">
              <i data-lucide="${p.icon || 'sparkles'}"></i>
            </div>
            <div>
              <h3>${p.name}</h3>
              <p>${p.tagline}</p>
            </div>
          </div>
          <p class="modal-desc" style="margin-top: 12px;">${p.description}</p>
          <div class="preset-details-list">
            ${(p.apps || []).map(a => `<span class="preset-tag">📦 ${a}</span>`).join('')}
            ${(p.tweaks || []).map(t => `<span class="preset-tag">⚡ ${t.replace('tweak_', '')}</span>`).join('')}
          </div>
        </div>
        <button class="btn btn-primary" onclick="LinForge.applyPreset('${p.id}')">
          <i data-lucide="zap"></i> Apply ${p.name}
        </button>
      `;
      container.appendChild(card);
    });

    if (window.lucide) lucide.createIcons();
  },

  async applyPreset(presetId) {
    try {
      this.showToast(`Starting preset ${presetId}...`, 'info');
      await fetch('/api/presets/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preset_id: presetId })
      });
      const drawer = document.getElementById('terminal-drawer');
      if (drawer && drawer.classList.contains('collapsed')) {
        drawer.classList.remove('collapsed');
      }
    } catch (e) {
      this.showToast(`Preset apply failed: ${e.message}`, 'error');
    }
  },

  // --- SYSTEM TELEMETRY & SPECS ---
  async loadSystemData() {
    try {
      const res = await fetch('/api/system');
      const data = await res.json();
      const summary = data.summary || {};
      const metrics = data.metrics || {};

      const distroText = document.getElementById('distro-pill-text');
      if (distroText) {
        distroText.textContent = `${summary.distro.pretty_name} (${summary.desktop.name} ${summary.desktop.session_type.toUpperCase()})`;
      }

      const kernelVal = document.getElementById('sidebar-kernel-val');
      if (kernelVal) {
        kernelVal.textContent = summary.distro.kernel;
      }

      this.renderSpecs(summary);
      this.renderDisks(metrics.disks || []);
    } catch (e) {
      console.error('Error loading system data:', e);
    }
  },

  async pollMetrics() {
    try {
      const res = await fetch('/api/metrics');
      const m = await res.json();

      // CPU
      const cpuBar = document.getElementById('cpu-gauge-bar');
      const cpuVal = document.getElementById('cpu-percent-text');
      const cpuModel = document.getElementById('cpu-model-text');
      const cpuTemp = document.getElementById('cpu-temp-text');

      if (cpuBar) cpuBar.style.width = `${m.cpu.usage_percent}%`;
      if (cpuVal) cpuVal.textContent = `${m.cpu.usage_percent}%`;
      if (cpuModel) cpuModel.textContent = `${m.cpu.model} (${m.cpu.cores} Cores @ ${m.cpu.frequency_mhz} MHz)`;
      if (cpuTemp) cpuTemp.textContent = m.cpu.temperature_c ? `${m.cpu.temperature_c}°C` : 'N/A';

      // Memory
      const ramBar = document.getElementById('ram-gauge-bar');
      const ramVal = document.getElementById('ram-percent-text');
      const ramUsage = document.getElementById('ram-usage-text');
      const swapStatus = document.getElementById('swap-status-text');

      if (ramBar) ramBar.style.width = `${m.memory.percent}%`;
      if (ramVal) ramVal.textContent = `${m.memory.percent}%`;
      if (ramUsage) ramUsage.textContent = `${m.memory.used_mb} MB / ${m.memory.total_mb} MB`;
      if (swapStatus) swapStatus.textContent = `Swap: ${m.memory.swap_used_mb} MB / ${m.memory.swap_total_mb} MB`;

      // Network
      const netDown = document.getElementById('net-down-text');
      const netUp = document.getElementById('net-up-text');
      if (netDown) netDown.textContent = `${m.network.down_kbs} KB/s`;
      if (netUp) netUp.textContent = `${m.network.up_kbs} KB/s`;

      // Update Chart
      this.updateChart(m.cpu.usage_percent, m.memory.percent);
    } catch (e) {}
  },

  renderSpecs(summary) {
    const container = document.getElementById('specs-container');
    if (!container) return;

    container.innerHTML = `
      <div class="spec-item"><span class="lbl">Linux Distribution</span><span class="val">${summary.distro.pretty_name}</span></div>
      <div class="spec-item"><span class="lbl">Desktop Environment</span><span class="val">${summary.desktop.name} ${summary.desktop.version} (${summary.desktop.session_type.toUpperCase()})</span></div>
      <div class="spec-item"><span class="lbl">Linux Kernel</span><span class="val">${summary.distro.kernel}</span></div>
      <div class="spec-item"><span class="lbl">Audio Server</span><span class="val">${summary.audio.primary}</span></div>
      ${(summary.gpus || []).map(g => `<div class="spec-item"><span class="lbl">GPU [${g.vendor}]</span><span class="val">${g.description} (${g.driver})</span></div>`).join('')}
    `;
  },

  renderDisks(disks) {
    const container = document.getElementById('disks-container');
    if (!container) return;

    container.innerHTML = '';
    disks.forEach(d => {
      const el = document.createElement('div');
      el.className = 'disk-item';
      el.innerHTML = `
        <div class="disk-top">
          <span>${d.mount} (${d.fs_type})</span>
          <span class="gauge-detail">${d.used} / ${d.total} (${d.percent}%)</span>
        </div>
        <div class="gauge-bar-wrapper">
          <div class="gauge-bar bg-indigo-gradient" style="width: ${d.percent}%;"></div>
        </div>
      `;
      container.appendChild(el);
    });
  },

  // --- APP STORE ---
  async loadApps(forceRefresh = false) {
    try {
      const url = forceRefresh ? '/api/apps?refresh=true' : '/api/apps';
      const res = await fetch(url);
      const data = await res.json();
      this.cachedApps = data.apps || [];
      this.renderAppCategories(data.categories || []);
      this.renderApps();
    } catch (e) {
      console.error('Error loading apps:', e);
    }
  },

  renderAppCategories(categories) {
    const container = document.getElementById('app-category-pills');
    if (!container) return;

    container.innerHTML = '<button class="pill active" data-category="all">All Applications</button>';
    categories.forEach(cat => {
      const btn = document.createElement('button');
      btn.className = 'pill';
      btn.setAttribute('data-category', cat.id);
      btn.textContent = cat.name;
      btn.addEventListener('click', () => {
        document.querySelectorAll('#app-category-pills .pill').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        this.renderApps();
      });
      container.appendChild(btn);
    });
  },

  renderApps(searchTerm = '') {
    const container = document.getElementById('apps-grid-container');
    if (!container) return;

    const activePill = document.querySelector('#app-category-pills .pill.active');
    const activeCategory = activePill ? activePill.getAttribute('data-category') : 'all';

    let filtered = this.cachedApps;
    if (activeCategory !== 'all') {
      filtered = filtered.filter(a => a.category === activeCategory);
    }
    if (searchTerm) {
      filtered = filtered.filter(a =>
        a.name.toLowerCase().includes(searchTerm) ||
        a.description.toLowerCase().includes(searchTerm)
      );
    }

    container.innerHTML = '';
    filtered.forEach(app => {
      const isInst = Boolean(app.is_installed);
      const card = document.createElement('div');
      card.className = `app-card ${isInst ? 'is-installed' : ''} ${this.selectedApps.has(app.id) ? 'selected' : ''}`;
      card.onclick = (e) => {
        if (e.target.tagName !== 'INPUT') {
          this.openAppModal(app.id);
        }
      };

      const statusLabel = isInst ? `✓ Installed (${app.installed_source || 'native'})` : 'Available';
      const statusClass = isInst ? 'status-installed' : 'status-uninstalled';

      card.innerHTML = `
        <input type="checkbox" class="app-checkbox" ${this.selectedApps.has(app.id) ? 'checked' : ''} />
        <div class="app-icon-wrap">
          <i data-lucide="${app.icon || 'box'}"></i>
        </div>
        <div class="app-details">
          <h4>${app.name}</h4>
          <p>${app.description}</p>
        </div>
        <span class="app-status-tag ${statusClass}">
          ${statusLabel}
        </span>
      `;

      const cb = card.querySelector('.app-checkbox');
      cb.addEventListener('change', (e) => {
        e.stopPropagation();
        if (cb.checked) {
          this.selectedApps.add(app.id);
          card.classList.add('selected');
        } else {
          this.selectedApps.delete(app.id);
          card.classList.remove('selected');
        }
        this.updateBatchSelectionBar();
      });

      container.appendChild(card);
    });

    if (window.lucide) lucide.createIcons();
  },

  updateBatchSelectionBar() {
    const bar = document.getElementById('batch-install-bar');
    const count = document.getElementById('selected-apps-count');
    if (!count) return;

    count.textContent = `${this.selectedApps.size} apps selected`;
    if (bar) {
      bar.style.opacity = this.selectedApps.size > 0 ? '1' : '0.5';
    }
  },

  clearAppSelection() {
    this.selectedApps.clear();
    this.renderApps();
    this.updateBatchSelectionBar();
  },

  async installSelectedApps() {
    if (!this.selectedApps.size) {
      this.showToast('Please select apps to install first.', 'info');
      return;
    }

    const batch = Array.from(this.selectedApps);
    this.showToast(`Starting batch installation of ${batch.length} apps...`, 'info');

    try {
      await fetch('/api/apps/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ batch })
      });
      const drawer = document.getElementById('terminal-drawer');
      if (drawer && drawer.classList.contains('collapsed')) {
        drawer.classList.remove('collapsed');
      }
    } catch (e) {
      this.showToast(`Batch failed: ${e.message}`, 'error');
    }
  },

  async installSingleApp(appId, source, forceReinstall = false) {
    this.showToast(`Installing ${appId}...`, 'info');
    try {
      await fetch('/api/apps/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_id: appId, source, force_reinstall: forceReinstall })
      });
      const drawer = document.getElementById('terminal-drawer');
      if (drawer && drawer.classList.contains('collapsed')) {
        drawer.classList.remove('collapsed');
      }
    } catch (e) {
      this.showToast(`Installation failed: ${e.message}`, 'error');
    }
  },

  async uninstallApp(appId) {
    this.showToast(`Uninstalling ${appId}...`, 'info');
    try {
      await fetch('/api/apps/uninstall', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_id: appId })
      });
      const drawer = document.getElementById('terminal-drawer');
      if (drawer && drawer.classList.contains('collapsed')) {
        drawer.classList.remove('collapsed');
      }
    } catch (e) {
      this.showToast(`Uninstall failed: ${e.message}`, 'error');
    }
  },

  // --- PERFORMANCE TWEAKS ---
  async loadTweaks() {
    try {
      const res = await fetch('/api/tweaks');
      const data = await res.json();
      this.cachedTweaks = data.tweaks || [];
      this.renderTweakCategories(data.categories || []);
      this.renderTweaks();
    } catch (e) {
      console.error('Error loading tweaks:', e);
    }
  },

  renderTweakCategories(categories) {
    const container = document.getElementById('tweak-category-pills');
    if (!container) return;

    container.innerHTML = '<button class="pill active" data-category="all">All Tweaks</button>';
    categories.forEach(cat => {
      const btn = document.createElement('button');
      btn.className = 'pill';
      btn.setAttribute('data-category', cat.id);
      btn.textContent = cat.name;
      btn.addEventListener('click', () => {
        document.querySelectorAll('#tweak-category-pills .pill').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        this.renderTweaks();
      });
      container.appendChild(btn);
    });
  },

  renderTweaks() {
    const container = document.getElementById('tweaks-grid-container');
    if (!container) return;

    const activePill = document.querySelector('#tweak-category-pills .pill.active');
    const activeCategory = activePill ? activePill.getAttribute('data-category') : 'all';

    let filtered = this.cachedTweaks;
    if (activeCategory !== 'all') {
      filtered = filtered.filter(t => t.category === activeCategory);
    }

    container.innerHTML = '';
    filtered.forEach(tw => {
      const card = document.createElement('div');
      card.className = 'tweak-card';
      card.innerHTML = `
        <div class="tweak-header">
          <div class="metric-icon bg-cyan"><i data-lucide="zap"></i></div>
          <div>
            <h4>${tw.name}</h4>
            <p>${tw.description}</p>
          </div>
        </div>
        <div class="tweak-footer">
          <span class="status-badge">${tw.is_applied ? 'Active' : 'Not Applied'}</span>
          <button class="btn btn-sm ${tw.is_applied ? 'btn-secondary' : 'btn-primary'}" onclick="LinForge.toggleTweak('${tw.id}', ${tw.is_applied})">
            ${tw.is_applied ? 'Revert Tweak' : 'Apply Tweak'}
          </button>
        </div>
      `;
      container.appendChild(card);
    });

    if (window.lucide) lucide.createIcons();
  },

  async toggleTweak(tweakId, isApplied) {
    const url = isApplied ? '/api/tweaks/revert' : '/api/tweaks/apply';
    this.showToast(`${isApplied ? 'Reverting' : 'Applying'} ${tweakId}...`, 'info');

    try {
      await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tweak_id: tweakId })
      });
      const drawer = document.getElementById('terminal-drawer');
      if (drawer && drawer.classList.contains('collapsed')) {
        drawer.classList.remove('collapsed');
      }
    } catch (e) {
      this.showToast(`Tweak operation failed: ${e.message}`, 'error');
    }
  },

  async applyRecommendedTweaks() {
    const recommended = ['tweak_gaming_sysctl', 'tweak_swappiness_10', 'tweak_split_lock', 'tweak_zram', 'tweak_bbr_tcp'];
    this.showToast('Applying recommended gaming tweaks...', 'info');

    try {
      await fetch('/api/tweaks/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ batch: recommended })
      });
      const drawer = document.getElementById('terminal-drawer');
      if (drawer && drawer.classList.contains('collapsed')) {
        drawer.classList.remove('collapsed');
      }
    } catch (e) {
      this.showToast(`Batch failed: ${e.message}`, 'error');
    }
  },

  // --- TROUBLESHOOTER ---
  async loadTroubleshooters() {
    try {
      const res = await fetch('/api/troubleshoot');
      const data = await res.json();
      const container = document.getElementById('troubleshoot-container');
      if (!container) return;

      container.innerHTML = '';
      (data.troubleshooters || []).forEach(item => {
        const row = document.createElement('div');
        row.className = `troubleshoot-item ${item.status === 'detected' ? 'issue-found' : ''}`;
        row.innerHTML = `
          <div class="troubleshoot-item-info">
            <div class="metric-icon ${item.status === 'detected' ? 'bg-rose' : 'bg-emerald'}">
              <i data-lucide="${item.status === 'detected' ? 'alert-triangle' : 'check'}"></i>
            </div>
            <div>
              <h4>${item.name}</h4>
              <p class="sub">${item.description}</p>
            </div>
          </div>
          <div class="header-actions">
            <span class="status-tag ${item.status === 'detected' ? 'status-detected' : 'status-healthy'}">
              ${item.status === 'detected' ? 'Issue Detected' : 'System Healthy'}
            </span>
            <button class="btn btn-secondary btn-sm" onclick="LinForge.runAction('troubleshoot', '${item.id}')">
              Run Repair
            </button>
          </div>
        `;
        container.appendChild(row);
      });

      if (window.lucide) lucide.createIcons();
    } catch (e) {
      console.error('Error loading troubleshooters:', e);
    }
  },

  // --- GENERIC ACTIONS RUNNER ---
  async runAction(moduleName, actionName) {
    const urlMap = {
      drivers: '/api/drivers/action',
      cleanup: '/api/cleanup/action',
      troubleshoot: '/api/troubleshoot/run',
      developer: '/api/developer/action',
      maintenance: '/api/maintenance/action'
    };

    const targetUrl = urlMap[moduleName];
    if (!targetUrl) return;

    try {
      this.showToast(`Starting ${actionName} operation in ${moduleName}...`, 'info');
      const body = (moduleName === 'troubleshoot' && actionName !== 'all')
        ? { fix_id: actionName }
        : { action: actionName };

      await fetch(targetUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const drawer = document.getElementById('terminal-drawer');
      if (drawer && drawer.classList.contains('collapsed')) {
        drawer.classList.remove('collapsed');
      }
    } catch (e) {
      this.showToast(`Action failed: ${e.message}`, 'error');
    }
  },

  // --- TOAST NOTIFICATIONS ---
  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
};

// Bootstrap application on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  LinForge.init();
});
