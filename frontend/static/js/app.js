// Linux Security Audit Tool - Frontend Application
class SecurityDashboard {
    constructor() {
        this.apiBase = 'http://localhost:5000';
        this.scans = [];
        this.history = [];
        this.activePolling = null;
        this.pollingInterval = 10000; // 10 seconds
        this.currentView = 'dashboard';
        this.latestSeveritySummary = null;

        // Initialize
        this.init();
    }

    async init() {
        // Hide loading screen
        setTimeout(() => {
            document.getElementById('loadingScreen').style.display = 'none';
        }, 1000);

        // Set up event listeners
        this.setupEventListeners();

        // Initialize charts
        this.initCharts();

        // Load initial data
        await this.loadData();

        // Start polling
        this.startPolling();

        // Update connection status
        this.updateConnectionStatus();

        // Update time
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);

        // Load saved state from localStorage
        this.loadSavedState();
    }

    setupEventListeners() {
        // Menu navigation
        document.querySelectorAll('.menu-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const view = item.dataset.view;
                this.switchView(view);
                this.updateBreadcrumb(view);

                // Update active menu item
                document.querySelectorAll('.menu-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
            });
        });

        // Sidebar helpers
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.getElementById('sidebarOverlay');

        const openSidebar = () => {
            sidebar.classList.add('active');
            if (overlay) overlay.classList.add('active');
        };
        const closeSidebar = () => {
            sidebar.classList.remove('active');
            if (overlay) overlay.classList.remove('active');
        };
        const toggleSidebar = () => sidebar.classList.contains('active') ? closeSidebar() : openSidebar();

        // Nav toggle (hamburger)
        document.querySelector('.nav-toggle').addEventListener('click', toggleSidebar);

        // Close button inside sidebar
        const closeBtn = document.getElementById('sidebarCloseBtn');
        if (closeBtn) closeBtn.addEventListener('click', closeSidebar);

        // Overlay click closes sidebar
        if (overlay) overlay.addEventListener('click', closeSidebar);

        // Auto-close sidebar when a menu item is clicked (helpful on small screens)
        document.querySelectorAll('.menu-item').forEach(item => {
            item.addEventListener('click', () => {
                if (window.innerWidth < 1024) closeSidebar();
            });
        });

        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadData();
            this.showToast('Refreshing data...', 'info');
        });

        // Fullscreen button
        document.getElementById('fullscreenBtn').addEventListener('click', () => {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        });

        // Quick actions
        document.getElementById('startQuickScan').addEventListener('click', () => this.openScanModal('quick'));
        document.getElementById('startFullScan').addEventListener('click', () => this.openScanModal('full'));
        document.getElementById('viewReports').addEventListener('click', () => this.generateReport());
        document.getElementById('viewAllScans').addEventListener('click', () => this.switchView('history'));
        document.getElementById('viewHistory').addEventListener('click', () => this.switchView('history'));
        // System Info action card
        const sysInfoBtn = document.getElementById('systemInfo');
        if (sysInfoBtn) sysInfoBtn.addEventListener('click', () => this.showSystemInfo());

        // Scan modal
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.modal').forEach(modal => {
                    modal.classList.remove('active');
                });
            });
        });

        // Start scan from modal
        document.getElementById('confirmStartScan').addEventListener('click', () => {
            const selectedOption = document.querySelector('.scan-option.active');
            const scanType = selectedOption ? selectedOption.dataset.type : 'quick';
            const description = document.getElementById('scanDescription').value;
            this.startScan(scanType, description);
        });

        // Scan option selection
        document.querySelectorAll('.scan-option').forEach(option => {
            option.addEventListener('click', () => {
                document.querySelectorAll('.scan-option').forEach(o => o.classList.remove('active'));
                option.classList.add('active');
            });
        });

        // Close modal on background click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        });

        // View all scans button (duplicate guard)
        const viewAllScansBtn = document.getElementById('viewAllScans');
        if (viewAllScansBtn) viewAllScansBtn.addEventListener('click', () => this.switchView('history'));

        // Start new scan button (only if element exists)
        const startNewScanBtn = document.getElementById('startNewScan');
        if (startNewScanBtn) startNewScanBtn.addEventListener('click', () => this.openScanModal('quick'));

        // Refresh scans button (only if element exists)
        const refreshScansBtn = document.getElementById('refreshScans');
        if (refreshScansBtn) refreshScansBtn.addEventListener('click', () => {
            this.loadData();
            this.showToast('Data refreshed', 'info');
        });

        // Generate report button
        document.getElementById('generateReport').addEventListener('click', () => {
            this.generateReport();
        });

        // Save config button
        document.getElementById('saveConfig').addEventListener('click', () => {
            this.saveConfig();
        });

        // Theme selector
        document.getElementById('themeSelect').addEventListener('change', (e) => {
            this.setTheme(e.target.value);
        });

        // Refresh interval input
        document.getElementById('refreshInterval').addEventListener('change', (e) => {
            const interval = parseInt(e.target.value) * 1000;
            if (interval >= 5000 && interval <= 60000) {
                this.pollingInterval = interval;
                this.restartPolling();
                this.showToast(`Refresh interval set to ${e.target.value} seconds`, 'success');
            }
        });

        // ── Analysis view ─────────────────────────────────────────────
        document.getElementById('loadAnalysisBtn').addEventListener('click', () => {
            const scanId = document.getElementById('analysisScanSelect').value;
            if (!scanId) {
                this.showToast('Please select a scan first', 'warning');
                return;
            }
            this.loadAnalysis(scanId);
        });
        document.getElementById('downloadAnalysisPdfBtn').addEventListener('click', () => {
            const scanId = document.getElementById('analysisScanSelect').value;
            if (scanId) this.downloadPDFReport(scanId);
        });
    }

    async loadData() {
        try {
            // Load system status
            await this.loadSystemStatus();

            // Load scans
            await this.loadScans();

            // Load history
            await this.loadHistory();

            // Update stats
            this.updateStats();
            await this.updateTopFindings();
            this.updateRiskOverview();

            // Update connection status
            this.updateConnectionStatus(true);
        } catch (error) {
            console.error('Error loading data:', error);
            this.updateConnectionStatus(false);
            this.showToast('Failed to load data from API', 'error');
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch(`${this.apiBase}/api/system/status`);
            if (!response.ok) throw new Error('API request failed');

            const data = await response.json();

            // Update username if available
            if (data.system && data.system.user) {
                document.getElementById('username').textContent = data.system.user;
            }

            // Update system status indicator
            const statusIndicator = document.getElementById('systemStatus');
            if (data.service && data.service.lynis_installed) {
                statusIndicator.classList.add('active');
                statusIndicator.classList.remove('inactive');
            } else {
                statusIndicator.classList.remove('active');
                statusIndicator.classList.add('inactive');
            }

            return data;
        } catch (error) {
            console.error('Error loading system status:', error);
            throw error;
        }
    }

    async loadScans() {
        try {
            const response = await fetch(`${this.apiBase}/api/scans`);
            if (!response.ok) throw new Error('API request failed');

            const data = await response.json();
            // Merge active jobs + completed history as one scans list
            this.scans = [
                ...(data.active_jobs || []),
                ...(data.history || []).map(h => ({ ...h, status: h.status || 'completed' }))
            ];

            // Update active scans table
            this.updateActiveScansTable();

            // Update all scans table (in scans view)
            this.updateAllScansTable();

            return this.scans;
        } catch (error) {
            console.error('Error loading scans:', error);
            this.scans = [];
            throw error;
        }
    }

    async loadHistory() {
        try {
            const response = await fetch(`${this.apiBase}/api/history`);
            if (!response.ok) throw new Error('API request failed');

            const data = await response.json();
            this.history = data.scans || [];

            // Update recent scans table
            this.updateRecentScansTable();

            // Update history table
            this.updateHistoryTable();

            return this.history;
        } catch (error) {
            console.error('Error loading history:', error);
            this.history = [];
            throw error;
        }
    }

    updateActiveScansTable() {
        const tbody = document.getElementById('activeScansBody');
        const noScansRow = document.getElementById('noActiveScans');

        // Clear existing rows (except the no scans row)
        tbody.innerHTML = '';
        tbody.appendChild(noScansRow);

        // Filter active scans
        const activeScans = this.scans.filter(scan =>
            scan.status === 'running' || scan.status === 'pending'
        );

        if (activeScans.length === 0) {
            noScansRow.style.display = '';
            return;
        }

        noScansRow.style.display = 'none';

        // Add active scans
        activeScans.forEach(scan => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="scan-id">${scan.scan_id}</div>
                    <small class="text-muted">${this.formatTimeAgo(scan.created_at)}</small>
                </td>
                <td><span class="status-badge ${scan.status}">${scan.status}</span></td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${scan.progress || 0}%"></div>
                    </div>
                    <small>${scan.progress || 0}%</small>
                </td>
                <td>${this.formatDateTime(scan.started_at || scan.created_at)}</td>
                <td>${this.calculateDuration(scan.started_at, scan.completed_at)}</td>
                <td>
                    <button class="btn-icon" onclick="dashboard.viewScanDetails('${scan.scan_id}')" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${scan.status === 'running' ? `
                        <button class="btn-icon" onclick="dashboard.cancelScan('${scan.scan_id}')" title="Cancel Scan">
                            <i class="fas fa-stop-circle"></i>
                        </button>
                    ` : ''}
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    updateAllScansTable() {
        const tbody = document.getElementById('allScansBody');
        if (!tbody) return;
        tbody.innerHTML = '';

        // Show active jobs + completed scans from history merged
        const activeJobs = this.scans.filter(s => s.status === 'running' || s.status === 'pending');
        const completed = this.history.slice();

        const allScans = [...activeJobs, ...completed];

        if (allScans.length === 0) {
            tbody.innerHTML = `
                <tr><td colspan="7" class="empty-state">
                    <i class="fas fa-shield-alt"></i><p>No scans found. Start your first scan!</p>
                </td></tr>`;
            return;
        }

        allScans.forEach(scan => {
            const status = scan.status || 'completed';
            const hi = scan.hardening_index;
            const hiText = hi !== null && hi !== undefined ? `${hi}/100` : '—';
            const sevSum = scan.severity_summary || {};
            const findingsText = scan.findings_count !== undefined
                ? `${scan.findings_count} (<span style='color:#DC2626'>${sevSum.critical || 0}C</span> <span style='color:#EA580C'>${sevSum.high || 0}H</span>)`
                : (scan.findings !== undefined ? scan.findings : '—');

            const row = document.createElement('tr');
            row.className = 'scan-row';
            row.innerHTML = `
                <td>
                    <div class="scan-id">${scan.scan_id}</div>
                    <small class="text-muted">${this.formatTimeAgo(scan.timestamp || scan.created_at || scan.completed_at)}</small>
                </td>
                <td><span class="status-badge ${status}">${status}</span></td>
                <td>${hiText}</td>
                <td>${findingsText}</td>
                <td>${this.formatDateTime(scan.timestamp || scan.started_at || scan.created_at)}</td>
                <td>
                    <button class="btn-icon" title="View Details" onclick="dashboard.viewScanDetails('${scan.scan_id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${status === 'completed' ? `
                    <button class="btn-icon" title="Full Analysis" onclick="dashboard.openAnalysis('${scan.scan_id}')" style="color:var(--color-primary)">
                        <i class="fas fa-microscope"></i>
                    </button>
                    <button class="btn-icon" title="Download PDF" onclick="dashboard.downloadPDFReport('${scan.scan_id}')">
                        <i class="fas fa-file-pdf"></i>
                    </button>` : ''}
                    ${status === 'running' ? `
                    <button class="btn-icon" title="Cancel" onclick="dashboard.cancelScan('${scan.scan_id}')" style="color:var(--color-danger)">
                        <i class="fas fa-stop-circle"></i>
                    </button>` : ''}
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    updateRecentScansTable() {
        const tbody = document.getElementById('recentScansBody');
        const noScansRow = document.getElementById('noRecentScans');

        // Clear existing rows (except the no scans row)
        tbody.innerHTML = '';
        tbody.appendChild(noScansRow);

        // Get recent completed scans (last 5)
        const recentScans = this.history.slice(0, 5);

        if (recentScans.length === 0) {
            noScansRow.style.display = '';
            return;
        }

        noScansRow.style.display = 'none';

        // Add recent scans
        recentScans.forEach(scan => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="scan-id">${scan.scan_id}</div>
                    <small class="text-muted">${this.formatTimeAgo(scan.completed_at || scan.timestamp)}</small>
                </td>
                <td><span class="status-badge completed">completed</span></td>
                <td>${this.formatDateTime(scan.completed_at || scan.timestamp)}</td>
                <td>${this.calculateDuration(scan.started_at, scan.completed_at)}</td>
                <td>
                    <span class="findings-count">${scan.findings || 'N/A'}</span>
                </td>
                <td>
                    <button class="btn-icon" onclick="dashboard.viewScanDetails('${scan.scan_id}')" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-icon" onclick="dashboard.openAnalysis('${scan.scan_id}')" title="Analyse Findings" style="color:var(--color-primary)">
                        <i class="fas fa-microscope"></i>
                    </button>
                    <button class="btn-icon" onclick="dashboard.downloadPDFReport('${scan.scan_id}')" title="Download PDF Report">
                        <i class="fas fa-file-pdf"></i>
                    </button>
                    <button class="btn-icon" onclick="dashboard.downloadRawOutput('${scan.scan_id}')" title="Download Raw Output">
                        <i class="fas fa-download"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    updateHistoryTable() {
        const tbody = document.getElementById('historyBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (this.history.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="empty-state">
                        <i class="fas fa-inbox"></i>
                        <p>No scan history</p>
                    </td>
                </tr>
            `;
            return;
        }

        this.history.forEach(scan => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="scan-id">${scan.scan_id}</div>
                </td>
                <td>${this.formatDateTime(scan.completed_at || scan.timestamp)}</td>
                <td><span class="status-badge completed">completed</span></td>
                <td>${this.calculateDuration(scan.started_at, scan.completed_at)}</td>
                <td>
                    <span class="findings-count">${scan.findings || 'N/A'}</span>
                </td>
                <td>
                    <button class="btn-icon" onclick="dashboard.viewScanDetails('${scan.scan_id}')" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-icon" onclick="dashboard.openAnalysis('${scan.scan_id}')" title="Analyse Findings" style="color:var(--color-primary)">
                        <i class="fas fa-microscope"></i>
                    </button>
                    <button class="btn-icon" onclick="dashboard.downloadPDFReport('${scan.scan_id}')" title="Download PDF Report">
                        <i class="fas fa-file-pdf"></i>
                    </button>
                    <button class="btn-icon" onclick="dashboard.downloadRawOutput('${scan.scan_id}')" title="Download Raw Output">
                        <i class="fas fa-download"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    animateValue(elementId, start, end, duration) {
        const obj = document.getElementById(elementId);
        if (!obj) return;

        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                obj.innerHTML = end;
            }
        };
        window.requestAnimationFrame(step);
    }

    updateStats() {
        const totalScans = this.scans.length + this.history.length;
        const completedScans = this.history.length;
        const activeScans = this.scans.filter(s => s.status === 'running').length;
        const failedScans = this.scans.filter(s => s.status === 'failed').length +
            this.history.filter(s => s.status === 'failed').length;

        this.animateValue('totalScans', 0, totalScans, 1000);
        this.animateValue('completedScans', 0, completedScans, 1000);
        this.animateValue('activeScans', 0, activeScans, 1000);
        this.animateValue('failedScans', 0, failedScans, 1000);
    }

    async updateTopFindings() {
        const findingsContainer = document.getElementById('topFindings');
        if (!findingsContainer) return;

        findingsContainer.innerHTML = '<p class="text-muted">Loading latest findings...</p>';

        const latestScan = this.history[0];
        if (!latestScan || !latestScan.scan_id) {
            findingsContainer.innerHTML = '<p class="text-muted">No completed scans available yet. Run a scan to see findings here.</p>';
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/api/scans/${latestScan.scan_id}/results`);
            if (!response.ok) {
                let errorMessage = `Failed to load findings (HTTP ${response.status})`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.message || errorMessage;
                } catch (jsonError) { /* ignore */ }
                throw new Error(errorMessage);
            }

            const results = await response.json();
            const parsedResults = results.parsed_results || {};
            const findings = parsedResults.findings || {};
            const hi = parsedResults.hardening_index ?? parsedResults.score?.hardening_index ?? null;
            this.latestSeveritySummary = parsedResults.severity_summary || null;
            this.latestHardeningIndex = hi;

            // ── Render score banner ──────────────────────────────────────────
            const banner = document.getElementById('reportScoreBanner');
            if (banner) {
                const sev = this.latestSeveritySummary || {};
                const scoreEl = document.getElementById('reportHardeningScore');
                const labelEl = document.getElementById('reportHardeningLabel');

                if (hi !== null && hi !== undefined) {
                    const color = hi < 40 ? '#DC2626' : hi < 60 ? '#D97706' : hi < 80 ? '#16A34A' : '#0891B2';
                    const label = hi < 40 ? 'Poor — Act Now' : hi < 60 ? 'Fair — Needs Work' : hi < 80 ? 'Good' : 'Excellent';
                    if (scoreEl) { scoreEl.textContent = `${hi}/100`; scoreEl.style.color = color; }
                    if (labelEl) { labelEl.textContent = label; labelEl.style.color = color; }
                } else {
                    if (scoreEl) { scoreEl.textContent = 'N/A'; scoreEl.style.color = 'var(--color-text-muted)'; }
                    if (labelEl) { labelEl.textContent = 'Run a full scan to see score'; labelEl.style.color = 'var(--color-text-muted)'; }
                }

                // Animate severity counts
                const counts = { critical: sev.critical || 0, high: sev.high || 0, medium: sev.medium || 0, low: sev.low || 0 };
                if (document.getElementById('reportCriticalCount')) this.animateValue('reportCriticalCount', 0, counts.critical, 800);
                if (document.getElementById('reportHighCount')) this.animateValue('reportHighCount', 0, counts.high, 800);
                if (document.getElementById('reportMediumCount')) this.animateValue('reportMediumCount', 0, counts.medium, 800);
                if (document.getElementById('reportLowCount')) this.animateValue('reportLowCount', 0, counts.low, 800);

                banner.style.display = 'block';
            }

            // ── Render top findings list ─────────────────────────────────────
            const topFindings = [
                ...(findings.critical || []),
                ...(findings.high || []),
                ...(findings.medium || []),
                ...(findings.low || [])
            ].slice(0, 10);

            if (topFindings.length === 0) {
                findingsContainer.innerHTML = '<p class="text-muted">No findings detected in the latest scan.</p>';
                return;
            }

            findingsContainer.innerHTML = topFindings.map(finding => {
                const severity = (finding.severity || 'info').toLowerCase();
                const sevColors = { critical: '#DC2626', high: '#EA580C', medium: '#D97706', low: '#0891B2' };
                const sevColor = sevColors[severity] || '#64748B';
                return `
                    <div class="finding-item" style="border-left:3px solid ${sevColor};padding-left:12px;margin-bottom:12px">
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                            <span style="background:${sevColor};color:white;font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;text-transform:uppercase">${severity}</span>
                            <span style="font-size:11px;color:var(--color-text-muted)">${finding.category || 'General'}</span>
                        </div>
                        <div class="finding-description" style="font-size:13px;color:var(--color-text);line-height:1.5">${finding.message || 'No details available'}</div>
                    </div>
                `;
            }).join('');

        } catch (error) {
            console.error('Error updating top findings:', error);
            findingsContainer.innerHTML = '<p class="text-muted">Unable to load findings summary.</p>';
        }
    }
    updateRiskOverview() {
        const statusChart = Chart.getChart('statusChart');
        if (!statusChart) return;

        const severity = this.latestSeveritySummary || {};
        const totals = {
            critical: severity.critical || 0,
            high: severity.high || 0,
            medium: severity.medium || 0,
            low: severity.low || 0
        };

        if ((totals.critical + totals.high + totals.medium + totals.low) === 0) {
            return;
        }

        statusChart.data.labels = ['Critical', 'High', 'Medium', 'Low'];
        statusChart.data.datasets[0].data = [totals.critical, totals.high, totals.medium, totals.low];
        statusChart.data.datasets[0].backgroundColor = ['#DC2626', '#EA580C', '#D97706', '#0891B2'];
        statusChart.update();
    }

    async startScan(scanType = 'quick', description = '') {
        try {
            const response = await fetch(`${this.apiBase}/api/scans`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    scan_type: scanType,
                    description: description
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to start scan');
            }

            const data = await response.json();

            // Close modal
            document.getElementById('startScanModal').classList.remove('active');

            // Clear description
            document.getElementById('scanDescription').value = '';

            // Show success message
            this.showToast(`Scan ${data.scan_id} started successfully`, 'success');

            // Reload data
            setTimeout(() => this.loadData(), 1000);

            return data;
        } catch (error) {
            console.error('Error starting scan:', error);
            this.showToast(`Failed to start scan: ${error.message}`, 'error');
        }
    }

    async cancelScan(scanId) {
        if (!confirm('Are you sure you want to cancel this scan?')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/api/scans/${scanId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to cancel scan');
            }

            this.showToast(`Scan ${scanId} cancelled`, 'success');

            // Reload data
            setTimeout(() => this.loadData(), 1000);
        } catch (error) {
            console.error('Error cancelling scan:', error);
            this.showToast('Failed to cancel scan', 'error');
        }
    }

    async viewScanDetails(scanId) {
        try {
            const response = await fetch(`${this.apiBase}/api/scans/${scanId}`);
            if (!response.ok) throw new Error('Failed to fetch scan details');

            const scan = await response.json();

            // Load results if available
            let results = null;
            if (scan.status === 'completed') {
                const resultsResponse = await fetch(`${this.apiBase}/api/scans/${scanId}/results`);
                if (resultsResponse.ok) {
                    results = await resultsResponse.json();
                }
            }

            // Show modal with details
            this.showScanDetailsModal(scan, results);
        } catch (error) {
            console.error('Error viewing scan details:', error);
            this.showToast('Failed to load scan details', 'error');
        }
    }

    async viewScanResults(scanId) {
        try {
            const response = await fetch(`${this.apiBase}/api/scans/${scanId}/results`);
            if (!response.ok) throw new Error('Failed to fetch scan results');

            const results = await response.json();

            // Show modal with results
            this.showScanResultsModal(results);
        } catch (error) {
            console.error('Error viewing scan results:', error);
            this.showToast('Failed to load scan results', 'error');
        }
    }

    async downloadRawOutput(scanId) {
        window.open(`${this.apiBase}/api/scans/${scanId}/raw?download=true`, '_blank');
    }

    // ── Analysis view methods ───────────────────────────────────────────────

    populateAnalysisScanSelector() {
        const sel = document.getElementById('analysisScanSelect');
        if (!sel) return;
        const current = sel.value;
        // Keep the placeholder
        sel.innerHTML = '<option value="">-- Choose a completed scan --</option>';
        this.history.forEach(scan => {
            const opt = document.createElement('option');
            opt.value = scan.scan_id;
            const ts = scan.timestamp || scan.completed_at || '';
            let label = scan.scan_id;
            if (ts) {
                try { label += '  —  ' + new Date(ts).toLocaleString(); } catch (e) { }
            }
            opt.textContent = label;
            if (scan.scan_id === current) opt.selected = true;
            sel.appendChild(opt);
        });
    }

    async loadAnalysis(scanId) {
        const loading = document.getElementById('analysisLoading');
        const results = document.getElementById('analysisResults');
        const pdfBtn = document.getElementById('downloadAnalysisPdfBtn');
        if (loading) loading.style.display = 'block';
        if (results) results.style.display = 'none';
        if (pdfBtn) pdfBtn.style.display = 'none';

        try {
            const response = await fetch(`${this.apiBase}/api/scans/${scanId}/analysis`);
            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.message || `HTTP ${response.status}`);
            }
            const data = await response.json();
            this._renderAnalysisData(data);
            // Store for PDF download
            if (pdfBtn) {
                pdfBtn.style.display = '';
                document.getElementById('analysisScanSelect').value = scanId;
            }
        } catch (error) {
            console.error('Analysis error:', error);
            this.showToast(`Analysis failed: ${error.message}`, 'error');
        } finally {
            if (loading) loading.style.display = 'none';
        }
    }

    _renderAnalysisData(data) {
        const resultsEl = document.getElementById('analysisResults');
        if (!resultsEl) return;

        const sum = data.severity_summary || {};
        const findings = data.findings || {};
        const hi = data.hardening_index;

        // Update summary cards
        document.getElementById('anaCountCritical').textContent = sum.critical || 0;
        document.getElementById('anaCountHigh').textContent = sum.high || 0;
        document.getElementById('anaCountMedium').textContent = sum.medium || 0;
        document.getElementById('anaCountLow').textContent = sum.low || 0;
        document.getElementById('anaSectionCountCritical').textContent = sum.critical || 0;
        document.getElementById('anaSectionCountHigh').textContent = sum.high || 0;
        document.getElementById('anaSectionCountMedium').textContent = sum.medium || 0;
        document.getElementById('anaSectionCountLow').textContent = sum.low || 0;

        // Hardening score card
        const hiEl = document.getElementById('analysisHardeningIndex');
        const hiLabel = document.getElementById('analysisHardeningLabel');
        const hiCard = document.getElementById('analysiHardeningCard');
        if (hi !== null && hi !== undefined) {
            hiEl.textContent = `${hi}/100`;
            const { label, cls } = hi < 40
                ? { label: 'Poor — Immediate action needed', cls: 'score-poor' }
                : hi < 60
                    ? { label: 'Fair — Improvement recommended', cls: 'score-fair' }
                    : hi < 80
                        ? { label: 'Good', cls: 'score-good' }
                        : { label: 'Excellent', cls: 'score-excellent' };
            hiLabel.textContent = label;
            if (hiCard) hiCard.className = `analysis-score-card ${cls}`;
        } else {
            hiEl.textContent = 'N/A';
            hiLabel.textContent = 'Not available';
        }

        // Render each severity section
        const SEV_META = {
            critical: { id: 'anaFindingsCritical', emptyMsg: 'No critical findings — great!' },
            high: { id: 'anaFindingsHigh', emptyMsg: 'No high-priority findings.' },
            medium: { id: 'anaFindingsMedium', emptyMsg: 'No medium-priority findings.' },
            low: { id: 'anaFindingsLow', emptyMsg: 'No low-priority findings.' },
        };

        const scanId = document.getElementById('analysisScanSelect')?.value || '';

        for (const [sev, meta] of Object.entries(SEV_META)) {
            const container = document.getElementById(meta.id);
            if (!container) continue;
            const items = findings[sev] || [];
            if (items.length === 0) {
                container.innerHTML = `<div class="analysis-empty"><i class="fas fa-check-circle"></i> ${meta.emptyMsg}</div>`;
                continue;
            }
            container.innerHTML = items.map((item, i) => {
                const msg = (item.message || '').replace(/'/g, "\\'");
                const cat = (item.category || 'General').replace(/'/g, "\\'");
                return `
                <div class="analysis-finding-card ${sev}">
                    <div class="afc-header">
                        <span class="afc-badge ${sev}">${sev.toUpperCase()}</span>
                        <span class="afc-category">${item.category || 'General'}</span>
                        <span class="afc-type">${item.type || 'finding'}</span>
                        <button onclick="dashboard.explainFinding('${scanId}','${msg}','${sev}','${cat}')"
                            title="Ask AI to explain this"
                            style="margin-left:auto;background:linear-gradient(135deg,#3b82f6,#06b6d4);color:white;border:none;border-radius:6px;padding:3px 10px;font-size:11px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:6px">
                            <i class="fas fa-robot"></i> Ask AI
                        </button>
                    </div>
                    <div class="afc-message">${item.message || ''}</div>
                </div>`;
            }).join('');
        }

        resultsEl.style.display = 'block';
    }

    async openAnalysis(scanId) {
        // Close any open modal
        document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
        this.switchView('analysis');
        this.updateBreadcrumb('analysis');
        document.querySelectorAll('.menu-item').forEach(i => i.classList.remove('active'));
        const mi = document.querySelector('.menu-item[data-view="analysis"]');
        if (mi) mi.classList.add('active');
        // Set the selector value
        const sel = document.getElementById('analysisScanSelect');
        if (sel) sel.value = scanId;
        await this.loadAnalysis(scanId);
    }

    scrollToSection(sectionId) {
        const el = document.getElementById(`analysis-${sectionId}`);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    showScanDetailsModal(scan, results = null) {
        const modal = document.getElementById('scanDetailsModal');
        const content = document.getElementById('scanDetailsContent');


        let findingsHtml = '';
        if (results && results.output_preview) {
            findingsHtml = `
                <div class="detail-section">
                    <h3>Output Preview</h3>
                    <pre style="background: var(--color-bg-lighter); padding: 15px; border-radius: var(--border-radius); overflow: auto; max-height: 300px; font-size: 12px; color: var(--color-text-secondary);">${results.output_preview}</pre>
                </div>
            `;
        }

        content.innerHTML = `
            <div class="scan-details">
                <div class="detail-section">
                    <h3>Scan Information</h3>
                    <div class="detail-row">
                        <div class="detail-label">Scan ID:</div>
                        <div class="detail-value">${scan.scan_id}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Status:</div>
                        <div class="detail-value"><span class="status-badge ${scan.status}">${scan.status}</span></div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Progress:</div>
                        <div class="detail-value">${scan.progress || 0}%</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Created:</div>
                        <div class="detail-value">${this.formatDateTime(scan.created_at)}</div>
                    </div>
                    ${scan.started_at ? `
                    <div class="detail-row">
                        <div class="detail-label">Started:</div>
                        <div class="detail-value">${this.formatDateTime(scan.started_at)}</div>
                    </div>
                    ` : ''}
                    ${scan.completed_at ? `
                    <div class="detail-row">
                        <div class="detail-label">Completed:</div>
                        <div class="detail-value">${this.formatDateTime(scan.completed_at)}</div>
                    </div>
                    ` : ''}
                    <div class="detail-row">
                        <div class="detail-label">Duration:</div>
                        <div class="detail-value">${this.calculateDuration(scan.started_at, scan.completed_at)}</div>
                    </div>
                </div>
                
                ${scan.current_phase ? `
                <div class="detail-section">
                    <h3>Current Phase</h3>
                    <div class="detail-row">
                        <div class="detail-label">Phase:</div>
                        <div class="detail-value">${scan.current_phase}</div>
                    </div>
                </div>
                ` : ''}
                
                ${scan.error_message ? `
                <div class="detail-section">
                    <h3>Error</h3>
                    <div class="detail-row">
                        <div class="detail-label">Message:</div>
                        <div class="detail-value" style="color: var(--color-danger);">${scan.error_message}</div>
                    </div>
                </div>
                ` : ''}
                
                ${findingsHtml}
                
                <div class="detail-section">
                    <h3>Actions</h3>
                    <div class="btn-group">
                        ${scan.status === 'running' ? `
                        <button class="btn-secondary" onclick="dashboard.cancelScan('${scan.scan_id}')">
                            <i class="fas fa-stop-circle"></i> Cancel Scan
                        </button>
                        ` : ''}
                        ${scan.status === 'completed' ? `
                        <button class="btn-primary" onclick="dashboard.viewScanResults('${scan.scan_id}')">
                            <i class="fas fa-chart-bar"></i> View Full Results
                        </button>
                        <button class="btn-secondary" onclick="dashboard.downloadRawOutput('${scan.scan_id}')">
                            <i class="fas fa-download"></i> Download Raw Output
                        </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;

        modal.classList.add('active');
    }

    showScanResultsModal(results) {
        const modal = document.getElementById('scanDetailsModal');
        const content = document.getElementById('scanDetailsContent');

        const parsedResults = results.parsed_results || {};
        const score = parsedResults.score || {};
        const severitySummary = parsedResults.severity_summary || {};
        const findings = parsedResults.findings || {};

        // Create severity badges HTML
        let severityBadgesHtml = '';
        if (Object.keys(severitySummary).length > 0) {
            severityBadgesHtml = `
                <div class="detail-section">
                    <h3>Security Findings by Severity</h3>
                    <div style="display: flex; gap: 15px; flex-wrap: wrap; margin-top: 15px;">
                        ${severitySummary.critical > 0 ? `
                        <div style="background: #FEE2E2; border: 2px solid #DC2626; border-radius: 8px; padding: 15px; min-width: 120px;">
                            <div style="color: #DC2626; font-size: 24px; font-weight: bold;">${severitySummary.critical}</div>
                            <div style="color: #DC2626; font-weight: 600;">CRITICAL</div>
                        </div>
                        ` : ''}
                        ${severitySummary.high > 0 ? `
                        <div style="background: #FED7AA; border: 2px solid #EA580C; border-radius: 8px; padding: 15px; min-width: 120px;">
                            <div style="color: #EA580C; font-size: 24px; font-weight: bold;">${severitySummary.high}</div>
                            <div style="color: #EA580C; font-weight: 600;">HIGH</div>
                        </div>
                        ` : ''}
                        ${severitySummary.medium > 0 ? `
                        <div style="background: #FEF3C7; border: 2px solid #D97706; border-radius: 8px; padding: 15px; min-width: 120px;">
                            <div style="color: #D97706; font-size: 24px; font-weight: bold;">${severitySummary.medium}</div>
                            <div style="color: #D97706; font-weight: 600;">MEDIUM</div>
                        </div>
                        ` : ''}
                        ${severitySummary.low > 0 ? `
                        <div style="background: #CFFAFE; border: 2px solid #0891B2; border-radius: 8px; padding: 15px; min-width: 120px;">
                            <div style="color: #0891B2; font-size: 24px; font-weight: bold;">${severitySummary.low}</div>
                            <div style="color: #0891B2; font-weight: 600;">LOW</div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        // Create findings list HTML
        let findingsHtml = '';
        const criticalFindings = findings.critical || [];
        const highFindings = findings.high || [];
        const mediumFindings = findings.medium || [];

        if (criticalFindings.length > 0 || highFindings.length > 0 || mediumFindings.length > 0) {
            findingsHtml = '<div class="detail-section"><h3>Top Priority Findings</h3>';

            // Show critical findings
            criticalFindings.slice(0, 5).forEach((finding, idx) => {
                findingsHtml += `
                    <div style="background: #FEE2E2; border-left: 4px solid #DC2626; padding: 12px; margin: 10px 0; border-radius: 4px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="background: #DC2626; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">CRITICAL</span>
                            <span style="color: #991B1B; font-weight: 500;">${finding.message}</span>
                        </div>
                    </div>
                `;
            });

            // Show high findings
            highFindings.slice(0, 5).forEach((finding, idx) => {
                findingsHtml += `
                    <div style="background: #FED7AA; border-left: 4px solid #EA580C; padding: 12px; margin: 10px 0; border-radius: 4px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="background: #EA580C; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">HIGH</span>
                            <span style="color: #9A3412; font-weight: 500;">${finding.message}</span>
                        </div>
                    </div>
                `;
            });

            // Show medium findings
            mediumFindings.slice(0, 3).forEach((finding, idx) => {
                findingsHtml += `
                    <div style="background: #FEF3C7; border-left: 4px solid #D97706; padding: 12px; margin: 10px 0; border-radius: 4px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="background: #D97706; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">MEDIUM</span>
                            <span style="color: #78350F; font-weight: 500;">${finding.message}</span>
                        </div>
                    </div>
                `;
            });

            findingsHtml += '</div>';
        }

        content.innerHTML = `
            <div class="scan-details">
                <div class="detail-section">
                    <h3>Scan Results</h3>
                    <div class="detail-row">
                        <div class="detail-label">Scan ID:</div>
                        <div class="detail-value">${results.scan_id}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Status:</div>
                        <div class="detail-value"><span class="status-badge completed">completed</span></div>
                    </div>
                    ${score.hardening_index ? `
                    <div class="detail-row">
                        <div class="detail-label">Security Score:</div>
                        <div class="detail-value"><strong>${score.hardening_index}/100</strong> (${score.status})</div>
                    </div>
                    ` : ''}
                    <div class="detail-row">
                        <div class="detail-label">Output Size:</div>
                        <div class="detail-value">${this.formatBytes(results.output_size || 0)}</div>
                    </div>
                </div>
                
                ${severityBadgesHtml}
                
                ${findingsHtml}
                
                <div class="detail-section">
                    <h3>Actions</h3>
                    <div class="btn-group">
                        <button class="btn-primary" onclick="dashboard.openAnalysis('${results.scan_id}')">
                            <i class="fas fa-microscope"></i> Full Analysis
                        </button>
                        <button class="btn-secondary" onclick="dashboard.downloadPDFReport('${results.scan_id}')">
                            <i class="fas fa-file-pdf"></i> Download PDF
                        </button>
                        <button class="btn-secondary" onclick="dashboard.downloadRawOutput('${results.scan_id}')">
                            <i class="fas fa-download"></i> Download Raw
                        </button>
                    </div>
                </div>
            </div>
        `;

        modal.classList.add('active');
    }

    switchView(viewName) {
        // Hide all views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });

        // Show selected view
        const targetView = document.getElementById(`${viewName}View`);
        if (targetView) {
            targetView.classList.add('active');
            this.currentView = viewName;

            // Save to localStorage
            localStorage.setItem('lastView', viewName);
        }
        // Populate analysis scan selector whenever Analysis is opened
        if (viewName === 'analysis') {
            this.populateAnalysisScanSelector();
        }
    }

    updateBreadcrumb(viewName) {
        const breadcrumb = document.getElementById('breadcrumb');
        const viewNames = {
            'dashboard': 'Dashboard',
            'scans': 'Security Scans',
            'history': 'Scan History',
            'analysis': 'Security Analysis',
            'reports': 'Reports',
            'settings': 'Settings'
        };
        breadcrumb.innerHTML = `<span>${viewNames[viewName] || 'Dashboard'}</span>`;
    }

    openScanModal(defaultType = 'quick') {
        const modal = document.getElementById('startScanModal');

        // Set default option
        document.querySelectorAll('.scan-option').forEach(option => {
            option.classList.remove('active');
            if (option.dataset.type === defaultType) {
                option.classList.add('active');
            }
        });

        modal.classList.add('active');
    }

    startPolling() {
        if (this.activePolling) {
            clearInterval(this.activePolling);
        }

        this.activePolling = setInterval(() => {
            this.loadData();
        }, this.pollingInterval);
    }

    restartPolling() {
        this.startPolling();
    }

    updateConnectionStatus(connected = true) {
        const statusElement = document.getElementById('connectionStatus');
        if (!statusElement) return;

        if (connected) {
            statusElement.innerHTML = '<i class="fas fa-circle" style="color: var(--color-success); font-size: 10px;"></i> Connected';
            statusElement.style.color = 'var(--color-success)';
        } else {
            statusElement.innerHTML = '<i class="fas fa-circle" style="color: var(--color-danger); font-size: 10px;"></i> Disconnected';
            statusElement.style.color = 'var(--color-danger)';
        }
    }

    updateTime() {
        const timeElement = document.getElementById('currentTime');
        if (!timeElement) return;

        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        timeElement.textContent = timeString;
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const icons = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle'
        };

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="${icons[type] || icons.info}"></i>
            <div class="toast-content">
                <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">&times;</button>
        `;

        container.appendChild(toast);

        // Add close event
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.remove();
        });

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }

    initCharts() {
        // Status chart
        const statusCtx = document.getElementById('statusChart');
        if (statusCtx) {
            new Chart(statusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Completed', 'Running', 'Failed', 'Pending'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: [
                            'var(--color-success)',
                            'var(--color-warning)',
                            'var(--color-danger)',
                            'var(--color-text-muted)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: 'var(--color-text)',
                                padding: 20
                            }
                        }
                    }
                }
            });
        }

        // Timeline chart
        const timelineCtx = document.getElementById('timelineChart');
        if (timelineCtx) {
            new Chart(timelineCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Scans',
                        data: [],
                        borderColor: 'var(--color-primary)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            grid: {
                                color: 'var(--color-border)'
                            },
                            ticks: {
                                color: 'var(--color-text-secondary)'
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'var(--color-border)'
                            },
                            ticks: {
                                color: 'var(--color-text-secondary)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: {
                                color: 'var(--color-text)'
                            }
                        }
                    }
                }
            });
        }
    }

    updateCharts() {
        // Update status chart
        const completed = this.history.length;
        const running = this.scans.filter(s => s.status === 'running').length;
        const failed = this.scans.filter(s => s.status === 'failed').length +
            this.history.filter(s => s.status === 'failed').length;
        const pending = this.scans.filter(s => s.status === 'pending').length;

        const statusChart = Chart.getChart('statusChart');
        if (statusChart) {
            statusChart.data.datasets[0].data = [completed, running, failed, pending];
            statusChart.update();
        }
    }

    generateReport() {
        // Get the most recent completed scan
        if (this.history.length === 0) {
            this.showToast('No completed scans available for report generation', 'warning');
            return;
        }

        const latestScan = this.history[0];
        this.downloadPDFReport(latestScan.scan_id);
    }

    async downloadPDFReport(scanId) {
        try {
            this.showToast('Generating PDF report...', 'info');

            const url = `${this.apiBase}/api/scans/${scanId}/pdf`;
            const response = await fetch(url);
            if (!response.ok) {
                let errorMessage = `Failed to generate PDF report (HTTP ${response.status})`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.message || errorMessage;
                } catch (jsonError) {
                    // Ignore JSON parse errors and use default message
                }
                throw new Error(errorMessage);
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `security_audit_${scanId}.pdf`;
            document.body.appendChild(link);
            link.click();
            link.remove();

            // Revoke the URL after a small delay to ensure download initiates
            setTimeout(() => {
                window.URL.revokeObjectURL(downloadUrl);
            }, 100);

            this.showToast('PDF report generated successfully', 'success');
        } catch (error) {
            console.error('Error generating PDF report:', error);
            this.showToast(`Failed to generate PDF report: ${error.message}`, 'error');
        }
    }

    saveConfig() {
        const apiEndpoint = document.getElementById('apiEndpoint').value;
        const scanTimeout = document.getElementById('scanTimeout').value;

        // Validate API endpoint
        try {
            new URL(apiEndpoint);
            this.apiBase = apiEndpoint;
        } catch (e) {
            this.showToast('Invalid API endpoint URL', 'error');
            return;
        }

        // Save to localStorage
        localStorage.setItem('apiEndpoint', apiEndpoint);
        localStorage.setItem('scanTimeout', scanTimeout);
        localStorage.setItem('notifyOnComplete', document.getElementById('notifyOnComplete').checked);
        localStorage.setItem('notifyOnFail', document.getElementById('notifyOnFail').checked);

        this.showToast('Configuration saved', 'success');

        // Restart polling with new API endpoint
        this.restartPolling();
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }

    loadSavedState() {
        // Load theme
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.getElementById('themeSelect').value = savedTheme;
        this.setTheme(savedTheme);

        // Load API endpoint
        const savedApiEndpoint = localStorage.getItem('apiEndpoint');
        if (savedApiEndpoint) {
            document.getElementById('apiEndpoint').value = savedApiEndpoint;
            this.apiBase = savedApiEndpoint;
        }

        // Load other settings
        const savedScanTimeout = localStorage.getItem('scanTimeout');
        if (savedScanTimeout) {
            document.getElementById('scanTimeout').value = savedScanTimeout;
        }

        const savedNotifyOnComplete = localStorage.getItem('notifyOnComplete');
        if (savedNotifyOnComplete !== null) {
            document.getElementById('notifyOnComplete').checked = savedNotifyOnComplete === 'true';
        }

        const savedNotifyOnFail = localStorage.getItem('notifyOnFail');
        if (savedNotifyOnFail !== null) {
            document.getElementById('notifyOnFail').checked = savedNotifyOnFail === 'true';
        }

        const savedRefreshInterval = localStorage.getItem('refreshInterval');
        if (savedRefreshInterval) {
            document.getElementById('refreshInterval').value = savedRefreshInterval;
            this.pollingInterval = parseInt(savedRefreshInterval) * 1000;
            this.restartPolling();
        }

        // Load last view
        const lastView = localStorage.getItem('lastView') || 'dashboard';
        this.switchView(lastView);
        this.updateBreadcrumb(lastView);

        // Update active menu item
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.view === lastView) {
                item.classList.add('active');
            }
        });
    }

    // Utility functions
    formatDateTime(dateString) {
        if (!dateString) return 'N/A';

        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatTimeAgo(dateString) {
        if (!dateString) return '';

        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);

        if (diffSec < 60) return 'just now';
        if (diffMin < 60) return `${diffMin}m ago`;
        if (diffHour < 24) return `${diffHour}h ago`;
        if (diffDay < 7) return `${diffDay}d ago`;

        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    calculateDuration(startString, endString) {
        if (!startString) return 'N/A';

        const start = new Date(startString);
        const end = endString ? new Date(endString) : new Date();
        const diffMs = end - start;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);

        if (diffSec < 60) return `${diffSec}s`;
        if (diffMin < 60) return `${diffMin}m ${diffSec % 60}s`;
        return `${diffHour}h ${diffMin % 60}m`;
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async showSystemInfo() {
        const modal = document.getElementById('systemInfoModal');
        const body = document.getElementById('systemInfoModalBody');
        if (!modal || !body) return;
        modal.classList.add('active');
        body.innerHTML = `
            <div style="text-align:center;padding:40px;color:var(--color-text-secondary)">
                <i class="fas fa-spinner fa-spin" style="font-size:32px;margin-bottom:12px"></i>
                <p>Loading system information...</p>
            </div>`;
        try {
            const resp = await fetch(`${this.apiBase}/api/system/status`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            const sys = data.system || {};
            const svc = data.service || {};
            const sto = data.storage || {};

            const lynisBadge = svc.lynis_installed
                ? `<span style="color:var(--color-success)"><i class="fas fa-check-circle"></i> Installed &amp; Ready</span>`
                : `<span style="color:var(--color-danger)"><i class="fas fa-times-circle"></i> Not Installed — run: <code>sudo apt install lynis</code></span>`;

            const diskPct = sto.total_gb ? Math.round((sto.used_gb / sto.total_gb) * 100) : 0;
            const diskColor = diskPct > 80 ? 'var(--color-danger)' : diskPct > 60 ? 'var(--color-warning)' : 'var(--color-success)';

            body.innerHTML = `
            <div style="display:grid;gap:16px">
                <!-- OS Info Card -->
                <div style="background:rgba(59,130,246,0.07);border:1px solid rgba(59,130,246,0.2);border-radius:10px;padding:16px">
                    <div style="font-size:12px;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px"><i class="fas fa-desktop"></i> System</div>
                    <table style="width:100%;border-collapse:collapse;font-size:14px">
                        <tr><td style="padding:6px 0;color:var(--color-text-secondary);width:140px">Hostname</td><td><strong>${sys.hostname || 'Unknown'}</strong></td></tr>
                        <tr><td style="padding:6px 0;color:var(--color-text-secondary)">Current User</td><td><strong>${sys.user || 'Unknown'}</strong></td></tr>
                        <tr><td style="padding:6px 0;color:var(--color-text-secondary)">Python Version</td><td><strong>${sys.python_version || 'Unknown'}</strong></td></tr>
                    </table>
                </div>

                <!-- Lynis Status Card -->
                <div style="background:rgba(16,185,129,0.07);border:1px solid rgba(16,185,129,0.2);border-radius:10px;padding:16px">
                    <div style="font-size:12px;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px"><i class="fas fa-shield-alt"></i> Audit Service</div>
                    <table style="width:100%;border-collapse:collapse;font-size:14px">
                        <tr><td style="padding:6px 0;color:var(--color-text-secondary);width:140px">Lynis</td><td>${lynisBadge}</td></tr>
                        <tr><td style="padding:6px 0;color:var(--color-text-secondary)">Active Scans</td><td><strong>${svc.active_scans || 0}</strong></td></tr>
                        <tr><td style="padding:6px 0;color:var(--color-text-secondary)">Session Scans</td><td><strong>${svc.total_scans || 0}</strong></td></tr>
                    </table>
                </div>

                <!-- Storage Card -->
                <div style="background:rgba(245,158,11,0.07);border:1px solid rgba(245,158,11,0.2);border-radius:10px;padding:16px">
                    <div style="font-size:12px;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px"><i class="fas fa-hdd"></i> Storage</div>
                    <div style="font-size:14px;margin-bottom:10px">
                        <span style="color:var(--color-text-secondary)">Used:</span> <strong>${sto.used_gb} GB</strong>
                        <span style="margin:0 8px;color:var(--color-text-muted)">of</span>
                        <strong>${sto.total_gb} GB</strong>
                        <span style="float:right;color:var(--color-text-secondary)">Free: <strong>${sto.free_gb} GB</strong></span>
                    </div>
                    <div style="background:var(--color-bg-lighter);border-radius:99px;height:8px;overflow:hidden">
                        <div style="height:100%;width:${diskPct}%;background:${diskColor};border-radius:99px;transition:width 1s ease"></div>
                    </div>
                    <div style="font-size:12px;color:${diskColor};margin-top:4px;text-align:right">${diskPct}% used</div>
                </div>
            </div>`;
        } catch (err) {
            body.innerHTML = `<div style="padding:20px;text-align:center;color:var(--color-danger)">
                <i class="fas fa-exclamation-triangle" style="font-size:32px"></i>
                <p>Failed to load system info: ${err.message}</p>
            </div>`;
        }
    }

    async explainFinding(scanId, message, severity, category) {
        const modal = document.getElementById('aiExplainModal');
        const content = document.getElementById('aiExplainContent');
        if (!modal || !content) return;

        modal.classList.add('active');
        content.innerHTML = `<div style="text-align:center;padding:32px;color:var(--color-text-secondary)">
            <i class="fas fa-robot" style="font-size:36px;margin-bottom:12px;color:var(--color-primary)"></i>
            <p>Consulting AI Security Advisor...</p>
            <small>Analyzing: "${message.substring(0, 60)}..."</small>
        </div>`;

        try {
            const resp = await fetch(`${this.apiBase}/api/scans/${scanId}/explain`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, severity, category })
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();

            const sevColors = { critical: '#DC2626', high: '#EA580C', medium: '#D97706', low: '#0891B2' };
            const sevColor = sevColors[severity] || '#64748B';
            const fixes = Array.isArray(data.how_to_fix) ? data.how_to_fix : [data.how_to_fix];

            content.innerHTML = `
            <div style="display:grid;gap:16px">
                <!-- Finding badge -->
                <div style="display:flex;align-items:flex-start;gap:12px;padding:12px;background:rgba(0,0,0,0.2);border-radius:8px;border-left:4px solid ${sevColor}">
                    <span style="background:${sevColor};color:white;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;text-transform:uppercase;flex-shrink:0">${severity}</span>
                    <span style="font-size:13px;color:var(--color-text-secondary);line-height:1.5">${message}</span>
                </div>

                <!-- What it means -->
                <div style="background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.25);border-radius:10px;padding:16px">
                    <div style="font-size:12px;font-weight:700;color:var(--color-primary);margin-bottom:8px;text-transform:uppercase;letter-spacing:0.5px">
                        <i class="fas fa-info-circle"></i> What this means
                    </div>
                    <p style="font-size:14px;line-height:1.7;color:var(--color-text);margin:0">${data.what_it_means || 'No explanation available.'}</p>
                </div>

                <!-- How to fix -->
                <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);border-radius:10px;padding:16px">
                    <div style="font-size:12px;font-weight:700;color:var(--color-success);margin-bottom:12px;text-transform:uppercase;letter-spacing:0.5px">
                        <i class="fas fa-tools"></i> How to fix it
                    </div>
                    <ol style="margin:0;padding-left:22px;display:grid;gap:10px">
                        ${fixes.map(step => `<li style="font-size:14px;line-height:1.6;color:var(--color-text)">${step}</li>`).join('')}
                    </ol>
                </div>

                <p style="font-size:11px;color:var(--color-text-muted);text-align:center;margin:0">
                    <i class="fas fa-robot"></i> AI-generated explanation. Always verify with your system administrator.
                </p>
            </div>`;
        } catch (err) {
            content.innerHTML = `<div style="padding:20px;text-align:center;color:var(--color-danger)">
                <p>Failed to get AI explanation: ${err.message}</p>
            </div>`;
        }
    }
}

// Initialize the dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new SecurityDashboard();
});

// Export for use in HTML onclick handlers
window.dashboard = null;
