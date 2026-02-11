"""
Core Lynis scanner implementation.
Handles execution, timeout, and result capture.
"""

import subprocess
import uuid
import signal
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List  # Added List import
import logging
import tempfile

# Use absolute imports for better reliability
from src.utils.security import privilege_manager, SecurityError
from src.utils.file_handler import FileHandler
from config import settings

logger = logging.getLogger(__name__)


class LynisScanner:
    """Main scanner class for executing Lynis audits."""
    
    def __init__(self):
        self.file_handler = FileHandler(settings.SCANS_DIR)
        self.current_scan_id = None
        self.current_scan_dir = None
        self.scan_process = None
        
    def _generate_scan_id(self) -> str:
        """Generate a unique scan ID."""
        return f"scan_{uuid.uuid4().hex[:8]}"
    
    def _validate_lynis_installed(self) -> bool:
        """
        Check if Lynis is installed and accessible.
        
        Returns:
            True if Lynis is available
            
        Raises:
            RuntimeError: If Lynis is not installed
        """
        try:
            # First check without sudo
            result = subprocess.run(
                ["which", settings.LYNIS_COMMAND],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info(f"Lynis found at: {result.stdout.strip()}")
                return True
            
            # If not found, check with sudo (if enabled)
            if settings.USE_SUDO:
                sudo_check = [settings.SUDO_COMMAND, "which", settings.LYNIS_COMMAND]
                result = subprocess.run(
                    sudo_check,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    logger.info(f"Lynis found (with sudo): {result.stdout.strip()}")
                    return True
            
            logger.error("Lynis not found in PATH")
            return False
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout checking for Lynis installation")
            return False
        except Exception as e:
            logger.error(f"Error checking Lynis installation: {e}")
            return False
    
    def _prepare_scan(self) -> Tuple[str, Path]:
        """
        Prepare for a new scan.
        
        Returns:
            Tuple of (scan_id, scan_directory)
            
        Raises:
            RuntimeError: If preparation fails
        """
        # Generate unique scan ID
        scan_id = self._generate_scan_id()
        logger.info(f"Preparing scan: {scan_id}")
        
        # Create scan directory
        try:
            scan_dir = self.file_handler.create_scan_directory(scan_id)
        except Exception as e:
            raise RuntimeError(f"Failed to create scan directory: {e}")
        
        # Prepare metadata
        metadata = {
            'scan_id': scan_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending',
            'directory': str(scan_dir),
            'lynis_command': settings.LYNIS_COMMAND,
            'lynis_args': settings.LYNIS_ARGS,
            'use_sudo': settings.USE_SUDO
        }
        
        # Save metadata
        try:
            self.file_handler.save_metadata(scan_dir, metadata)
        except Exception as e:
            logger.warning(f"Could not save metadata: {e}")
            # Continue even if metadata fails
        
        return scan_id, scan_dir
    
    def _execute_lynis(self, scan_dir: Path) -> Tuple[int, str, str]:
        """
        Execute Lynis command and capture output.
        
        Args:
            scan_dir: Directory to store output
            
        Returns:
            Tuple of (return_code, stdout, stderr)
            
        Raises:
            subprocess.TimeoutExpired: If scan times out
            SecurityError: If privilege escalation fails
        """
        # Build the base command
        base_command = [settings.LYNIS_COMMAND] + settings.LYNIS_ARGS
        
        # Add privilege escalation if needed
        try:
            command = privilege_manager.build_command(base_command)
        except SecurityError as e:
            logger.error(f"Privilege escalation failed: {e}")
            raise
        
        logger.info(f"Executing command: {' '.join(command)}")
        
        # Create a temporary file for output
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, 
                                       encoding='utf-8') as tmp_out:
            temp_output_file = tmp_out.name
            
        try:
            # Execute with timeout
            self.scan_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # Wait for completion with timeout
            stdout, stderr = self.scan_process.communicate(
                timeout=settings.LYNIS_TIMEOUT
            )
            return_code = self.scan_process.returncode
            
            # Write output to temporary file
            with open(temp_output_file, 'w', encoding='utf-8') as f:
                f.write(f"=== STDOUT ===\n{stdout}\n")
                f.write(f"=== STDERR ===\n{stderr}\n")
                f.write(f"=== RETURN CODE ===\n{return_code}\n")
            
            return return_code, stdout, stderr
            
        except subprocess.TimeoutExpired:
            # Kill the process if it times out
            if self.scan_process:
                self.scan_process.kill()
                stdout, stderr = self.scan_process.communicate()
            raise
            
        finally:
            # Always clean up the temporary file
            if Path(temp_output_file).exists():
                try:
                    # Move the temp file to scan directory
                    dest_file = scan_dir / "lynis_output.tmp"
                    Path(temp_output_file).rename(dest_file)
                    logger.debug(f"Moved output to {dest_file}")
                except OSError as e:
                    logger.warning(f"Could not move temp file: {e}")
                    Path(temp_output_file).unlink(missing_ok=True)
            
            self.scan_process = None
    
    def _handle_scan_result(self, scan_id: str, scan_dir: Path, 
                           return_code: int, stdout: str, stderr: str) -> Dict[str, Any]:
        """
        Process and save scan results.
        
        Returns:
            Dictionary with scan results
        """
        logger.info(f"Scan {scan_id} completed with return code: {return_code}")
        
        # Combine output for saving
        combined_output = f"""=== LYNIS SCAN OUTPUT ===
Scan ID: {scan_id}
Timestamp: {datetime.now().isoformat()}
Return Code: {return_code}

=== STDOUT ===
{stdout}

=== STDERR ===
{stderr}
"""
        
        # Save the output
        try:
            output_file = self.file_handler.save_scan_output(
                scan_dir, combined_output, "lynis_raw_output.txt"
            )
        except Exception as e:
            logger.error(f"Failed to save scan output: {e}")
            output_file = None
        
        # Update metadata
        metadata = {
            'scan_id': scan_id,
            'status': 'completed' if return_code == 0 else 'failed',
            'return_code': return_code,
            'output_file': str(output_file) if output_file else None,
            'completed_at': datetime.now().isoformat(),
            'stdout_length': len(stdout),
            'stderr_length': len(stderr),
            'has_errors': bool(stderr.strip())
        }
        
        try:
            self.file_handler.save_metadata(scan_dir, metadata)
        except Exception as e:
            logger.warning(f"Could not update metadata: {e}")
        
        # Move to completed directory
        if return_code == 0:
            try:
                completed_dir = self.file_handler.move_to_completed(scan_dir)
                metadata['completed_directory'] = str(completed_dir)
            except Exception as e:
                logger.warning(f"Could not move to completed: {e}")
        
        return metadata
    
    def run_scan(self) -> Dict[str, Any]:
        """
        Execute a complete Lynis scan.
        
        Returns:
            Dictionary with scan results
            
        Raises:
            RuntimeError: If scan cannot be executed
        """
        logger.info("Starting Lynis scan")
        
        # Validate environment
        try:
            privilege_manager.validate_environment()
        except SecurityError as e:
            raise RuntimeError(f"Environment validation failed: {e}")
        
        # Check if Lynis is installed
        if not self._validate_lynis_installed():
            raise RuntimeError(
                "Lynis is not installed or not in PATH. "
                "Install Lynis first: sudo apt install lynis (or equivalent)"
            )
        
        # Prepare scan
        try:
            self.current_scan_id, self.current_scan_dir = self._prepare_scan()
        except Exception as e:
            raise RuntimeError(f"Scan preparation failed: {e}")
        
        # Execute Lynis
        try:
            return_code, stdout, stderr = self._execute_lynis(self.current_scan_dir)
        except subprocess.TimeoutExpired:
            error_msg = f"Scan {self.current_scan_id} timed out after {settings.LYNIS_TIMEOUT} seconds"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except SecurityError as e:
            error_msg = f"Security error during scan: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during scan execution: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Handle results
        try:
            results = self._handle_scan_result(
                self.current_scan_id, self.current_scan_dir,
                return_code, stdout, stderr
            )
            return results
            
        except Exception as e:
            logger.error(f"Error handling scan results: {e}")
            raise RuntimeError(f"Failed to process scan results: {e}")
        
        finally:
            # Clear current scan
            self.current_scan_id = None
            self.current_scan_dir = None
    
    def cancel_scan(self) -> bool:
        """Cancel the currently running scan."""
        if self.scan_process and self.scan_process.poll() is None:
            logger.info("Cancelling running scan")
            self.scan_process.terminate()
            
            try:
                self.scan_process.wait(timeout=10)
                return True
            except subprocess.TimeoutExpired:
                logger.warning("Process did not terminate, killing it")
                self.scan_process.kill()
                return True
        return False
