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
            document.getElementById('loadingDetails').style.display = 'none';
            
        } catch (error) {
            console.error('Error loading scan details:', error);
            this.showError(`Failed to load scan details: ${error.message}`);
        }
    }
    
    renderScanDetails(scan, results = null) {
        const content = document.getElementById('scanDetailsContent');
        
        let findingsHtml = '';
        if (results && results.output_preview) {
            findingsHtml = `
                <div class="section">
                    <div class="section-header">
                        <h2><i class="fas fa-file-alt"></i> Output Preview</h2>
                    </div>
                    <div class="table-container">
                        <pre style="padding: 20px; font-family: 'Courier New', monospace; font-size: 12px; line-height: 1.4; overflow: auto; max-height: 500px;">${results.output_preview}</pre>
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
        
        document.getElementById('loadingDetails').style.display = 'none';
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
