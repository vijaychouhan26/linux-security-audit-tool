# Linux Security Audit and Hardening System using Lynis

This project focuses on auditing Linux systems for security misconfigurations and helping users understand how to harden their systems using industry best practices.

## Overview
Linux systems are widely used in servers and cloud environments, but many are deployed with insecure default configurations. This project uses Lynis as the core audit engine and builds a structured system around it to make audit results more understandable and actionable.

## Features
- **Local Linux system security audit** using Lynis
- **Human-readable dashboard** with severity indicators (Critical, High, Medium, Low)
- **Automated severity classification** of security findings
- **PDF report generation** with professional formatting for non-technical users
- **RESTful API** for programmatic access
- **Real-time scan monitoring** and progress tracking
- **Scan history** with persistent storage
- **Interactive web dashboard** with dark mode

## New Features (Latest Update)
✨ **Human-Readable Output**: Scan results are now categorized by severity (Critical, High, Medium, Low) for easy understanding

✨ **PDF Report Downloads**: Generate professional PDF reports with human-readable summaries instead of raw Lynis output

✨ **Severity Dashboard**: Visual indicators show the impact level of security findings at a glance

✨ **Risk Assessment**: Automatic risk classification helps prioritize remediation efforts

## Technologies Used
- Python 3.8+
- Lynis (security audit engine)
- Flask (REST API)
- ReportLab (PDF generation)
- HTML/CSS/JavaScript (Web Dashboard)

## Current Features
- Local system auditing
- Severity classification (Critical/High/Medium/Low)
- Human-readable reports and PDF exports
- Web-based dashboard with real-time updates
- Persistent scan history

## Prerequisites

1. **Linux System**: This tool is designed for Linux only
2. **Python 3.8+**: `python3 --version`
3. **Lynis Installed**: `sudo apt install lynis` (or equivalent for your distribution)
4. **Sudo Access**: For full system audit capabilities

## Installation

```bash
# Clone or copy the project
cd linux-security-audit-tool

# Install Python dependencies
pip install -r requirements.txt

# Ensure Lynis is installed
sudo apt install lynis -y  # Ubuntu/Debian
# or
sudo yum install lynis -y  # RHEL/CentOS
```

## Usage

### Starting the Dashboard

```bash
# Start the API server (Terminal 1)
python3 run_api.py

# Start the dashboard (Terminal 2)
python3 frontend/dashboard.py

# Access the dashboard
# Open browser to http://localhost:8080
```

### Running a Security Scan

**Via Dashboard:**
1. Open http://localhost:8080 in your browser
2. Click "Quick Scan" or "Full Scan"
3. View results with severity indicators
4. Download PDF report

**Via API:**
```bash
# Start a scan
curl -X POST http://localhost:5000/api/scans

# Check scan status
curl http://localhost:5000/api/scans/<scan_id>

# Get results
curl http://localhost:5000/api/scans/<scan_id>/results

# Download PDF report
curl http://localhost:5000/api/scans/<scan_id>/pdf -o report.pdf
```

### Understanding Severity Levels

- **CRITICAL** 🔴: Immediate action required (e.g., root password issues, disabled security modules)
- **HIGH** 🟠: Should be addressed soon (e.g., firewall disabled, weak encryption)
- **MEDIUM** 🟡: Plan for remediation (e.g., configuration improvements, missing updates)
- **LOW** 🔵: Best practice recommendations (e.g., optional optimizations)

## API Endpoints

### Scan Management
- `POST /api/scans` - Start a new scan
- `GET /api/scans` - List all scans/jobs
- `GET /api/scans/<scan_id>` - Get scan status
- `GET /api/scans/<scan_id>/results` - Get scan results with severity classification
- `GET /api/scans/<scan_id>/raw` - Get raw Lynis output
- `GET /api/scans/<scan_id>/pdf` - Download PDF report (**NEW**)
- `DELETE /api/scans/<scan_id>` - Cancel a running scan

### System Information
- `GET /api/history` - Get scan history from file system
- `GET /api/system/status` - Get system and service status
- `GET /health` - Health check endpoint
- `GET /api` - API documentation
