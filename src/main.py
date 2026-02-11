"""
Main entry point for Phase 1 of Linux Security Audit Tool.
Provides clear terminal interface for running scans.
"""

import sys
import os
import logging
from pathlib import Path

# CRITICAL: Add project root to Python path before any imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.scanner import LynisScanner
    from src.utils.security import privilege_manager
    from config import settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path}")
    sys.exit(1)


def setup_logging() -> logging.Logger:
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    settings.LOGS_DIR.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.FileHandler(settings.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Linux Security Audit Tool - Phase 1")
    logger.info("=" * 60)
    
    return logger


def print_banner():
    """Print application banner."""
    banner = """
╔══════════════════════════════════════════════════════════╗
║     Linux Security Audit Tool - Phase 1                  ║
║     Local System Scanner                                 ║
╚══════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_instructions():
    """Print usage instructions."""
    instructions = """
INSTRUCTIONS:
1. This tool runs Lynis locally on this system
2. Lynis requires root privileges for a full audit
3. If you're not root, the tool will use sudo
4. You may be prompted for your sudo password
5. Scan results are saved in: scans/completed/

IMPORTANT:
- Ensure Lynis is installed: sudo apt install lynis
- Run in a terminal with sufficient privileges
- Scans may take 2-10 minutes depending on system
"""
    print(instructions)


def confirm_scan() -> bool:
    """Get user confirmation before starting scan."""
    print("\n" + "=" * 60)
    response = input("Start Lynis system audit? (yes/no): ").strip().lower()
    return response in ['yes', 'y']


def main():
    """Main execution function."""
    # Setup
    logger = setup_logging()
    print_banner()
    
    try:
        # Check environment
        print("🔍 Checking system environment...")
        
        # Validate Python version
        if sys.version_info < settings.MIN_PYTHON_VERSION:
            print(f"❌ Python {settings.MIN_PYTHON_VERSION[0]}.{settings.MIN_PYTHON_VERSION[1]}+ required")
            sys.exit(1)
        
        # Check privileges
        is_root, username = privilege_manager.check_current_privileges()
        privilege_status = "root" if is_root else f"user: {username}"
        print(f"✓ Running as: {privilege_status}")
        
        # Check sudo availability if needed
        if settings.USE_SUDO and not is_root:
            if privilege_manager.check_sudo_available():
                print("✓ sudo is available")
            else:
                print("⚠  sudo not available - some checks may fail")
        
        print_instructions()
        
        # Get confirmation
        if not confirm_scan():
            print("Scan cancelled by user.")
            sys.exit(0)
        
        # Create and run scanner
        print("\n" + "=" * 60)
        print("🚀 Starting Lynis Security Audit")
        print("=" * 60)
        
        scanner = LynisScanner()
        
        print("\n📋 Scan Information:")
        print(f"  • Scan ID will be generated")
        print(f"  • Output directory: {settings.COMPLETED_SCANS_DIR}")
        print(f"  • Timeout: {settings.LYNIS_TIMEOUT} seconds")
        print(f"  • Using sudo: {'Yes' if settings.USE_SUDO else 'No'}")
        
        print("\n⏳ Executing Lynis... This may take several minutes.")
        print("   Please wait for completion.")
        print("   Do NOT interrupt the process.")
        
        # Run the scan
        try:
            results = scanner.run_scan()
            
            # Display results
            print("\n" + "=" * 60)
            print("✅ SCAN COMPLETED SUCCESSFULLY")
            print("=" * 60)
            
            print(f"\n📊 Scan Results:")
            print(f"  • Scan ID: {results.get('scan_id', 'N/A')}")
            print(f"  • Status: {results.get('status', 'N/A')}")
            print(f"  • Return Code: {results.get('return_code', 'N/A')}")
            print(f"  • Output File: {results.get('output_file', 'N/A')}")
            print(f"  • Completed: {results.get('completed_at', 'N/A')}")
            
            if results.get('has_errors'):
                print("  ⚠  Scan completed with warnings/errors")
            
            print(f"\n💾 Results saved to: {results.get('completed_directory', 'N/A')}")
            print("\n📖 To view full output:")
            print(f"   cat {results.get('output_file', 'path/to/output')}")
            
        except RuntimeError as e:
            print(f"\n❌ SCAN FAILED: {e}")
            logger.error(f"Scan failed: {e}")
            sys.exit(1)
        
        except KeyboardInterrupt:
            print("\n\n⚠  Scan interrupted by user")
            if scanner.cancel_scan():
                print("✓ Scan process terminated")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        logger.exception("Unexpected error in main execution")
        sys.exit(1)
    
    finally:
        print("\n" + "=" * 60)
        print("Linux Security Audit Tool - Execution Complete")
        print("=" * 60)


if __name__ == "__main__":
    main()
