"""
Scan service for managing background scan execution.
Uses threading for simple background processing.
"""

import threading
import uuid
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from queue import Queue
import traceback

from src.core.scanner import LynisScanner
from config import settings

logger = logging.getLogger(__name__)


class ScanJob:
    """Represents a single scan job with status tracking."""
    
    def __init__(self, scan_id: str):
        self.scan_id = scan_id
        self.status = "pending"  # pending, running, completed, failed, cancelled
        self.progress = 0  # 0-100 percentage
        self.current_phase = "Initializing"
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.thread: Optional[threading.Thread] = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for JSON serialization."""
        return {
            "scan_id": self.scan_id,
            "status": self.status,
            "progress": self.progress,
            "current_phase": self.current_phase,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "has_result": self.result is not None,
            "error_message": self.error_message,
            "estimated_time_remaining": self._estimate_time_remaining()
        }
    
    def _estimate_time_remaining(self) -> Optional[int]:
        """Estimate time remaining in seconds (very rough estimate)."""
        if self.status != "running":
            return None
        
        # Lynis scans typically take 2-10 minutes
        # We'll use a simple linear progress estimate
        if self.progress <= 0:
            return 300  # 5 minutes default
        
        elapsed = (datetime.now() - self.started_at).total_seconds()
        if elapsed <= 0:
            return 300
        
        total_estimated = elapsed / (self.progress / 100)
        remaining = total_estimated - elapsed
        return max(0, int(remaining))


class ScanService:
    """
    Service for managing background scan execution.
    Thread-safe for multiple API requests.
    """
    
    def __init__(self):
        self._jobs: Dict[str, ScanJob] = {}
        self._lock = threading.Lock()
        self._scanner = LynisScanner()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._periodic_cleanup,
            daemon=True,
            name="ScanServiceCleanup"
        )
        self._cleanup_thread.start()
        
        logger.info("ScanService initialized")
    
    def _periodic_cleanup(self) -> None:
        """Periodically clean up old/completed jobs."""
        while True:
            time.sleep(300)  # Run every 5 minutes
            try:
                self._cleanup_old_jobs()
            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")
    
    def _cleanup_old_jobs(self) -> None:
        """Remove old completed/failed jobs to prevent memory bloat."""
        with self._lock:
            now = datetime.now()
            jobs_to_remove = []
            
            for job_id, job in self._jobs.items():
                if job.status in ["completed", "failed", "cancelled"]:
                    # Remove jobs older than 24 hours
                    if job.completed_at and (now - job.completed_at).total_seconds() > 86400:
                        jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self._jobs[job_id]
                logger.info(f"Cleaned up old job: {job_id}")
    
    def create_scan_job(self) -> ScanJob:
        """Create a new scan job and return it."""
        scan_id = f"api_scan_{uuid.uuid4().hex[:8]}"
        job = ScanJob(scan_id)
        
        with self._lock:
            self._jobs[scan_id] = job
        
        logger.info(f"Created new scan job: {scan_id}")
        return job
    
    def _run_scan_thread(self, job: ScanJob) -> None:
        """Thread function to execute the scan."""
        try:
            job.status = "running"
            job.started_at = datetime.now()
            job.current_phase = "Initializing environment"
            job.progress = 10
            logger.info(f"Starting scan execution for job: {job.scan_id}")
            
            # Phase 1: Environment check
            job.current_phase = "Checking system environment"
            job.progress = 20
            
            # Phase 2: Running Lynis
            job.current_phase = "Executing Lynis security audit"
            job.progress = 40
            
            # Actually run the scan
            result = self._scanner.run_scan()
            
            # Update with results
            job.current_phase = "Processing scan results"
            job.progress = 80
            
            job.result = result
            job.status = "completed"
            job.progress = 100
            job.completed_at = datetime.now()
            
            logger.info(f"Scan completed successfully: {job.scan_id}")
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Scan failed for job {job.scan_id}: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
    
    def start_scan(self, job: ScanJob) -> bool:
        """
        Start a scan in the background.
        
        Returns:
            True if scan started successfully
        """
        if job.status != "pending":
            logger.warning(f"Cannot start job {job.scan_id} with status: {job.status}")
            return False
        
        try:
            # Create and start thread
            thread = threading.Thread(
                target=self._run_scan_thread,
                args=(job,),
                daemon=True,
                name=f"ScanThread-{job.scan_id}"
            )
            
            job.thread = thread
            thread.start()
            
            logger.info(f"Started background scan thread for job: {job.scan_id}")
            return True
            
        except Exception as e:
            job.status = "failed"
            job.error_message = f"Failed to start scan thread: {e}"
            logger.error(f"Failed to start scan thread for job {job.scan_id}: {e}")
            return False
    
    def get_job(self, scan_id: str) -> Optional[ScanJob]:
        """Get a scan job by ID."""
        with self._lock:
            return self._jobs.get(scan_id)
    
    def get_job_status(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get job status as dictionary."""
        job = self.get_job(scan_id)
        if job:
            return job.to_dict()
        return None
    
    def get_job_result(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get full job result if available."""
        job = self.get_job(scan_id)
        if job and job.status == "completed" and job.result:
            result = job.result.copy()
            result.update(job.to_dict())
            return result
        return None
    
    def cancel_job(self, scan_id: str) -> bool:
        """Cancel a running job."""
        job = self.get_job(scan_id)
        if not job:
            return False
        
        if job.status == "running" and job.thread:
            # Try to cancel the scanner
            if self._scanner.cancel_scan():
                job.status = "cancelled"
                job.completed_at = datetime.now()
                job.error_message = "Scan cancelled by user"
                logger.info(f"Cancelled scan job: {scan_id}")
                return True
        
        return False
    
    def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all jobs (most recent first)."""
        with self._lock:
            jobs = list(self._jobs.values())
        
        # Sort by creation time (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        # Apply limit
        jobs = jobs[:limit]
        
        return [job.to_dict() for job in jobs]
    
    def get_scan_history(self) -> List[Dict[str, Any]]:
        """
        Get scan history from completed scans directory.
        This reads from the file system, not from in-memory jobs.
        """
        from src.utils.file_handler import FileHandler
        
        try:
            file_handler = FileHandler(settings.SCANS_DIR)
            scans = file_handler.get_scan_list("completed")
            
            # Add additional metadata for API response
            for scan in scans:
                scan_id = scan.get('scan_id', 'unknown')
                scan['api_endpoint'] = f"/api/scans/{scan_id}/results"
                scan['raw_output_url'] = f"/api/scans/{scan_id}/raw"
                
                # Check if output file exists and get its size
                output_file = scan.get('output_file')
                if output_file and Path(output_file).exists():
                    scan['output_size'] = Path(output_file).stat().st_size
                else:
                    scan['output_size'] = 0
            
            return scans
            
        except Exception as e:
            logger.error(f"Error getting scan history: {e}")
            return []


# Global instance for API to use
scan_service = ScanService()
