"""
Security-related utilities for privilege handling and validation.
CRITICAL: Proper sudo handling to prevent silent failures.
"""

import os
import sys
import subprocess
import getpass
from typing import Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass


class PrivilegeManager:
    """Manages privilege escalation and validation for Lynis execution."""
    
    def __init__(self, use_sudo: bool = True):
        self.use_sudo = use_sudo
        self._sudo_available = None
        
    def check_sudo_available(self) -> bool:
        """
        Check if sudo is available and we can use it.
        Returns: True if sudo is available and usable
        Raises: SecurityError if sudo is required but not available
        """
        if not self.use_sudo:
            return False
            
        if self._sudo_available is None:
            try:
                # Check if sudo command exists
                result = subprocess.run(
                    ["which", "sudo"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                self._sudo_available = result.returncode == 0
                
                if self._sudo_available:
                    logger.debug("sudo command is available")
                else:
                    logger.warning("sudo command not found in PATH")
                    
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.error(f"Error checking sudo availability: {e}")
                self._sudo_available = False
        
        return self._sudo_available
    
    def check_current_privileges(self) -> Tuple[bool, str]:
        """
        Check current user privileges.
        Returns: (is_root: bool, username: str)
        """
        username = getpass.getuser()
        is_root = os.geteuid() == 0  # Effective user ID 0 = root
        
        logger.info(f"Current user: {username}, is root: {is_root}")
        return is_root, username
    
    def build_command(self, base_command: List[str]) -> List[str]:
        """
        Build the command with appropriate privilege escalation.
        
        Args:
            base_command: The command to run (e.g., ["lynis", "audit", "system"])
            
        Returns:
            Command list with sudo if needed
            
        Raises:
            SecurityError: If sudo is required but not available
        """
        is_root, username = self.check_current_privileges()
        
        # If we're already root, no sudo needed
        if is_root:
            logger.info("Running as root, sudo not needed")
            return base_command
        
        # If we're not root but sudo is disabled
        if not self.use_sudo:
            raise SecurityError(
                "Not running as root and sudo is disabled. "
                "Either run as root or enable sudo usage."
            )
        
        # Check if sudo is available
        if not self.check_sudo_available():
            raise SecurityError(
                "sudo is required but not available. "
                "Install sudo or run this tool as root."
            )
        
        # Add sudo to command
        sudo_command = [self.SUDO_COMMAND] + base_command
        logger.info(f"Command will run with sudo as user: {username}")
        
        return sudo_command
    
    def validate_environment(self) -> None:
        """
        Validate the execution environment.
        Raises exceptions for critical issues.
        """
        # Check Python version
        if sys.version_info < (3, 8):
            raise SecurityError(
                f"Python 3.8+ required. Current: {sys.version_info}"
            )
        
        # Check if we can potentially use sudo
        if self.use_sudo:
            self.check_sudo_available()
        
        logger.info("Environment validation passed")


# Singleton instance
privilege_manager = PrivilegeManager()
