#!/usr/bin/env python3
"""
Lynis Output Parser
Parses raw Lynis output into structured, human-readable data for dashboard display.
"""

import re
from typing import Dict, List, Any, Optional


class LynisParser:
    """Parse Lynis security audit output into structured data."""
    
    # Configuration constants
    MAX_SUGGESTION_DETAILS = 3  # Maximum detail lines per suggestion
    MAX_WARNINGS_DISPLAY = 10  # Maximum warnings to return
    MAX_SUGGESTIONS_DISPLAY = 20  # Maximum suggestions to return
    OUTPUT_PREVIEW_LENGTH = 2000  # Characters for output preview
    
    def __init__(self):
        """Initialize the parser."""
        self.ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    
    def strip_ansi_codes(self, text: str) -> str:
        """
        Remove ANSI color codes from text.
        
        Args:
            text: Text with ANSI escape sequences
            
        Returns:
            Clean text without ANSI codes
        """
        return self.ansi_escape.sub('', text)
    
    def parse(self, raw_output: str) -> Dict[str, Any]:
        """
        Parse raw Lynis output into structured data.
        
        Args:
            raw_output: Raw output from Lynis scan
            
        Returns:
            Dictionary containing parsed structured data
        """
        # Strip ANSI codes for parsing
        clean_output = self.strip_ansi_codes(raw_output)
        
        parsed_data = {
            'summary': self._parse_summary(clean_output),
            'warnings': self._extract_warnings(clean_output),
            'suggestions': self._extract_suggestions(clean_output),
            'system_info': self._parse_system_info(clean_output),
            'security_components': self._parse_security_components(clean_output),
        }
        
        return parsed_data
    
    def _parse_summary(self, text: str) -> Dict[str, Any]:
        """Extract summary information from Lynis output."""
        summary = {
            'hardening_index': None,
            'tests_performed': None,
            'plugins_enabled': None,
        }
        
        # Extract hardening index
        hardening_match = re.search(r'Hardening index\s*:\s*(\d+)', text)
        if hardening_match:
            summary['hardening_index'] = int(hardening_match.group(1))
        
        # Extract tests performed
        tests_match = re.search(r'Tests performed\s*:\s*(\d+)', text)
        if tests_match:
            summary['tests_performed'] = int(tests_match.group(1))
        
        # Extract plugins enabled
        plugins_match = re.search(r'Plugins enabled\s*:\s*(\d+)', text)
        if plugins_match:
            summary['plugins_enabled'] = int(plugins_match.group(1))
        
        return summary
    
    def _extract_warnings(self, text: str) -> List[Dict[str, str]]:
        """Extract warnings from Lynis output."""
        warnings = []
        
        # Look for warnings count
        warnings_match = re.search(r'Warnings\s*\((\d+)\):', text)
        warnings_count = int(warnings_match.group(1)) if warnings_match else 0
        
        # Look for [WARNING] markers in the output
        warning_pattern = re.compile(r'\[WARNING\]:?\s*(.+?)(?=\n|$)', re.IGNORECASE)
        for match in warning_pattern.finditer(text):
            warnings.append({
                'type': 'warning',
                'message': match.group(1).strip()
            })
        
        return warnings
    
    def _extract_suggestions(self, text: str) -> List[Dict[str, Any]]:
        """Extract suggestions from Lynis output."""
        suggestions = []
        
        # Look for suggestions section
        suggestions_section = re.search(
            r'Suggestions.*?(?=Follow-up:|================================================================================)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if suggestions_section:
            suggestion_text = suggestions_section.group(0)
            
            # Parse individual suggestions with test IDs
            suggestion_pattern = re.compile(
                r'\*\s*(.+?)\s*\[([A-Z]+-\d+)\]\s*(?:\n\s*-\s*(.+?))?(?=\n\s*\*|\Z)',
                re.DOTALL
            )
            
            for match in suggestion_pattern.finditer(suggestion_text):
                suggestion = {
                    'message': match.group(1).strip(),
                    'test_id': match.group(2).strip(),
                    'details': []
                }
                
                # Extract additional details if present
                if match.group(3):
                    details_text = match.group(3).strip()
                    # Extract Related resources or Details
                    detail_lines = [line.strip() for line in details_text.split('\n') if line.strip()]
                    suggestion['details'] = detail_lines[:self.MAX_SUGGESTION_DETAILS]
                
                suggestions.append(suggestion)
        
        return suggestions
    
    def _parse_system_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract system information from Lynis output."""
        system_info = {
            'os_name': None,
            'os_version': None,
            'kernel_version': None,
            'hostname': None,
            'hardware_platform': None,
        }
        
        # Extract OS name
        os_name_match = re.search(r'Operating system name:\s*(.+?)(?=\n|$)', text)
        if os_name_match:
            system_info['os_name'] = os_name_match.group(1).strip()
        
        # Extract OS version
        os_version_match = re.search(r'Operating system version:\s*(.+?)(?=\n|$)', text)
        if os_version_match:
            system_info['os_version'] = os_version_match.group(1).strip()
        
        # Extract kernel version
        kernel_match = re.search(r'Kernel version:\s*(.+?)(?=\n|$)', text)
        if kernel_match:
            system_info['kernel_version'] = kernel_match.group(1).strip()
        
        # Extract hostname
        hostname_match = re.search(r'Hostname:\s*(.+?)(?=\n|$)', text)
        if hostname_match:
            system_info['hostname'] = hostname_match.group(1).strip()
        
        # Extract hardware platform
        platform_match = re.search(r'Hardware platform:\s*(.+?)(?=\n|$)', text)
        if platform_match:
            system_info['hardware_platform'] = platform_match.group(1).strip()
        
        return system_info
    
    def _parse_security_components(self, text: str) -> Dict[str, bool]:
        """Extract security components status from Lynis output."""
        components = {
            'firewall': False,
            'intrusion_software': False,
            'malware_scanner': False,
        }
        
        # Look for Software components section
        components_section = re.search(
            r'Software components:(.+?)(?=Files:|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if components_section:
            section_text = components_section.group(1)
            
            # Check for [V] (installed) or [X] (not installed)
            if re.search(r'Firewall\s+\[V\]', section_text):
                components['firewall'] = True
            if re.search(r'Intrusion software\s+\[V\]', section_text):
                components['intrusion_software'] = True
            if re.search(r'Malware scanner\s+\[V\]', section_text):
                components['malware_scanner'] = True
        
        return components
    
    def format_for_display(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format parsed data for dashboard display.
        
        Args:
            parsed_data: Parsed Lynis output data
            
        Returns:
            Formatted data optimized for dashboard display
        """
        summary = parsed_data.get('summary', {})
        warnings = parsed_data.get('warnings', [])
        suggestions = parsed_data.get('suggestions', [])
        
        return {
            'score': {
                'hardening_index': summary.get('hardening_index', 0),
                'display': f"{summary.get('hardening_index', 0)}/100",
                'status': self._get_score_status(summary.get('hardening_index', 0))
            },
            'statistics': {
                'tests_performed': summary.get('tests_performed', 0),
                'warnings_count': len(warnings),
                'suggestions_count': len(suggestions),
                'plugins_enabled': summary.get('plugins_enabled', 0)
            },
            'system_info': parsed_data.get('system_info', {}),
            'security_components': parsed_data.get('security_components', {}),
            'findings': {
                'warnings': warnings[:self.MAX_WARNINGS_DISPLAY],
                'suggestions': suggestions[:self.MAX_SUGGESTIONS_DISPLAY],
            }
        }
    
    def _get_score_status(self, score: int) -> str:
        """
        Get status label based on hardening index score.
        
        Args:
            score: Hardening index (0-100)
            
        Returns:
            Status label (excellent, good, fair, poor)
        """
        if score >= 80:
            return 'excellent'
        elif score >= 60:
            return 'good'
        elif score >= 40:
            return 'fair'
        else:
            return 'poor'
