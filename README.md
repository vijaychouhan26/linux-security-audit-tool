# Linux Security Audit and Hardening System using Lynis

This project focuses on auditing Linux systems for security misconfigurations and helping users understand how to harden their systems using industry best practices.

## Overview
Linux systems are widely used in servers and cloud environments, but many are deployed with insecure default configurations. This project uses Lynis as the core audit engine and builds a structured system around it to make audit results more understandable and actionable.

## Features
- Local Linux system security audit
- Uses Lynis as the audit engine
- Stores audit results for review
- Learning-oriented and human-readable design
- Extensible architecture for future enhancements

## Technologies Used
- Python
- Lynis
- Linux

## Current Scope
- Local system auditing
- Raw audit output collection
- Basic processing and storage

## Future Scope
- Human-readable reports
- Severity classification
- Remote system auditing
- Compliance checks

## Disclaimer
This tool is intended for educational and auditing purposes only.
# Linux Security Audit Tool - Phase 1

A professional, structured Linux security auditing tool using Lynis for local system scans.

## Phase 1: Core Scanner Implementation

This phase implements a reliable, well-structured command-line tool that:
- Runs Lynis audits on the local system
- Handles sudo privileges correctly
- Saves timestamped scan results
- Provides clear terminal feedback
- Prevents silent failures

## Prerequisites

1. **Linux System**: This tool is designed for Linux only
2. **Python 3.8+**: `python3 --version`
3. **Lynis Installed**: `sudo apt install lynis` (or equivalent for your distribution)
4. **Sudo Access**: For full system audit capabilities

## Installation

```bash
# Clone or copy the project
cd linux-security-audit-tool

# No pip install required for Phase 1 (pure Python)
# Just ensure you have Python 3.8+
python3 --version
# Linux Security Audit Tool - Phase 2

A professional, structured Linux security auditing tool with REST API.

## Phase 2: API Layer with Background Processing

This phase adds a clean Flask API with background execution:
- RESTful JSON API for scan management
- Background scan execution (non-blocking)
- Scan status tracking and progress updates
- Comprehensive error handling
- Scan history management

## API Endpoints

### Scan Management
- `POST /api/scans` - Start a new scan
- `GET /api/scans` - List all scans/jobs
- `GET /api/scans/<scan_id>` - Get scan status
- `GET /api/scans/<scan_id>/results` - Get scan results
- `GET /api/scans/<scan_id>/raw` - Get raw Lynis output
- `DELETE /api/scans/<scan_id>` - Cancel a running scan

### System Information
- `GET /api/history` - Get scan history from file system
- `GET /api/system/status` - Get system and service status
- `GET /health` - Health check endpoint
- `GET /api` - API documentation

## Installation for Phase 2

```bash
# Install Python dependencies
pip install -r requirements.txt

# Ensure Lynis is installed
sudo apt install lynis -y
