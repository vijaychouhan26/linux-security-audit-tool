#!/usr/bin/env python3
"""
Complete Linux Security Audit API in a single file - FIXED VERSION.
This includes scanning functionality with proper imports.
"""

import os
import sys  # ADDED THIS IMPORT
import json
import uuid
import threading
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS
import logging

# PDF generation support
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    import io as _io
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configuration
SCANS_DIR = Path("scans")
LOGS_DIR = Path("logs")
SCANS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# In-memory storage for scan jobs
scan_jobs = {}
scan_lock = threading.Lock()

class ScanJob:
    def __init__(self, scan_id):
        self.scan_id = scan_id
        self.status = "pending"
        self.progress = 0
        self.current_phase = "Initializing"
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.thread = None
    
    def to_dict(self):
        return {
            "scan_id": self.scan_id,
            "status": self.status,
            "progress": self.progress,
            "current_phase": self.current_phase,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }

def run_lyniss_scan(job):
    """Run Lynis scan in background thread."""
    try:
        job.status = "running"
        job.started_at = datetime.now()
        job.current_phase = "Checking Lynis installation"
        job.progress = 10
        
        # Check if Lynis is installed
        result = subprocess.run(["which", "lynis"], capture_output=True, text=True)
        if result.returncode != 0:
            job.status = "failed"
            job.error = "Lynis not found. Install with: sudo apt install lynis"
            job.completed_at = datetime.now()
            return
        
        job.current_phase = "Running security audit"
        job.progress = 30
        
        # Create scan directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scan_dir = SCANS_DIR / f"{timestamp}_{job.scan_id}"
        scan_dir.mkdir(parents=True, exist_ok=True)
        
        # Run Lynis
        cmd = ["sudo", "lynis", "audit", "system", "--quick"]
        logger.info(f"Running command: {' '.join(cmd)}")
        
        job.current_phase = "Executing Lynis commands"
        job.progress = 50
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        job.current_phase = "Processing results"
        job.progress = 80
        
        # Save output
        output_file = scan_dir / "lynis_output.txt"
        with open(output_file, 'w') as f:
            f.write(f"=== STDOUT ===\n{result.stdout}\n")
            f.write(f"=== STDERR ===\n{result.stderr}\n")
            f.write(f"=== RETURN CODE ===\n{result.returncode}\n")
        
        # Save metadata
        metadata = {
            "scan_id": job.scan_id,
            "timestamp": datetime.now().isoformat(),
            "return_code": result.returncode,
            "output_file": str(output_file),
            "command": " ".join(cmd)
        }
        
        metadata_file = scan_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        job.result = metadata
        job.status = "completed"
        job.progress = 100
        job.completed_at = datetime.now()
        job.current_phase = "Scan completed"
        
        logger.info(f"Scan {job.scan_id} completed successfully")
        
    except subprocess.TimeoutExpired:
        job.status = "failed"
        job.error = "Scan timed out after 10 minutes"
        job.completed_at = datetime.now()
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.completed_at = datetime.now()
        logger.error(f"Scan {job.scan_id} failed: {e}")

