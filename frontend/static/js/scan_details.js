// Scan Details Page JavaScript
class ScanDetails {
    constructor() {
        this.scanId = this.getScanIdFromURL();
        this.apiBase = localStorage.getItem('apiEndpoint') || 'http://localhost:5000';
        
        this.init();
    }
    
    getScanIdFromURL() {
        const path = window.location.pathname;
        const parts = path.split('/');
        return parts[parts.length - 1];
    }
    
    async init() {
        if (!this.scanId) {
            this.showError('No scan ID provided');
            return;
        }
        
        document.getElementById('scanIdPlaceholder').textContent = this.scanId;
        
        await this.loadScanDetails();
    }
    
    async loadScanDetails() {
        try {
            // Load scan status
            const statusResponse = await fetch(`${this.apiBase}/api/scans/${this.scanId}`);
            if (!statusResponse.ok) {
                throw new Error('Failed to fetch scan status');
            }
            
            const scan = await statusResponse.json();
            
            // Load results if available
            let results = null;
            if (scan.status === 'completed') {
                const resultsResponse = await fetch(`${this.apiBase}/api/scans/${this.scanId}/results`);
                if (resultsResponse.ok) {
                    results = await resultsResponse.json();
                }
            }
            
            // Render details
            this.renderScanDetails(scan, results);
            
            // Hide loading screen
            const loadingEl = document.getElementById('loadingDetails');
            if (loadingEl) {
                loadingEl.style.display = 'none';
            }
            
        } catch (error) {
            console.error('Error loading scan details:', error);
            this.showError(`Failed to load scan details: ${error.message}`);
        }
    }
    
