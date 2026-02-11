"""
API routes for Linux Security Audit Tool.
"""

from flask import jsonify, request, send_file
from pathlib import Path
import logging
from datetime import datetime

from src.services.scan_service import scan_service
from src.utils.lynis_parser import LynisParser
from config import settings

logger = logging.getLogger(__name__)


def register_routes(app):
    """
    Register all API routes with the Flask application.
    """
    
    @app.route('/api/scans', methods=['POST'])
    def start_scan():
        """
        Start a new security scan.
        
        Request body (optional):
        {
            "priority": "normal|high"  # Currently unused, for future
        }
        
        Returns:
            JSON with scan job details
        """
        try:
            # Parse optional parameters
            data = request.get_json(silent=True) or {}
            
            # Create new scan job
            job = scan_service.create_scan_job()
            
            # Start the scan in background
            started = scan_service.start_scan(job)
            
            if not started:
                return jsonify({
                    "error": "Failed to start scan",
                    "message": "Could not start background scan thread.",
                    "scan_id": job.scan_id
                }), 500
            
            # Return job information
            response = {
                "message": "Scan started successfully",
                "scan_id": job.scan_id,
                "status_endpoint": f"/api/scans/{job.scan_id}",
                "results_endpoint": f"/api/scans/{job.scan_id}/results",
                "estimated_time": "2-10 minutes",
                "timestamp": datetime.now().isoformat()
            }
            
            return jsonify(response), 202  # 202 Accepted
            
        except Exception as e:
            logger.error(f"Error starting scan: {e}")
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
    
    @app.route('/api/scans', methods=['GET'])
    def list_scans():
        """
        List all scan jobs (both in-memory and completed).
        
        Query parameters:
        - limit: Maximum number of jobs to return (default: 50)
        - include_history: Include file system history (default: false)
        
        Returns:
            JSON list of scan jobs
        """
        try:
            # Get query parameters
            limit = request.args.get('limit', default=50, type=int)
            include_history = request.args.get('include_history', default='false').lower() == 'true'
            
            # Get in-memory jobs
            jobs = scan_service.list_jobs(limit=limit)
            
            # Optionally include file system history
            if include_history:
                history = scan_service.get_scan_history()
                # Combine and sort by timestamp (newest first)
                all_scans = jobs + history
                all_scans.sort(
                    key=lambda x: x.get('completed_at') or x.get('created_at') or '',
                    reverse=True
                )
                all_scans = all_scans[:limit]
                
                response = {
                    "jobs": all_scans,
                    "total": len(all_scans),
                    "includes_history": True
                }
            else:
                response = {
                    "jobs": jobs,
                    "total": len(jobs),
                    "includes_history": False
                }
            
            return jsonify(response), 200
            
        except Exception as e:
            logger.error(f"Error listing scans: {e}")
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
    
    @app.route('/api/scans/<scan_id>', methods=['GET'])
    def get_scan_status(scan_id):
        """
        Get status of a specific scan.
        
        Returns:
            JSON with scan status and progress
        """
        try:
            status = scan_service.get_job_status(scan_id)
            
            if not status:
                # Check if it might be in file system history
                history = scan_service.get_scan_history()
                for scan in history:
                    if scan.get('scan_id') == scan_id:
                        scan['status'] = 'completed'  # From history
                        scan['from_history'] = True
                        return jsonify(scan), 200
                
                return jsonify({
                    "error": "Not Found",
                    "message": f"Scan with ID '{scan_id}' not found.",
                    "timestamp": datetime.now().isoformat()
                }), 404
            
            return jsonify(status), 200
            
        except Exception as e:
            logger.error(f"Error getting scan status {scan_id}: {e}")
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
    
    @app.route('/api/scans/<scan_id>/results', methods=['GET'])
    def get_scan_results(scan_id):
        """
        Get results of a completed scan.
        
        Returns:
            JSON with detailed scan results
        """
        try:
            results = scan_service.get_job_result(scan_id)
            
            if not results:
                # Check file system for completed scan
                from src.utils.file_handler import FileHandler
                file_handler = FileHandler(settings.SCANS_DIR)
                
                # Look for scan in completed directory
                scans = file_handler.get_scan_list("completed")
                for scan in scans:
                    if scan.get('scan_id') == scan_id:
                        # Found in file system, load full results
                        scan_dir = Path(scan.get('directory', ''))
                        if scan_dir.exists():
                            # Load metadata
                            metadata_file = scan_dir / "metadata.json"
                            if metadata_file.exists():
                                import json
                                with open(metadata_file, 'r') as f:
                                    metadata = json.load(f)
                                
                                # Load raw output
                                output_file = scan_dir / "lynis_raw_output.txt"
                                if output_file.exists():
                                    with open(output_file, 'r') as f:
                                        raw_output = f.read()
                                    
                                    # Parse Lynis output for structured data
                                    parser = LynisParser()
                                    parsed_data = parser.parse(raw_output)
                                    formatted_data = parser.format_for_display(parsed_data)
                                    
                                    # Create preview with configured length
                                    preview_length = parser.OUTPUT_PREVIEW_LENGTH
                                    output_preview = parser.strip_ansi_codes(raw_output[:preview_length])
                                    if len(raw_output) > preview_length:
                                        output_preview += "..."
                                    
                                    # Return combined results
                                    response = {
                                        "scan_id": scan_id,
                                        "status": "completed",
                                        "from_history": True,
                                        "metadata": metadata,
                                        "parsed_results": formatted_data,
                                        "output_preview": output_preview,
                                        "output_size": len(raw_output),
                                        "raw_output_url": f"/api/scans/{scan_id}/raw",
                                        "completed_at": metadata.get('completed_at')
                                    }
                                    return jsonify(response), 200
            
            if results:
                return jsonify(results), 200
            else:
                return jsonify({
                    "error": "Not Found or Not Complete",
                    "message": f"Results for scan '{scan_id}' not found or scan is not complete.",
                    "timestamp": datetime.now().isoformat()
                }), 404
                
        except Exception as e:
            logger.error(f"Error getting scan results {scan_id}: {e}")
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
    
    @app.route('/api/scans/<scan_id>/raw', methods=['GET'])
    def get_raw_output(scan_id):
        """
        Get raw Lynis output file for a completed scan.
        
        Query parameters:
        - download: If true, force download (default: false)
        
        Returns:
            Raw text file or JSON error
        """
        try:
            # First check in-memory job
            job = scan_service.get_job(scan_id)
            output_file = None
            
            if job and job.result:
                output_path = job.result.get('output_file')
                if output_path:
                    output_file = Path(output_path)
            
            # If not found, check file system
            if not output_file or not output_file.exists():
                from src.utils.file_handler import FileHandler
                file_handler = FileHandler(settings.SCANS_DIR)
                
                scans = file_handler.get_scan_list("completed")
                for scan in scans:
                    if scan.get('scan_id') == scan_id:
                        scan_dir = Path(scan.get('directory', ''))
                        output_file = scan_dir / "lynis_raw_output.txt"
                        if output_file.exists():
                            break
                        else:
                            output_file = None
            
            if not output_file or not output_file.exists():
                return jsonify({
                    "error": "Not Found",
                    "message": f"Raw output for scan '{scan_id}' not found.",
                    "timestamp": datetime.now().isoformat()
                }), 404
            
            # Check if download is requested
            download = request.args.get('download', default='false').lower() == 'true'
            
            return send_file(
                str(output_file),
                mimetype='text/plain',
                as_attachment=download,
                download_name=f"lynis_scan_{scan_id}.txt"
            )
            
        except Exception as e:
            logger.error(f"Error getting raw output {scan_id}: {e}")
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
    
    @app.route('/api/scans/<scan_id>', methods=['DELETE'])
    def cancel_scan(scan_id):
        """
        Cancel a running scan.
        
        Returns:
            JSON with cancellation status
        """
        try:
            cancelled = scan_service.cancel_job(scan_id)
            
            if cancelled:
                return jsonify({
                    "message": f"Scan '{scan_id}' cancelled successfully.",
                    "scan_id": scan_id,
                    "timestamp": datetime.now().isoformat()
                }), 200
            else:
                return jsonify({
                    "error": "Cannot Cancel",
                    "message": f"Scan '{scan_id}' cannot be cancelled or does not exist.",
                    "timestamp": datetime.now().isoformat()
                }), 400
                
        except Exception as e:
            logger.error(f"Error cancelling scan {scan_id}: {e}")
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
    
    @app.route('/api/history', methods=['GET'])
    def get_history():
        """
        Get scan history from file system (completed scans).
        
        Query parameters:
        - limit: Maximum number of scans to return (default: 100)
        - days: Only return scans from last N days (optional)
        
        Returns:
            JSON list of historical scans
        """
        try:
            limit = request.args.get('limit', default=100, type=int)
            days = request.args.get('days', default=None, type=int)
            
            history = scan_service.get_scan_history()
            
            # Filter by days if specified
            if days:
                cutoff = datetime.now().timestamp() - (days * 86400)
                filtered = []
                for scan in history:
                    timestamp_str = scan.get('timestamp', '')
                    if timestamp_str:
                        try:
                            # Parse timestamp from directory name
                            scan_time = datetime.strptime(
                                timestamp_str.split('_')[0], 
                                "%Y%m%d"
                            ).timestamp()
                            if scan_time >= cutoff:
                                filtered.append(scan)
                        except (ValueError, IndexError):
                            # If we can't parse, include it
                            filtered.append(scan)
                history = filtered
            
            # Apply limit
            history = history[:limit]
            
            return jsonify({
                "scans": history,
                "total": len(history),
                "limit": limit,
                "days_filter": days
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting scan history: {e}")
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
    
    @app.route('/api/system/status', methods=['GET'])
    def system_status():
        """
        Get system and service status.
        
        Returns:
            JSON with system information
        """
        try:
            from src.utils.security import privilege_manager
            import getpass
            import os
            
            # Get system info
            is_root, username = privilege_manager.check_current_privileges()
            
            # Check if Lynis is installed
            from src.core.scanner import LynisScanner
            scanner = LynisScanner()
            lynis_installed = scanner._validate_lynis_installed()
            
            # Count completed scans
            from src.utils.file_handler import FileHandler
            file_handler = FileHandler(settings.SCANS_DIR)
            completed_scans = len(file_handler.get_scan_list("completed"))
            
            # Get disk usage
            import shutil
            total, used, free = shutil.disk_usage(settings.SCANS_DIR)
            
            response = {
                "system": {
                    "user": username,
                    "is_root": is_root,
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "hostname": os.uname().nodename
                },
                "service": {
                    "lynis_installed": lynis_installed,
                    "scans_directory": str(settings.SCANS_DIR),
                    "total_completed_scans": completed_scans,
                    "active_jobs": len(scan_service.list_jobs(limit=1000))
                },
                "storage": {
                    "total_gb": round(total / (1024**3), 2),
                    "used_gb": round(used / (1024**3), 2),
                    "free_gb": round(free / (1024**3), 2),
                    "usage_percent": round((used / total) * 100, 1)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return jsonify(response), 200
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
    
    @app.route('/api/scans/<scan_id>/pdf', methods=['GET'])
    def generate_pdf_report(scan_id):
        """
        Generate and download a PDF report for a completed scan.
        
        Returns:
            PDF file download or JSON error
        """
        try:
            from src.utils.pdf_generator import PDFReportGenerator
            
            # Get scan results
            results = scan_service.get_job_result(scan_id)
            
            if not results:
                # Check file system for completed scan
                from src.utils.file_handler import FileHandler
                file_handler = FileHandler(settings.SCANS_DIR)
                
                # Look for scan in completed directory
                scans = file_handler.get_scan_list("completed")
                for scan in scans:
                    if scan.get('scan_id') == scan_id:
                        # Found in file system, load full results
                        scan_dir = Path(scan.get('directory', ''))
                        if scan_dir.exists():
                            # Load metadata
                            metadata_file = scan_dir / "metadata.json"
                            if metadata_file.exists():
                                import json
                                with open(metadata_file, 'r') as f:
                                    metadata = json.load(f)
                                
                                # Load raw output
                                output_file = scan_dir / "lynis_raw_output.txt"
                                if output_file.exists():
                                    with open(output_file, 'r') as f:
                                        raw_output = f.read()
                                    
                                    # Parse Lynis output for structured data
                                    parser = LynisParser()
                                    parsed_data = parser.parse(raw_output)
                                    formatted_data = parser.format_for_display(parsed_data)
                                    
                                    # Create results structure
                                    results = {
                                        "scan_id": scan_id,
                                        "status": "completed",
                                        "from_history": True,
                                        "metadata": metadata,
                                        "parsed_results": formatted_data,
                                        "completed_at": metadata.get('completed_at'),
                                        "timestamp": metadata.get('timestamp')
                                    }
                                    break
            
            if not results:
                return jsonify({
                    "error": "Not Found",
                    "message": f"Scan '{scan_id}' not found or not completed.",
                    "timestamp": datetime.now().isoformat()
                }), 404
            
            # Generate PDF
            generator = PDFReportGenerator()
            pdf_bytes = generator.generate_report(results)
            
            # Create response with PDF
            from flask import Response
            response = Response(pdf_bytes, mimetype='application/pdf')
            response.headers['Content-Disposition'] = f'attachment; filename=security_audit_{scan_id}.pdf'
            response.headers['Content-Type'] = 'application/pdf'
            
            return response
            
        except ImportError as e:
            logger.error(f"PDF generation library not available: {e}")
            return jsonify({
                "error": "Service Unavailable",
                "message": "PDF generation is not available. Please install reportlab: pip install reportlab",
                "timestamp": datetime.now().isoformat()
            }), 503
        except Exception as e:
            logger.error(f"Error generating PDF for scan {scan_id}: {e}")
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
    
    logger.info("API routes registered successfully")
