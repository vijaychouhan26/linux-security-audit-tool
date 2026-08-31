# Linux Security Audit & Hardening System

> Automated Linux security auditing, risk classification, reporting, and REST-based access using Lynis, Python, Flask, and ReportLab.

## About the Project

This project turns raw Lynis security-audit output into a structured workflow for reviewing Linux security posture and prioritizing remediation.

The system is designed around practical security operations: run an audit, collect findings, classify risk, expose results through an API, retain scan history, and generate a professional report.

## What It Does

- Runs local Linux security audits using **Lynis**
- Classifies findings into **Critical / High / Medium / Low** severity levels
- Presents findings through a human-readable web dashboard
- Generates professional **PDF security reports**
- Exposes audit operations through a **Flask REST API**
- Tracks scan status and history
- Provides system/service health information
- Helps prioritize remediation instead of presenting only raw scanner output

## Architecture

```text
Linux Host
   |
   v
Lynis Security Audit
   |
   v
Python Processing / Severity Classification
   |
   +----> REST API (Flask)
   |
   +----> Web Dashboard
   |
   +----> PDF Reporting (ReportLab)
   |
   v
Security Findings / Remediation Priorities
```

## Technologies

- **Linux:** Ubuntu / Debian / Kali-compatible workflow
- **Security:** Lynis
- **Backend:** Python, Flask
- **Reporting:** ReportLab
- **Web:** HTML / CSS / JavaScript
- **API:** REST / JSON
- **Version Control:** Git / GitHub

## Security & Troubleshooting Skills Demonstrated

This project also reflects practical skills relevant to technical support and infrastructure troubleshooting:

- Linux command-line investigation
- Service and system-status checks
- Log and audit-output analysis
- Root-cause-oriented troubleshooting
- HTTP/REST API request-response handling
- Structured issue documentation
- Risk prioritization and remediation tracking

## Installation

### Prerequisites

- Linux system
- Python 3.8+
- Lynis
- sudo access for full audit coverage

### Debian / Ubuntu / Kali

```bash
sudo apt update
sudo apt install lynis python3 python3-pip -y
```

### Python dependencies

```bash
pip install -r requirements.txt
```

## Usage

Start the API:

```bash
python3 run_api.py
```

Then start the dashboard using the project entry point available in your checkout.

Example API workflow:

```bash
# Health check
curl http://localhost:5000/health

# Start a scan
curl -X POST http://localhost:5000/api/scans

# List scans
curl http://localhost:5000/api/scans

# Read scan results
curl http://localhost:5000/api/scans/<scan_id>/results

# Download a generated report
curl http://localhost:5000/api/scans/<scan_id>/pdf -o report.pdf
```

## API Overview

| Endpoint | Purpose |
|---|---|
| `POST /api/scans` | Start a scan |
| `GET /api/scans` | List scans |
| `GET /api/scans/<scan_id>` | Scan status |
| `GET /api/scans/<scan_id>/results` | Classified findings |
| `GET /api/scans/<scan_id>/raw` | Raw Lynis output |
| `GET /api/scans/<scan_id>/pdf` | PDF report |
| `DELETE /api/scans/<scan_id>` | Cancel a scan |
| `GET /api/history` | Scan history |
| `GET /api/system/status` | System/service status |
| `GET /health` | Service health |

## Severity Model

- **Critical** — immediate attention required
- **High** — high-priority remediation
- **Medium** — remediation should be planned
- **Low** — best-practice or lower-impact improvement

## Documentation

- [Authorized VAPT Reconnaissance Assessment](docs/authorized-vapt-reconnaissance-assessment.md)

## Author

**Vijay Chouhan**  
B.Tech Computer Science — Cybersecurity Specialization  
Cybersecurity | VAPT | Linux | Networking | Web Security

GitHub: https://github.com/vijaychouhan26
LinkedIn: https://linkedin.com/in/vijay-chouhan-1130632b7
