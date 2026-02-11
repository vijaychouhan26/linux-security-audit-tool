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
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import logging

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
    """Get results of a completed scan."""
    # Check in-memory jobs
    with scan_lock:
        job = scan_jobs.get(scan_id)
    
    if job and job.status == "completed" and job.result:
        return jsonify(job.result)
    
    # Check filesystem
    for item in SCANS_DIR.iterdir():
        if item.is_dir() and scan_id in item.name:
            metadata_file = item / "metadata.json"
            output_file = item / "lynis_output.txt"
            
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    result = {
                        "scan_id": scan_id,
                        "status": "completed",
                        "from_history": True,
                        **metadata
                    }
                    
                    # Add preview of output
                    if output_file.exists():
                        with open(output_file, 'r') as f:
                            content = f.read()
                        result["output_preview"] = content[:1000] + "..." if len(content) > 1000 else content
                        result["output_size"] = len(content)
                        result["raw_output_url"] = f"/api/scans/{scan_id}/raw"
                    
                    return jsonify(result)
                except Exception as e:
                    return jsonify({"error": f"Failed to read results: {e}"}), 500
    
    return jsonify({"error": "Results not found or scan not complete"}), 404

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