# API Endpoints
@app.route('/')
def home():
    return jsonify({
        "service": "Linux Security Audit Tool",
        "version": "2.0.0",
        "status": "running",
        "endpoints": [
            "GET /health",
            "GET /api",
            "POST /api/scans",
            "GET /api/scans",
            "GET /api/scans/<id>",
            "GET /api/scans/<id>/results",
            "GET /api/scans/<id>/raw",
            "DELETE /api/scans/<id>",
            "GET /api/history"
        ]
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api')
def api_info():
    return jsonify({
        "name": "Linux Security Audit API",
        "description": "REST API for running and managing Lynis security scans",
        "version": "v1"
    })

@app.route('/api/scans', methods=['POST'])
def start_scan():
    """Start a new security scan."""
    scan_id = f"scan_{uuid.uuid4().hex[:8]}"
    
    job = ScanJob(scan_id)
    
    with scan_lock:
        scan_jobs[scan_id] = job
    
    # Start scan in background thread
    thread = threading.Thread(target=run_lyniss_scan, args=(job,), daemon=True)
    job.thread = thread
    thread.start()
    
    return jsonify({
        "message": "Scan started successfully",
        "scan_id": scan_id,
        "status_endpoint": f"/api/scans/{scan_id}",
        "results_endpoint": f"/api/scans/{scan_id}/results",
        "estimated_time": "2-10 minutes"
    }), 202

@app.route('/api/scans', methods=['GET'])
def list_scans():
    """List all scan jobs."""
    with scan_lock:
        jobs = [job.to_dict() for job in scan_jobs.values()]
    
    # Also list completed scans from filesystem
    history = []
    if SCANS_DIR.exists():
        for item in SCANS_DIR.iterdir():
            if item.is_dir():
                metadata_file = item / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        # Add quick findings count
                        for fname in ['lynis_output.txt', 'lynis_raw_output.txt']:
                            out_f = item / fname
                            if out_f.exists():
                                try:
                                    raw = out_f.read_text(errors='replace')
                                    parsed = parse_lynis_findings(raw)
                                    metadata['findings_count'] = parsed['stats']['total_findings']
                                    metadata['hardening_index'] = parsed['hardening_index']
                                    metadata['severity_summary'] = parsed['severity_summary']
                                except Exception:
                                    pass
                                break
                        history.append(metadata)
                    except:
                        pass

    return jsonify({
        "active_jobs": jobs,
        "history": history,
        "total": len(jobs) + len(history)
    })

@app.route('/api/scans/<scan_id>', methods=['GET'])
def get_scan_status(scan_id):
    """Get status of a specific scan."""
    with scan_lock:
        job = scan_jobs.get(scan_id)
    
    if job:
        return jsonify(job.to_dict())
    
    # Check if scan exists in filesystem
    for item in SCANS_DIR.iterdir():
        if item.is_dir() and scan_id in item.name:
            metadata_file = item / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    return jsonify({
                        "scan_id": scan_id,
                        "status": "completed",
                        "from_history": True,
                        **metadata
                    })
                except:
                    pass
    
    return jsonify({"error": "Scan not found"}), 404

@app.route('/api/scans/<scan_id>/results', methods=['GET'])
def get_scan_results(scan_id):
    """Get results of a completed scan with parsed analysis data."""
    # Check in-memory jobs first
    with scan_lock:
        job = scan_jobs.get(scan_id)

    def _load_from_dir(d):
        meta_f = d / 'metadata.json'
        meta = {}
        if meta_f.exists():
            try:
                meta = json.loads(meta_f.read_text())
            except Exception:
                pass
        for fname in ['lynis_output.txt', 'lynis_raw_output.txt']:
            out_f = d / fname
            if out_f.exists():
                try:
                    raw = out_f.read_text(errors='replace')
                    parsed = parse_lynis_findings(raw)
                    result = {
                        'scan_id': scan_id,
                        'status': 'completed',
                        'from_history': True,
                        **meta,
                        'output_size': len(raw),
                        'raw_output_url': f'/api/scans/{scan_id}/raw',
                        'output_preview': raw[:800] + '...' if len(raw) > 800 else raw,
                        'hardening_index': parsed['hardening_index'],
                        'system_info': parsed['system_info'],
                        'severity_summary': parsed['severity_summary'],
                        'stats': parsed['stats'],
                        'parsed_results': {
                            'score': {
                                'hardening_index': parsed['hardening_index'],
                                'status': (
                                    'Poor' if (parsed['hardening_index'] or 0) < 40 else
                                    'Fair' if (parsed['hardening_index'] or 0) < 60 else
                                    'Good' if (parsed['hardening_index'] or 0) < 80 else
                                    'Excellent'
                                ) if parsed['hardening_index'] else 'Unknown'
                            },
                            'severity_summary': parsed['severity_summary'],
                            'findings': {
                                k: [{'message': f['message'], 'category': f.get('category', ''), 'type': f.get('type', '')}
                                    for f in v[:10]]
                                for k, v in parsed['findings'].items()
                            }
                        }
                    }
                    return result
                except Exception:
                    pass
        # Output file missing — return just metadata
        if meta:
            return {'scan_id': scan_id, 'status': 'completed', 'from_history': True, **meta}
        return None

    if job and job.status == 'completed' and job.result:
        out_path = Path(job.result.get('output_file', ''))
        if out_path.exists():
            r = _load_from_dir(out_path.parent)
            if r:
                return jsonify(r)
        return jsonify(job.result)

    for item in SCANS_DIR.iterdir():
        if not item.is_dir():
            continue
        if scan_id in item.name:
            r = _load_from_dir(item)
            if r:
                return jsonify(r)
        for sub in item.iterdir() if item.is_dir() else []:
            if sub.is_dir() and scan_id in sub.name:
                r = _load_from_dir(sub)
                if r:
                    return jsonify(r)

    return jsonify({'error': 'Results not found or scan not complete'}), 404

@app.route('/api/scans/<scan_id>/raw', methods=['GET'])
def get_raw_output(scan_id):
    """Get raw Lynis output."""
    for item in SCANS_DIR.iterdir():
        if item.is_dir() and scan_id in item.name:
            output_file = item / "lynis_output.txt"
            if output_file.exists():
                return send_file(
                    str(output_file),
                    mimetype='text/plain',
                    as_attachment=True,
                    download_name=f"lynis_scan_{scan_id}.txt"
                )
    
    return jsonify({"error": "Raw output not found"}), 404

@app.route('/api/scans/<scan_id>', methods=['DELETE'])
def cancel_scan(scan_id):
    """Cancel a running scan."""
    with scan_lock:
        job = scan_jobs.get(scan_id)
    
    if not job:
        return jsonify({"error": "Scan not found"}), 404
    
    if job.status == "running":
        # Try to cancel (this is a simple implementation)
        job.status = "cancelled"
        job.error = "Cancelled by user"
        job.completed_at = datetime.now()
        return jsonify({"message": "Scan cancelled"})
    
    return jsonify({"error": "Scan cannot be cancelled"}), 400

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get scan history from filesystem."""
    history = []
    
    if SCANS_DIR.exists():
        for item in sorted(SCANS_DIR.iterdir(), key=lambda x: x.name, reverse=True):
            if item.is_dir():
                metadata_file = item / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        history.append(metadata)
                    except:
                        # Basic info from directory name
                        history.append({
                            "directory": str(item),
                            "name": item.name
                        })
    
    return jsonify({
        "scans": history,
        "total": len(history)
    })

@app.route('/api/system/status', methods=['GET'])
def system_status():
    """Get system status."""
    import getpass
    import shutil
    
    # Check Lynis
    lynis_installed = subprocess.run(["which", "lynis"], capture_output=True).returncode == 0
    
    # Disk usage
    total, used, free = shutil.disk_usage(".")
    
    return jsonify({
        "system": {
            "user": getpass.getuser(),
            "hostname": os.uname().nodename,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"  # FIXED: uses sys now
        },
        "service": {
            "lynis_installed": lynis_installed,
            "active_scans": len([j for j in scan_jobs.values() if j.status == "running"]),
            "total_scans": len(scan_jobs)
        },
        "storage": {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2)
        }
    })


import re as _re

# ─── Lynis Output Parser ────────────────────────────────────────────────────

# Keyword → severity mapping for intelligent classification
_CRITICAL_KEYWORDS = [
    'root login', 'empty password', 'no password', 'world-writable',
    'SUID root', 'SGID root', 'remote root', 'rootkit', 'backdoor',
    'malware', 'exploit', 'critical', 'CVE-', 'insecure permission on /etc/shadow',
    'PermitRootLogin yes', 'no firewall', 'firewall disabled',
]
_HIGH_KEYWORDS = [
    'ssh', 'password authentication', 'weak cipher', 'MD5', 'DES', 'NULL cipher',
    'outdated', 'unpatched', 'kernel module', 'sudo', 'NOPASSWD',
    'open port', 'listening', 'setuid', 'setgid', 'writable by group',
    'expired', 'no expir', 'umask', '022', '000',
]
_LOW_KEYWORDS = [
    'banner', 'motd', 'legal', 'info', 'log rotation', 'logging',
    'ntp', 'time sync', 'dns', 'nameserver', 'compiler', 'package manager',
    'shell timeout', 'idle', 'auditd',
]

def _strip_ansi(text):
    return _re.sub(r'\x1b\[[0-9;]*m', '', text)

def _classify_severity(text):
    """Classify a finding text into critical/high/medium/low."""
    t = text.lower()
    for kw in _CRITICAL_KEYWORDS:
        if kw.lower() in t:
            return 'critical'
    for kw in _HIGH_KEYWORDS:
        if kw.lower() in t:
            return 'high'
    for kw in _LOW_KEYWORDS:
        if kw.lower() in t:
            return 'low'
    return 'medium'

def _extract_category(text):
    """Try to extract a Lynis test category from the text."""
    cats = ['Authentication', 'Networking', 'File Systems', 'USB', 'Storage',
            'Kernel', 'Memory', 'Processes', 'Logging', 'SSH', 'Firewall',
            'Malware', 'Containers', 'Software', 'Cryptography', 'Compilers']
    t = text.lower()
    for c in cats:
        if c.lower() in t:
            return c
    return 'General'

def parse_lynis_findings(raw_output):
    """
    Parse raw Lynis output and return structured findings dict.
    Returns:
        {
          hardening_index: int|None,
          system_info: {os, kernel, hostname},
          findings: {critical:[], high:[], medium:[], low:[]},
          suggestions: [],
          stats: {warnings: int, suggestions: int}
        }
    """
    lines = raw_output.splitlines()
    findings = {'critical': [], 'high': [], 'medium': [], 'low': []}
    suggestions = []
    hardening_index = None
    sys_info = {}
    seen_warnings = set()
    seen_suggestions = set()

    for raw_line in lines:
        line = _strip_ansi(raw_line.strip())

        # Hardening index
        if 'Hardening index' in line or 'hardening index' in line:
            m = _re.search(r'Hardening\s*index\s*:\s*(\d+)', line, _re.IGNORECASE)
            if m:
                hardening_index = int(m.group(1))

        # System info
        if 'Operating system' in line or 'Linux version' in line:
            m = _re.search(r':\s*(.+)', line)
            if m:
                sys_info.setdefault('os', m.group(1).strip())
        if 'Kernel version' in line or 'kernel version' in line:
            m = _re.search(r':\s*(.+)', line)
            if m:
                sys_info.setdefault('kernel', m.group(1).strip())
        if 'Hostname' in line:
            m = _re.search(r':\s*(.+)', line)
            if m:
                sys_info.setdefault('hostname', m.group(1).strip())

        # Warnings (lines starting with "!" or "  !" in Lynis output)
        if _re.match(r'^\s*!', line):
            txt = _re.sub(r'^\s*!\s*', '', line).strip()
            txt = _re.sub(r'\s+', ' ', txt)
            if txt and len(txt) > 8 and txt not in seen_warnings:
                seen_warnings.add(txt)
                sev = _classify_severity(txt)
                cat = _extract_category(txt)
                findings[sev].append({
                    'message': txt[:300],
                    'severity': sev,
                    'category': cat,
                    'type': 'warning'
                })

        # Suggestions (lines starting with "*" in Lynis output)
        if _re.match(r'^\s*\*', line):
            txt = _re.sub(r'^\s*\*\s*', '', line).strip()
            txt = _re.sub(r'\s+', ' ', txt)
            if txt and len(txt) > 8 and txt not in seen_suggestions:
                seen_suggestions.add(txt)
                sev = _classify_severity(txt)
                cat = _extract_category(txt)
                entry = {
                    'message': txt[:300],
                    'severity': sev,
                    'category': cat,
                    'type': 'suggestion'
                }
                suggestions.append(entry)
                # Also add suggestions to findings by severity
                findings[sev].append(entry)

    total_w = sum(len(v) for v in findings.values())
    return {
        'hardening_index': hardening_index,
        'system_info': sys_info,
        'findings': findings,
        'suggestions': suggestions,
        'stats': {
            'warnings': len(seen_warnings),
            'suggestions': len(seen_suggestions),
            'total_findings': total_w,
        },
        'severity_summary': {k: len(v) for k, v in findings.items()}
    }


# ─── Analysis API Endpoint ──────────────────────────────────────────────────

@app.route('/api/scans/<scan_id>/analysis', methods=['GET'])
def get_scan_analysis(scan_id):
    """Return structured findings analysis for a completed scan."""
    raw_output, metadata = None, {}

    def _find_in_dir(d):
        for fname in ['lynis_raw_output.txt', 'lynis_output.txt']:
            f = d / fname
            if f.exists():
                meta = {}
                mf = d / 'metadata.json'
                if mf.exists():
                    try:
                        meta = json.loads(mf.read_text())
                    except Exception:
                        pass
                try:
                    return f.read_text(errors='replace'), meta
                except Exception:
                    pass
        return None, {}

    # Search root scans/ and subdirs
    for item in SCANS_DIR.iterdir():
        if not item.is_dir():
            continue
        if scan_id in item.name:
            raw_output, metadata = _find_in_dir(item)
            if raw_output:
                break
        for sub in item.iterdir() if item.is_dir() else []:
            if sub.is_dir() and scan_id in sub.name:
                raw_output, metadata = _find_in_dir(sub)
                if raw_output:
                    break
        if raw_output:
            break

    # In-memory fallback
    if not raw_output:
        with scan_lock:
            job = scan_jobs.get(scan_id)
        if job and job.result:
            p = Path(job.result.get('output_file', ''))
            if p.exists():
                try:
                    raw_output = p.read_text(errors='replace')
                    metadata = job.result
                except Exception:
                    pass

    if not raw_output:
        return jsonify({'error': 'Not Found', 'message': f"Scan '{scan_id}' not found."}), 404

    try:
        parsed = parse_lynis_findings(raw_output)
        return jsonify({
            'scan_id': scan_id,
            'timestamp': metadata.get('timestamp', metadata.get('completed_at', '')),
            'command': metadata.get('command', ''),
            'return_code': metadata.get('return_code'),
            **parsed
        })
    except Exception as e:
        logger.error(f"Analysis error for {scan_id}: {e}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


# ─── AI / Explanation Engine ────────────────────────────────────────────────

GEMINI_API_KEY = 'AIzaSyAmXVbSrUVVxd5sw_aPw-AOWfKUKCPdGeo'
# Try newer models in order — flash-lite → flash → pro
_GEMINI_MODELS = [
    'gemini-2.0-flash-lite',
    'gemini-1.5-flash-8b',
    'gemini-1.5-flash',
]
GEMINI_BASE = 'https://generativelanguage.googleapis.com/v1beta/models'

# ── Local knowledge base for offline / quota-exceeded scenarios ──────────────
_LOCAL_KB = [
    {
        'keywords': ['file integrity', 'aide', 'tripwire', 'FINT'],
        'what_it_means': "Your computer doesn't have a program to watch over critical system files. Without this, someone who breaks in can secretly change important files and you'd never know. It's like having no camera in a store — theft can happen unseen.",
        'how_to_fix': [
            'Install a file integrity monitor: sudo apt install aide',
            'Initialize the AIDE database: sudo aideinit',
            'Copy the new database: sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db',
            'Set up a daily check: echo "0 5 * * * root aide --check" | sudo tee /etc/cron.d/aide-check',
        ]
    },
    {
        'keywords': ['root login', 'PermitRootLogin', 'SSH-7408', 'direct root'],
        'what_it_means': "Your SSH server allows the most powerful account (root) to log in directly from the internet. This means hackers can try to guess the root password without any extra barriers. Root has access to everything on your system.",
        'how_to_fix': [
            'Open the SSH config: sudo nano /etc/ssh/sshd_config',
            'Find the line PermitRootLogin and change it to: PermitRootLogin no',
            'Restart SSH: sudo systemctl restart sshd',
            'Make sure you have a normal user account you can SSH into first!',
        ]
    },
    {
        'keywords': ['password authentication', 'PasswordAuthentication', 'SSH-7412'],
        'what_it_means': "SSH is configured to accept passwords. Attackers can run automated tools that guess thousands of passwords per second. Using key-based authentication (like a special digital key) is much safer because keys can't be guessed.",
        'how_to_fix': [
            'Generate an SSH key pair if you don\'t have one: ssh-keygen -t ed25519',
            'Copy your public key to the server: ssh-copy-id user@yourserver',
            'Disable password login: sudo sed -i "s/PasswordAuthentication yes/PasswordAuthentication no/" /etc/ssh/sshd_config',
            'Restart SSH: sudo systemctl restart sshd',
        ]
    },
    {
        'keywords': ['firewall', 'ufw', 'iptables', 'nftables', 'FW-'],
        'what_it_means': "Your system has no active firewall. A firewall is like a security guard at the door — it controls which connections are allowed in and out. Without it, any service running on your machine could be reached by anyone on the internet.",
        'how_to_fix': [
            'Install and enable UFW (the simplest Linux firewall): sudo apt install ufw',
            'Set default rules: sudo ufw default deny incoming && sudo ufw default allow outgoing',
            'Allow SSH so you don\'t lock yourself out: sudo ufw allow ssh',
            'Enable the firewall: sudo ufw enable',
        ]
    },
    {
        'keywords': ['sudo', 'NOPASSWD', 'AUTH-9262', 'sudoers'],
        'what_it_means': "One or more user accounts can run administrator commands without being asked for a password. This means if someone gains access to that account (even briefly), they can immediately take full control of the entire system.",
        'how_to_fix': [
            'Review the sudoers file: sudo visudo',
            'Look for lines with NOPASSWD and remove or restrict them',
            'Check /etc/sudoers.d/ for extra configs: ls -la /etc/sudoers.d/',
            'Only keep NOPASSWD for automated services that truly require it, document why',
        ]
    },
    {
        'keywords': ['umask', 'SHLL-6230', 'umask 002', 'umask 000'],
        'what_it_means': "The system's file permission default (umask) is too permissive. This means every new file created on the system might accidentally be readable or writable by other users. It's like leaving your documents in a public folder by default.",
        'how_to_fix': [
            'Check current umask: umask',
            'Set a stricter default in /etc/profile or /etc/bash.bashrc: umask 027',
            'Also set it in /etc/login.defs: find the line UMASK and set it to 027',
            'Apply immediately: echo "umask 027" | sudo tee -a /etc/profile',
        ]
    },
    {
        'keywords': ['world-writable', 'world writable', 'FILE-6374'],
        'what_it_means': "Some files or directories on your system can be written to by any user — even untrusted ones. This is a major security risk because malicious programs or users can modify these files, potentially replacing legitimate programs with dangerous ones.",
        'how_to_fix': [
            'Find world-writable files: find / -perm -002 -type f -not -path "/proc/*" 2>/dev/null',
            'For each file found, remove the world-write permission: chmod o-w /path/to/file',
            'For directories, add the sticky bit to allow deletion only by owner: chmod +t /path/to/dir',
        ]
    },
    {
        'keywords': ['suid', 'SGID', 'setuid', 'setgid', 'FILE-7'],
        'what_it_means': "Some programs on your system have special elevated permissions (SUID/SGID). While some programs need this legitimately, unnecessary SUID files are a common way attackers gain administrator access. It's like giving a regular employee a master key to the building.",
        'how_to_fix': [
            'List all SUID files: find / -perm /4000 -type f 2>/dev/null',
            'List all SGID files: find / -perm /2000 -type f 2>/dev/null',
            'For any unexpected file: sudo chmod u-s /path/to/file',
            'Research each file before removing SUID — some (like ping, passwd) legitimately need it',
        ]
    },
    {
        'keywords': ['ssh protocol', 'SSH-7402', 'protocol 1'],
        'what_it_means': "An outdated SSH protocol version is in use. SSH Protocol 1 has serious known security vulnerabilities that allow attackers to intercept and hijack your encrypted connections. Protocol 2 is the modern, secure version.",
        'how_to_fix': [
            'Edit the SSH config: sudo nano /etc/ssh/sshd_config',
            'Ensure only Protocol 2 is used: add or update the line: Protocol 2',
            'Also set: KexAlgorithms curve25519-sha256,diffie-hellman-group-exchange-sha256',
            'Restart SSH: sudo systemctl restart sshd',
        ]
    },
    {
        'keywords': ['updates', 'upgrade', 'package', 'unpatched', 'outdated', 'PKGS-'],
        'what_it_means': "Your system has software packages that need updates. Many of these updates contain security patches for known vulnerabilities. Running old software is like leaving known holes in your wall — attackers know where they are and how to use them.",
        'how_to_fix': [
            'Update package list: sudo apt update',
            'Install all available updates: sudo apt upgrade -y',
            'Also update installed applications: sudo apt full-upgrade -y',
            'Set up automatic security updates: sudo apt install unattended-upgrades && sudo dpkg-reconfigure unattended-upgrades',
        ]
    },
    {
        'keywords': ['ntp', 'time sync', 'TIME-', 'chrony', 'clock'],
        'what_it_means': "Your system's clock is not being synchronized with the internet. An incorrect clock can cause security certificates to fail, log files to have wrong timestamps (making incident investigations impossible), and authentication tokens to reject valid logins.",
        'how_to_fix': [
            'Install chrony (recommended NTP client): sudo apt install chrony',
            'Enable and start it: sudo systemctl enable --now chrony',
            'Verify sync: chronyc tracking',
            'Alternatively use systemd-timesyncd: sudo timedatectl set-ntp true',
        ]
    },
    {
        'keywords': ['auditd', 'audit daemon', 'ACCT-9628', 'logging'],
        'what_it_means': "The system audit daemon (auditd) is not running. This daemon records security-relevant events like who logged in, who ran what commands, and what files were accessed. Without it, you have no record of suspicious activity.",
        'how_to_fix': [
            'Install auditd: sudo apt install auditd',
            'Enable and start it: sudo systemctl enable --now auditd',
            'View audit logs: sudo ausearch -ts today',
            'Add rules for important files: sudo auditctl -w /etc/passwd -p wa -k passwd_changes',
        ]
    },
    {
        'keywords': ['compiler', 'gcc', 'development', 'HRDN-7222'],
        'what_it_means': "Compiler tools are installed on the server. Servers typically don't need to compile code. If an attacker gains access, they can use compilers to build malicious tools directly on your machine, making it much easier to escalate their attack.",
        'how_to_fix': [
            'Check if compilers are needed: dpkg -l | grep -E "gcc|build-essential"',
            'If not needed, remove them: sudo apt remove gcc build-essential --autoremove',
            'If needed for a specific user only, restrict access: sudo chmod o-x /usr/bin/gcc',
        ]
    },
    {
        'keywords': ['banner', 'motd', 'SSH-7440', 'legal notice'],
        'what_it_means': "Your SSH server is missing a legal warning banner. While this seems minor, a login banner is legally important — it notifies users that the system is monitored. Without it, unauthorized access attempts may be harder to prosecute legally.",
        'how_to_fix': [
            'Create a banner file: sudo nano /etc/ssh/banner',
            'Add text like: "Authorized access only. This system is monitored. All activity may be recorded."',
            'Configure SSH to show it: echo "Banner /etc/ssh/banner" | sudo tee -a /etc/ssh/sshd_config',
            'Restart SSH: sudo systemctl restart sshd',
        ]
    },
    {
        'keywords': ['empty password', 'blank password', 'AUTH-9', 'no password'],
        'what_it_means': "One or more user accounts have no password set. This means anyone who knows that username can log in without any authentication. This is a critical vulnerability — any user on your network or internet could gain access.",
        'how_to_fix': [
            'Find accounts with empty passwords: sudo awk -F: \'($2 == "") {print $1}\' /etc/shadow',
            'Set a strong password for each: sudo passwd username',
            'Lock accounts that should not be active: sudo passwd -l username',
            'Disable login for system accounts: sudo usermod -s /sbin/nologin username',
        ]
    },
]

def _local_explain(finding_message, severity, category):
    """Match the finding to our local knowledge base and return a formatted explanation."""
    msg_lower = finding_message.lower()
    best_match = None
    best_score = 0

    for entry in _LOCAL_KB:
        score = sum(1 for kw in entry['keywords'] if kw.lower() in msg_lower)
        if score > best_score:
            best_score = score
            best_match = entry

    if best_match and best_score > 0:
        return {
            'what_it_means': best_match['what_it_means'],
            'how_to_fix': best_match['how_to_fix'],
            'source': 'local'
        }

    # Generic fallback by severity
    sev_generic = {
        'critical': {
            'what_it_means': f"This is a CRITICAL security issue in the {category} area of your system. It represents a serious vulnerability that attackers commonly exploit to gain unauthorized access or control.",
            'how_to_fix': [
                'Address this immediately — do not delay',
                f'Search for "{finding_message[:60]}" in Lynis documentation: https://cisofy.com/lynis/',
                'Consult your system administrator before making changes',
                'After fixing, re-run the security scan to verify the issue is resolved',
            ]
        },
        'high': {
            'what_it_means': f"This is a HIGH priority security issue in the {category} area. While not immediately catastrophic, attackers can use this as a stepping stone to gain deeper access to your system.",
            'how_to_fix': [
                f'Research this specific finding: "{finding_message[:60]}"',
                'Check Lynis documentation: https://cisofy.com/lynis/',
                'Plan to fix this within the next week',
                'Re-run the scan after applying any fixes',
            ]
        },
        'medium': {
            'what_it_means': f"This is a medium-priority security recommendation for the {category} area. Fixing this will improve your system's overall security posture and reduce attack surface.",
            'how_to_fix': [
                f'Look up this finding in Lynis docs: https://cisofy.com/lynis/',
                'Plan to address this in your next maintenance window',
                'Consider enabling automatic security hardening for this category',
            ]
        },
        'low': {
            'what_it_means': f"This is a low-priority security improvement suggestion for the {category} area. While not urgent, addressing it contributes to better security hygiene.",
            'how_to_fix': [
                'This is a best-practice recommendation',
                f'Look up the specific test in Lynis documentation: https://cisofy.com/lynis/',
                'Address during regular maintenance',
            ]
        },
    }
    fallback = sev_generic.get(severity, sev_generic['medium'])
    return {**fallback, 'source': 'local'}


def _try_gemini(finding_message, severity, category):
    """Try Gemini API models in order. Returns parsed dict or None."""
    import urllib.request as _urlreq

    prompt = (
        f"You are a Linux security expert helping a NON-TECHNICAL person understand a security audit finding.\n\n"
        f"Finding: {finding_message}\nSeverity: {severity.upper()}\nCategory: {category}\n\n"
        f"Provide:\n"
        f"1. \"what_it_means\": 2-3 sentences in simple everyday language explaining the risk and why it matters.\n"
        f"2. \"how_to_fix\": A list of 2-4 specific, actionable steps with exact Linux commands.\n\n"
        f"Respond ONLY with valid JSON. Keys: \"what_it_means\" (string) and \"how_to_fix\" (list of strings)."
    )
    body = json.dumps({
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 600}
    }).encode('utf-8')

    for model in _GEMINI_MODELS:
        url = f'{GEMINI_BASE}/{model}:generateContent?key={GEMINI_API_KEY}'
        req = _urlreq.Request(url, data=body,
                              headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with _urlreq.urlopen(req, timeout=12) as resp:
                if resp.status != 200:
                    continue
                raw = json.loads(resp.read().decode())
            text = raw['candidates'][0]['content']['parts'][0]['text'].strip()
            if text.startswith('```'):
                text = text.split('\n', 1)[1].rsplit('```', 1)[0].strip()
            result = json.loads(text)
            result['source'] = 'gemini'
            return result
        except Exception as e:
            logger.debug(f'Gemini model {model} failed: {e}')
            continue
    return None


def _get_ai_explanation(finding_message, severity, category):
    """Get an explanation — tries Gemini first, falls back to local KB."""
    result = _try_gemini(finding_message, severity, category)
    if result:
        return result
    return _local_explain(finding_message, severity, category)


@app.route('/api/scans/<scan_id>/explain', methods=['POST'])
def explain_finding(scan_id):
    """Get AI/local explanation for a specific finding (used by Analysis view)."""
    data = request.get_json() or {}
    message = data.get('message', '')
    severity = data.get('severity', 'medium')
    category = data.get('category', 'General')

    if not message:
        return jsonify({'error': 'No finding message provided'}), 400

    result = _get_ai_explanation(message, severity, category)
    return jsonify(result)


# ─── PDF Builder ────────────────────────────────────────────────────────────

def _build_pdf(scan_id, raw_output, metadata):
    """Build a professional PDF report with Critical/High/Medium/Low sections."""
    parsed = parse_lynis_findings(raw_output)
    findings = parsed['findings']
    severity_summary = parsed['severity_summary']
    hardening_index = parsed['hardening_index']
    sys_info = parsed['system_info']

    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            rightMargin=54, leftMargin=54,
                            topMargin=54, bottomMargin=54)

    styles = getSampleStyleSheet()
    normal = styles['Normal']

    title_style   = ParagraphStyle('PdfTitle', parent=styles['Heading1'],
                                   fontSize=24, alignment=TA_CENTER,
                                   textColor=colors.HexColor('#0F172A'), spaceAfter=4)
    sub_style     = ParagraphStyle('PdfSub', parent=styles['Normal'],
                                   fontSize=10, alignment=TA_CENTER,
                                   textColor=colors.HexColor('#64748B'), spaceAfter=20)
    sec_style     = ParagraphStyle('PdfSec', parent=styles['Heading2'],
                                   fontSize=13, spaceBefore=18, spaceAfter=8,
                                   textColor=colors.HexColor('#0F172A'))
    badge_style   = ParagraphStyle('PdfBadge', parent=styles['Normal'],
                                   fontSize=10, fontName='Helvetica-Bold',
                                   alignment=TA_CENTER)
    msg_style     = ParagraphStyle('PdfMsg', parent=styles['Normal'],
                                   fontSize=9, leading=13)
    cat_style     = ParagraphStyle('PdfCat', parent=styles['Normal'],
                                   fontSize=8, textColor=colors.HexColor('#64748B'))

    SEV = {
        'critical': {
            'color':  colors.HexColor('#DC2626'),
            'bg':     colors.HexColor('#FEF2F2'),
            'header': colors.HexColor('#DC2626'),
            'label':  'CRITICAL',
        },
        'high': {
            'color':  colors.HexColor('#EA580C'),
            'bg':     colors.HexColor('#FFF7ED'),
            'header': colors.HexColor('#EA580C'),
            'label':  'HIGH',
        },
        'medium': {
            'color':  colors.HexColor('#D97706'),
            'bg':     colors.HexColor('#FFFBEB'),
            'header': colors.HexColor('#D97706'),
            'label':  'MEDIUM',
        },
        'low': {
            'color':  colors.HexColor('#0891B2'),
            'bg':     colors.HexColor('#F0F9FF'),
            'header': colors.HexColor('#0891B2'),
            'label':  'LOW',
        },
    }

    story = []

    # ── Cover / Title ──────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph('🛡 Linux Security Audit Report', title_style))
    ts = metadata.get('timestamp', metadata.get('completed_at', ''))
    if ts:
        try:
            ts = datetime.fromisoformat(ts).strftime('%B %d, %Y  %I:%M %p')
        except Exception:
            pass
    story.append(Paragraph(f'Scan ID: {scan_id}  ·  {ts}', sub_style))

    # Horizontal rule
    story.append(Table([['']], colWidths=[6.5*inch],
                        style=TableStyle([('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor('#E2E8F0'))])))
    story.append(Spacer(1, 0.15*inch))

    # ── Hardening Score banner ──────────────────────────────────────────────
    hi = hardening_index if hardening_index is not None else '?'
    if isinstance(hi, int):
        score_color = (colors.HexColor('#DC2626') if hi < 40 else
                       colors.HexColor('#D97706') if hi < 60 else
                       colors.HexColor('#16A34A'))
        score_label = 'Poor' if hi < 40 else 'Fair' if hi < 60 else 'Good' if hi < 80 else 'Excellent'
    else:
        score_color = colors.HexColor('#64748B')
        score_label = 'Unknown'

    score_tbl = Table([[
        Paragraph(f'<b>{hi}/100</b>', ParagraphStyle('Score', parent=normal, fontSize=28,
                  fontName='Helvetica-Bold', textColor=score_color, alignment=TA_CENTER)),
        Paragraph(f'<b>Hardening Score</b><br/>{score_label}',
                  ParagraphStyle('ScoreLbl', parent=normal, fontSize=13,
                  textColor=score_color)),
    ]], colWidths=[1.5*inch, 3*inch])
    score_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(score_tbl)
    story.append(Spacer(1, 0.15*inch))

    # ── Severity Summary row ────────────────────────────────────────────────
    sev_row = []
    for sev_key in ['critical', 'high', 'medium', 'low']:
        cnt = severity_summary.get(sev_key, 0)
        s = SEV[sev_key]
        cell = Paragraph(
            f'<b>{cnt}</b><br/>{s["label"]}',
            ParagraphStyle(f'SevCell{sev_key}', parent=normal, fontSize=12,
                           fontName='Helvetica-Bold', alignment=TA_CENTER,
                           textColor=s['color'])
        )
        sev_row.append(cell)

    sev_tbl = Table([sev_row], colWidths=[1.6*inch]*4)
    sev_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#FEF2F2')),
        ('BACKGROUND', (1,0), (1,-1), colors.HexColor('#FFF7ED')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#FFFBEB')),
        ('BACKGROUND', (3,0), (3,-1), colors.HexColor('#F0F9FF')),
        ('BOX', (0,0), (0,-1), 1.5, colors.HexColor('#DC2626')),
        ('BOX', (1,0), (1,-1), 1.5, colors.HexColor('#EA580C')),
        ('BOX', (2,0), (2,-1), 1.5, colors.HexColor('#D97706')),
        ('BOX', (3,0), (3,-1), 1.5, colors.HexColor('#0891B2')),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('COLPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(sev_tbl)
    story.append(Spacer(1, 0.2*inch))

    # ── System Info ─────────────────────────────────────────────────────────
    si_data = [['Property', 'Value'],
               ['OS', sys_info.get('os', 'Unknown')],
               ['Kernel', sys_info.get('kernel', 'Unknown')],
               ['Hostname', sys_info.get('hostname', 'Unknown')],
               ['Command', metadata.get('command', 'sudo lynis audit system')],
               ['Return Code', str(metadata.get('return_code', 'N/A'))]]
    si_tbl = Table(si_data, colWidths=[1.5*inch, 5*inch])
    si_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(Paragraph('System Information', sec_style))
    story.append(si_tbl)

    # ── Severity Sections ───────────────────────────────────────────────────
    ai_style = ParagraphStyle('AiBox', parent=normal, fontSize=8.5,
                               leading=12, textColor=colors.HexColor('#1E293B'))
    ai_label_style = ParagraphStyle('AiLabel', parent=normal, fontSize=8,
                                     fontName='Helvetica-Bold',
                                     textColor=colors.HexColor('#0F172A'))
    fix_step_style = ParagraphStyle('FixStep', parent=normal, fontSize=8.5,
                                     leading=12, leftIndent=12,
                                     textColor=colors.HexColor('#166534'))

    def _render_severity_section(sev_key, items):
        if not items:
            return
        s = SEV[sev_key]
        story.append(PageBreak())

        # Section header band
        hdr_tbl = Table([[
            Paragraph(f'<b>{s["label"]} Priority Findings ({len(items)})</b>',
                      ParagraphStyle(f'Hdr{sev_key}', parent=normal, fontSize=14,
                                     fontName='Helvetica-Bold', textColor=colors.white))
        ]], colWidths=[6.5*inch])
        hdr_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), s['header']),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(hdr_tbl)
        story.append(Spacer(1, 0.1*inch))

        # Use AI for top 5 critical/high, top 3 medium, none for low
        ai_limit = 5 if sev_key == 'critical' else 3 if sev_key == 'high' else 2 if sev_key == 'medium' else 0

        for i, item in enumerate(items[:60], 1):
            msg = item.get('message', '')
            cat = item.get('category', 'General')
            itype = item.get('type', 'finding')

            # Build content cells
            content_paras = [Paragraph(msg, msg_style),
                             Paragraph(f'Category: {cat}  ·  Type: {itype}', cat_style)]

            # Fetch AI explanation for top N findings
            if i <= ai_limit:
                ai_data = _get_ai_explanation(msg, sev_key, cat)
                if ai_data:
                    what = ai_data.get('what_it_means', '')
                    fixes = ai_data.get('how_to_fix', [])
                    if isinstance(fixes, str):
                        fixes = [fixes]

                    content_paras.append(Spacer(1, 0.04*inch))

                    # "What this means" box
                    ai_box = Table([[
                        [Paragraph('🔍 What this means:', ai_label_style),
                         Paragraph(what, ai_style)]
                    ]], colWidths=[6.0*inch])
                    ai_box.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
                        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                        ('TOPPADDING', (0,0), (-1,-1), 5),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                        ('LEFTPADDING', (0,0), (-1,-1), 8),
                    ]))
                    content_paras.append(ai_box)

                    # "How to fix" box
                    if fixes:
                        fix_items = [Paragraph('🔧 How to fix it:', ai_label_style)]
                        for step_num, step in enumerate(fixes, 1):
                            fix_items.append(Paragraph(f'{step_num}. {step}', fix_step_style))
                        fix_box = Table([[fix_items]], colWidths=[6.0*inch])
                        fix_box.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F0FDF4')),
                            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#86EFAC')),
                            ('TOPPADDING', (0,0), (-1,-1), 5),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                            ('LEFTPADDING', (0,0), (-1,-1), 8),
                        ]))
                        content_paras.append(Spacer(1, 0.02*inch))
                        content_paras.append(fix_box)

            row = [[
                Paragraph(f'<b>#{i}</b>', ParagraphStyle('Idx', parent=normal,
                          fontSize=9, alignment=TA_CENTER)),
                Paragraph(f'<b>{s["label"]}</b>',
                          ParagraphStyle(f'Sev{sev_key}', parent=badge_style,
                                         textColor=s['color'])),
                content_paras,
            ]]
            card = Table(row, colWidths=[0.4*inch, 0.75*inch, 5.35*inch])
            card.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), s['bg']),
                ('BOX',        (0,0), (-1,-1), 0.75, s['color']),
                ('LINEAFTER',  (0,0), (0,-1),  1,    s['color']),
                ('TOPPADDING',    (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING',   (0,0), (-1,-1), 6),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            story.append(KeepTogether(card))
            story.append(Spacer(1, 0.05*inch))

    for sev_key in ['critical', 'high', 'medium', 'low']:
        _render_severity_section(sev_key, findings.get(sev_key, []))

    # ── Footer ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.4*inch))
    story.append(Table([['']], colWidths=[6.5*inch],
                        style=TableStyle([('LINEABOVE', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0'))])))
    story.append(Paragraph(
        f'<i>Linux Security Audit Tool  ·  Report generated {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</i>',
        ParagraphStyle('Footer', parent=normal, fontSize=8,
                       textColor=colors.HexColor('#94A3B8'), alignment=TA_CENTER)
    ))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes



@app.route('/api/scans/<scan_id>/pdf', methods=['GET'])
def generate_pdf_report(scan_id):
    """Generate and download a PDF report for a completed scan."""
    if not REPORTLAB_AVAILABLE:
        return jsonify({
            "error": "Service Unavailable",
            "message": "PDF generation requires reportlab. Run: pip install reportlab"
        }), 503

    # Search all scan directories (root + subdirs)
    raw_output = None
    metadata = {}

    def _find_in_dir(d):
        """Return (raw_output, metadata) if scan found in directory d, else (None, {})."""
        for fname in ["lynis_raw_output.txt", "lynis_output.txt"]:
            out_f = d / fname
            if out_f.exists():
                meta_f = d / "metadata.json"
                meta = {}
                if meta_f.exists():
                    try:
                        with open(meta_f, 'r') as f:
                            meta = json.load(f)
                    except Exception:
                        pass
                try:
                    with open(out_f, 'r', errors='replace') as f:
                        return f.read(), meta
                except Exception:
                    pass
        return None, {}

    # 1. Search root scans/ dir and its immediate scan subdirectories
    for item in SCANS_DIR.iterdir():
        if not item.is_dir():
            continue
        if scan_id in item.name:
            raw_output, metadata = _find_in_dir(item)
            if raw_output:
                break
        # Also check one level deeper (e.g. scans/completed/<dir>)
        if item.is_dir():
            for sub in item.iterdir():
                if sub.is_dir() and scan_id in sub.name:
                    raw_output, metadata = _find_in_dir(sub)
                    if raw_output:
                        break
        if raw_output:
            break

    # 2. Check in-memory result (for scans done this session before server restart)
    if not raw_output:
        with scan_lock:
            job = scan_jobs.get(scan_id)
        if job and job.result:
            out_path = job.result.get('output_file')
            if out_path:
                p = Path(out_path)
                if p.exists():
                    try:
                        with open(p, 'r', errors='replace') as f:
                            raw_output = f.read()
                        metadata = job.result
                    except Exception:
                        pass

    if not raw_output:
        return jsonify({
            "error": "Not Found",
            "message": f"Scan '{scan_id}' not found or has no output file."
        }), 404

    try:
        pdf_bytes = _build_pdf(scan_id, raw_output, metadata)
        resp = Response(pdf_bytes, mimetype='application/pdf')
        resp.headers['Content-Disposition'] = f'attachment; filename=security_audit_{scan_id}.pdf'
        return resp
    except Exception as e:
        logger.error(f"PDF generation error for {scan_id}: {e}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": f"PDF generation failed: {e}"
        }), 500


if __name__ == '__main__':

    print("\n" + "="*60)
    print("Linux Security Audit Tool - COMPLETE API (FIXED)")
    print("="*60)
    print("Server running on: http://0.0.0.0:5000")
    print("\nFeatures:")
    print("  • Start Lynis security scans")
    print("  • Monitor scan progress")
    print("  • View scan results")
    print("  • Download raw output")
    print("  • Scan history")
    print("  • System status")
    print("\nPrerequisites:")
    print("  • Lynis installed: sudo apt install lynis")
    print("  • Sudo access for full audit")
    print("\nPress Ctrl+C to stop")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
