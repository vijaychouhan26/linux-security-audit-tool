"""
File and directory management utilities.
Ensures organized, timestamped scan storage.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional, Dict, Any, List  # Added List import
import json

logger = logging.getLogger(__name__)


class FileHandler:
    """Manages scan file storage and organization."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for subdir in ["pending", "completed", "archived"]:
            (self.base_dir / subdir).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directories exist in {self.base_dir}")
    
    def create_scan_directory(self, scan_id: str) -> Path:
        """
        Create a timestamped directory for a new scan.
        
        Args:
            scan_id: Unique identifier for the scan
            
        Returns:
            Path to the created directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_name = f"{timestamp}_{scan_id}"
        scan_dir = self.base_dir / "pending" / dir_name
        
        try:
            scan_dir.mkdir(parents=True, exist_ok=False)
            logger.info(f"Created scan directory: {scan_dir}")
            return scan_dir
        except FileExistsError:
            logger.warning(f"Scan directory already exists: {scan_dir}")
            # Append microsecond for uniqueness
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            dir_name = f"{timestamp}_{scan_id}"
            scan_dir = self.base_dir / "pending" / dir_name
            scan_dir.mkdir(parents=True, exist_ok=True)
            return scan_dir
    
    def save_scan_output(self, scan_dir: Path, content: str, 
                         filename: str = "lynis_raw.txt") -> Path:
        """
        Save raw Lynis output to file.
        
        Args:
            scan_dir: Directory to save the file in
            content: The content to save
            filename: Name of the file
            
        Returns:
            Path to the saved file
        """
        output_file = scan_dir / filename
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Set restrictive permissions (owner read/write only)
            os.chmod(output_file, 0o600)
            
            logger.info(f"Saved scan output to {output_file}")
            return output_file
            
        except (IOError, OSError) as e:
            logger.error(f"Failed to save scan output: {e}")
            raise
    
    def save_metadata(self, scan_dir: Path, metadata: Dict[str, Any]) -> Path:
        """
        Save scan metadata as JSON.
        
        Args:
            scan_dir: Directory to save metadata in
            metadata: Dictionary of metadata
            
        Returns:
            Path to the metadata file
        """
        metadata_file = scan_dir / "metadata.json"
        
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            os.chmod(metadata_file, 0o600)
            logger.debug(f"Saved metadata to {metadata_file}")
            return metadata_file
            
        except (IOError, json.JSONEncodeError) as e:
            logger.error(f"Failed to save metadata: {e}")
            raise
    
    def move_to_completed(self, scan_dir: Path) -> Optional[Path]:
        """
        Move scan from pending to completed directory.
        
        Args:
            scan_dir: Current scan directory path
            
        Returns:
            New path in completed directory, or None if failed
        """
        if not scan_dir.exists():
            logger.error(f"Cannot move non-existent directory: {scan_dir}")
            return None
        
        try:
            # Get the directory name
            dir_name = scan_dir.name
            new_path = self.base_dir / "completed" / dir_name
            
            # Move the directory
            shutil.move(str(scan_dir), str(new_path))
            logger.info(f"Moved scan to completed: {new_path}")
            return new_path
            
        except (shutil.Error, OSError) as e:
            logger.error(f"Failed to move scan directory: {e}")
            return None
    
    def cleanup_old_scans(self, max_age_days: int = 30) -> int:
        """
        Remove scans older than specified days.
        
        Args:
            max_age_days: Maximum age in days
            
        Returns:
            Number of scans removed
        """
        removed_count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_days * 86400)
        
        for status_dir in ["pending", "completed", "archived"]:
            directory = self.base_dir / status_dir
            
            if not directory.exists():
                continue
            
            for item in directory.iterdir():
                if item.is_dir():
                    try:
                        # Extract timestamp from directory name
                        timestamp_str = item.name.split('_')[0]
                        dir_time = datetime.strptime(
                            timestamp_str, "%Y%m%d_%H%M%S"
                        ).timestamp()
                        
                        if dir_time < cutoff_time:
                            shutil.rmtree(item)
                            removed_count += 1
                            logger.info(f"Removed old scan: {item}")
                            
                    except (ValueError, IndexError, OSError) as e:
                        logger.warning(f"Could not remove {item}: {e}")
        
        return removed_count
    
    def get_scan_list(self, status: str = "completed") -> List[Dict[str, Any]]:
        """
        Get list of scans with their metadata.
        
        Args:
            status: Scan status (pending, completed, archived)
            
        Returns:
            List of scan metadata dictionaries
        """
        scans = []
        directory = self.base_dir / status
        
        if not directory.exists():
            return scans
        
        for item in directory.iterdir():
            if item.is_dir():
                metadata_file = item / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        scans.append(metadata)
                    except (json.JSONDecodeError, IOError):
                        # Create basic metadata from directory name
                        parts = item.name.split('_')
                        if len(parts) >= 2:
                            scans.append({
                                'scan_id': '_'.join(parts[1:]),
                                'timestamp': parts[0],
                                'directory': str(item)
                            })
        
        # Sort by timestamp (newest first)
        scans.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return scans