    renderScanDetails(scan, results = null) {
        const content = document.getElementById('scanDetailsContent');
        
        // Build findings HTML with parsed data
        let findingsHtml = '';
        let parsedResultsHtml = '';
        
        if (results && results.parsed_results) {
            // Display parsed security results
            parsedResultsHtml = this.renderParsedResults(results.parsed_results);
        }
        
        if (results && results.output_preview) {
            findingsHtml = `
                <div class="section">
                    <div class="section-header">
                        <h2><i class="fas fa-file-alt"></i> Raw Output Preview</h2>
                    </div>
                    <div class="table-container">
                        <pre style="padding: 20px; background: var(--color-bg-secondary); border-radius: 8px; font-family: 'Courier New', monospace; font-size: 12px; line-height: 1.4; overflow: auto; max-height: 500px; white-space: pre-wrap; word-wrap: break-word;">${this.escapeHtml(results.output_preview)}</pre>
                    </div>
                </div>
            `;
        }
        
        content.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon ${this.getStatusColor(scan.status)}">
                        <i class="fas fa-${this.getStatusIcon(scan.status)}"></i>
                    </div>
                    <div class="stat-info">
                        <h3>${scan.status.toUpperCase()}</h3>
                        <p>Status</p>
                    </div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-icon primary">
                        <i class="fas fa-percentage"></i>
                    </div>
                    <div class="stat-info">
                        <h3>${scan.progress || 0}%</h3>
                        <p>Progress</p>
                    </div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-icon info">
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="stat-info">
                        <h3>${this.calculateDuration(scan.started_at, scan.completed_at)}</h3>
                        <p>Duration</p>
                    </div>
                </div>
                
                ${results && results.output_size ? `
                <div class="stat-card">
                    <div class="stat-icon success">
                        <i class="fas fa-database"></i>
                    </div>
                    <div class="stat-info">
                        <h3>${this.formatBytes(results.output_size)}</h3>
                        <p>Output Size</p>
                    </div>
                </div>
                ` : ''}
            </div>
            
            <div class="section">
                <div class="section-header">
                    <h2><i class="fas fa-info-circle"></i> Scan Information</h2>
                </div>
                <div class="table-container">
                    <table class="data-table">
                        <tbody>
                            <tr>
                                <td style="width: 150px; color: var(--color-text-secondary);">Scan ID:</td>
                                <td><code>${scan.scan_id}</code></td>
                            </tr>
                            <tr>
                                <td style="color: var(--color-text-secondary);">Status:</td>
                                <td><span class="status-badge ${scan.status}">${scan.status}</span></td>
                            </tr>
                            ${scan.current_phase ? `
                            <tr>
                                <td style="color: var(--color-text-secondary);">Current Phase:</td>
                                <td>${scan.current_phase}</td>
                            </tr>
                            ` : ''}
                            <tr>
                                <td style="color: var(--color-text-secondary);">Created:</td>
                                <td>${this.formatDateTime(scan.created_at)}</td>
                            </tr>
                            ${scan.started_at ? `
                            <tr>
                                <td style="color: var(--color-text-secondary);">Started:</td>
                                <td>${this.formatDateTime(scan.started_at)}</td>
                            </tr>
                            ` : ''}
                            ${scan.completed_at ? `
                            <tr>
                                <td style="color: var(--color-text-secondary);">Completed:</td>
                                <td>${this.formatDateTime(scan.completed_at)}</td>
                            </tr>
                            ` : ''}
                            <tr>
                                <td style="color: var(--color-text-secondary);">Duration:</td>
                                <td>${this.calculateDuration(scan.started_at, scan.completed_at)}</td>
                            </tr>
                            ${scan.error_message ? `
                            <tr>
                                <td style="color: var(--color-text-secondary);">Error:</td>
                                <td style="color: var(--color-danger);">${scan.error_message}</td>
                            </tr>
                            ` : ''}
                        </tbody>
                    </table>
                </div>
            </div>
            
            ${parsedResultsHtml}
            
            ${findingsHtml}
            
            <div class="section">
                <div class="section-header">
                    <h2><i class="fas fa-cogs"></i> Actions</h2>
                </div>
                <div class="btn-group">
                    ${scan.status === 'running' ? `
                    <button class="btn-danger" onclick="scanDetails.cancelScan()">
                        <i class="fas fa-stop-circle"></i> Cancel Scan
                    </button>
                    ` : ''}
                    
                    ${scan.status === 'completed' ? `
                    <button class="btn-primary" onclick="scanDetails.downloadRawOutput()">
                        <i class="fas fa-download"></i> Download Raw Output
                    </button>
                    <button class="btn-secondary" onclick="scanDetails.viewFullResults()">
                        <i class="fas fa-external-link-alt"></i> View Full Results
                    </button>
                    ` : ''}
                    
                    <button class="btn-secondary" onclick="window.location.href='/'">
                        <i class="fas fa-arrow-left"></i> Back to Dashboard
                    </button>
                </div>
            </div>
        `;
    }
    
    async cancelScan() {
        if (!confirm('Are you sure you want to cancel this scan?')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/api/scans/${this.scanId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to cancel scan');
            }
            
            alert('Scan cancelled successfully');
            window.location.reload();
        } catch (error) {
            console.error('Error cancelling scan:', error);
            alert(`Failed to cancel scan: ${error.message}`);
        }
    }
    
    downloadRawOutput() {
        window.open(`${this.apiBase}/api/scans/${this.scanId}/raw?download=true`, '_blank');
    }
    
    viewFullResults() {
        window.open(`${this.apiBase}/api/scans/${this.scanId}/results`, '_blank');
    }
    
    showError(message) {
        const content = document.getElementById('scanDetailsContent');
        content.innerHTML = `
            <div class="empty-state" style="padding: 40px; text-align: center;">
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: var(--color-danger); margin-bottom: 20px;"></i>
                <h2 style="margin-bottom: 10px;">Error Loading Scan Details</h2>
                <p style="color: var(--color-text-secondary); margin-bottom: 20px;">${message}</p>
                <button class="btn-primary" onclick="window.location.href='/'">
                    <i class="fas fa-arrow-left"></i> Back to Dashboard
                </button>
            </div>
        `;
        
        const loadingEl = document.getElementById('loadingDetails');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
    }
    
    renderParsedResults(parsed) {
        if (!parsed) return '';
        
        const score = parsed.score || {};
        const stats = parsed.statistics || {};
        const systemInfo = parsed.system_info || {};
        const securityComponents = parsed.security_components || {};
        const findings = parsed.findings || {};
        
        // Get status color for hardening score
        const scoreStatus = score.status || 'poor';
        const scoreColor = this.getScoreColor(scoreStatus);
        
        return `
            <!-- Security Score -->
            <div class="section">
                <div class="section-header">
                    <h2><i class="fas fa-shield-alt"></i> Security Score</h2>
                </div>
                <div class="stats-grid">
                    <div class="stat-card" style="grid-column: span 2;">
                        <div class="stat-icon ${scoreColor}">
                            <i class="fas fa-shield-alt"></i>
                        </div>
                        <div class="stat-info">
                            <h3 style="font-size: 2em;">${score.hardening_index || 0}/100</h3>
                            <p>Hardening Index</p>
                            <div style="margin-top: 10px; background: var(--color-bg-secondary); border-radius: 10px; height: 20px; overflow: hidden;">
                                <div style="width: ${score.hardening_index || 0}%; height: 100%; background: linear-gradient(90deg, var(--color-${scoreColor}), var(--color-${scoreColor}-light)); transition: width 0.3s ease;"></div>
                            </div>
                            <small style="margin-top: 5px; display: block; text-transform: uppercase; color: var(--color-${scoreColor});">${scoreStatus}</small>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon primary">
                            <i class="fas fa-tasks"></i>
                        </div>
                        <div class="stat-info">
                            <h3>${stats.tests_performed || 0}</h3>
                            <p>Tests Performed</p>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon ${stats.warnings_count > 0 ? 'danger' : 'success'}">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <div class="stat-info">
                            <h3>${stats.warnings_count || 0}</h3>
                            <p>Warnings</p>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon info">
                            <i class="fas fa-lightbulb"></i>
                        </div>
                        <div class="stat-info">
                            <h3>${stats.suggestions_count || 0}</h3>
                            <p>Suggestions</p>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon success">
                            <i class="fas fa-plug"></i>
                        </div>
                        <div class="stat-info">
                            <h3>${stats.plugins_enabled || 0}</h3>
                            <p>Plugins Enabled</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- System Information -->
            ${systemInfo.os_name ? `
            <div class="section">
                <div class="section-header">
                    <h2><i class="fas fa-server"></i> System Information</h2>
                </div>
                <div class="table-container">
                    <table class="data-table">
                        <tbody>
                            ${systemInfo.os_name ? `<tr><td style="width: 200px; color: var(--color-text-secondary);">Operating System:</td><td>${this.escapeHtml(systemInfo.os_name)}</td></tr>` : ''}
                            ${systemInfo.os_version ? `<tr><td style="color: var(--color-text-secondary);">OS Version:</td><td>${this.escapeHtml(systemInfo.os_version)}</td></tr>` : ''}
                            ${systemInfo.kernel_version ? `<tr><td style="color: var(--color-text-secondary);">Kernel Version:</td><td>${this.escapeHtml(systemInfo.kernel_version)}</td></tr>` : ''}
                            ${systemInfo.hostname ? `<tr><td style="color: var(--color-text-secondary);">Hostname:</td><td>${this.escapeHtml(systemInfo.hostname)}</td></tr>` : ''}
                            ${systemInfo.hardware_platform ? `<tr><td style="color: var(--color-text-secondary);">Hardware Platform:</td><td>${this.escapeHtml(systemInfo.hardware_platform)}</td></tr>` : ''}
                        </tbody>
                    </table>
                </div>
            </div>
            ` : ''}
            
            <!-- Security Components -->
            <div class="section">
                <div class="section-header">
                    <h2><i class="fas fa-shield-virus"></i> Security Components</h2>
                </div>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-icon ${securityComponents.firewall ? 'success' : 'danger'}">
                            <i class="fas fa-${securityComponents.firewall ? 'check-circle' : 'times-circle'}"></i>
                        </div>
                        <div class="stat-info">
                            <h3>${securityComponents.firewall ? 'Installed' : 'Not Installed'}</h3>
                            <p>Firewall</p>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon ${securityComponents.intrusion_software ? 'success' : 'danger'}">
                            <i class="fas fa-${securityComponents.intrusion_software ? 'check-circle' : 'times-circle'}"></i>
                        </div>
                        <div class="stat-info">
                            <h3>${securityComponents.intrusion_software ? 'Installed' : 'Not Installed'}</h3>
                            <p>Intrusion Detection</p>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon ${securityComponents.malware_scanner ? 'success' : 'danger'}">
                            <i class="fas fa-${securityComponents.malware_scanner ? 'check-circle' : 'times-circle'}"></i>
                        </div>
                        <div class="stat-info">
                            <h3>${securityComponents.malware_scanner ? 'Installed' : 'Not Installed'}</h3>
                            <p>Malware Scanner</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Warnings -->
            ${findings.warnings && findings.warnings.length > 0 ? `
            <div class="section">
                <div class="section-header">
                    <h2><i class="fas fa-exclamation-triangle"></i> Warnings (${findings.warnings.length})</h2>
                </div>
                <div class="table-container">
                    ${findings.warnings.map(warning => `
                        <div style="padding: 15px; margin-bottom: 10px; background: var(--color-bg-secondary); border-left: 4px solid var(--color-danger); border-radius: 4px;">
                            <div style="display: flex; align-items: start;">
                                <i class="fas fa-exclamation-circle" style="color: var(--color-danger); margin-right: 12px; margin-top: 3px;"></i>
                                <div style="flex: 1;">
                                    <p style="margin: 0; color: var(--color-text-primary);">${this.escapeHtml(warning.message)}</p>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            <!-- Suggestions -->
            ${findings.suggestions && findings.suggestions.length > 0 ? `
            <div class="section">
                <div class="section-header">
                    <h2><i class="fas fa-lightbulb"></i> Security Suggestions (${findings.suggestions.length})</h2>
                </div>
                <div class="table-container">
                    ${findings.suggestions.map(suggestion => `
                        <div style="padding: 15px; margin-bottom: 10px; background: var(--color-bg-secondary); border-left: 4px solid var(--color-info); border-radius: 4px;">
                            <div style="display: flex; align-items: start; justify-content: space-between;">
                                <div style="display: flex; align-items: start; flex: 1;">
                                    <i class="fas fa-lightbulb" style="color: var(--color-info); margin-right: 12px; margin-top: 3px;"></i>
                                    <div style="flex: 1;">
                                        <p style="margin: 0 0 5px 0; color: var(--color-text-primary); font-weight: 500;">${this.escapeHtml(suggestion.message)}</p>
                                        ${suggestion.details && suggestion.details.length > 0 ? `
                                            <ul style="margin: 8px 0 0 0; padding-left: 20px; color: var(--color-text-secondary); font-size: 0.9em;">
                                                ${suggestion.details.map(detail => `<li>${this.escapeHtml(detail)}</li>`).join('')}
                                            </ul>
                                        ` : ''}
                                    </div>
                                </div>
                                <span style="background: var(--color-bg-tertiary); padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-family: monospace; white-space: nowrap; margin-left: 10px;">${this.escapeHtml(suggestion.test_id)}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
        `;
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getScoreColor(status) {
        switch (status) {
            case 'excellent': return 'success';
            case 'good': return 'primary';
            case 'fair': return 'warning';
            case 'poor': return 'danger';
            default: return 'primary';
        }
    }
    
    // Utility functions
    getStatusColor(status) {
        switch (status) {
            case 'completed': return 'success';
            case 'running': return 'warning';
            case 'failed': return 'danger';
            default: return 'primary';
        }
    }
    
    getStatusIcon(status) {
        switch (status) {
            case 'completed': return 'check-circle';
            case 'running': return 'spinner';
            case 'failed': return 'times-circle';
            default: return 'clock';
        }
    }
    
    formatDateTime(dateString) {
        if (!dateString) return 'N/A';
        
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
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
        if (!bytes || bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.scanDetails = new ScanDetails();
});
