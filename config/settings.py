"""
Configuration settings for the Linux Security Audit Tool.
Extended for Phase 2 API.
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Directory paths
SCANS_DIR = PROJECT_ROOT / "scans"
PENDING_SCANS_DIR = SCANS_DIR / "pending"
COMPLETED_SCANS_DIR = SCANS_DIR / "completed"
ARCHIVED_SCANS_DIR = SCANS_DIR / "archived"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
for directory in [SCANS_DIR, PENDING_SCANS_DIR, COMPLETED_SCANS_DIR, 
                  ARCHIVED_SCANS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Lynis configuration
LYNIS_COMMAND = "lynis"
LYNIS_ARGS = ["audit", "system", "--quick"]  # --quick for faster scans
LYNIS_TIMEOUT = 1800  # 30 minutes timeout for safety

# Sudo configuration
USE_SUDO = True  # Lynis typically requires sudo for full audit
SUDO_COMMAND = "sudo"
SUDO_PASSWORD_PROMPT = "[sudo] password for"

# Scan configuration
MAX_CONCURRENT_SCANS = 1  # Only one scan at a time for Phase 2
SCAN_HISTORY_LIMIT = 100  # Maximum number of scans to keep

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_DIR / "audit_tool.log"
API_LOG_FILE = LOGS_DIR / "api.log"

# API Configuration
API_HOST = "0.0.0.0"  # Bind to all interfaces
API_PORT = 5000
API_DEBUG = True  # Set to False in production
API_THREADED = True

# Security configuration
ALLOWED_USERS = []  # Empty means any user can run (for Phase 1)
MIN_PYTHON_VERSION = (3, 8)

# Background job configuration
MAX_JOBS_IN_MEMORY = 100  # Maximum number of jobs to keep in memory
JOB_CLEANUP_INTERVAL = 300  # Clean up old jobs every 5 minutes (seconds)
