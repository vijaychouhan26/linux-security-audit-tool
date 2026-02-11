#!/usr/bin/env python3
"""
Severity Classifier for Security Findings
Categorizes security findings into risk levels (low, medium, high, critical)
"""

import re
from typing import Dict, List, Any
from enum import Enum


class Severity(Enum):
    """Severity levels for security findings"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SeverityClassifier:
    """
    Classifies security findings by severity based on keywords and patterns.
    """
    
    # Keywords that indicate different severity levels
    CRITICAL_KEYWORDS = [
        'root password', 'no password', 'weak password', 'default password',
        'remote root login', 'ssh root login', 'unpatched vulnerability',
        'critical vulnerability', 'remote code execution', 'rce',
        'privilege escalation', 'compromised', 'backdoor', 'malware'
    ]
    
    HIGH_KEYWORDS = [
        'firewall', 'disabled', 'not installed', 'not running',
        'unencrypted', 'weak cipher', 'outdated', 'deprecated',
        'world writable', 'world readable', 'permission 777',
        'selinux disabled', 'apparmor disabled', 'security module',
        'kernel parameter', 'sysctl', 'insecure protocol',
        'telnet', 'ftp', 'rsh', 'no authentication'
    ]
    
    MEDIUM_KEYWORDS = [
        'warning', 'configuration', 'update available', 'upgrade',
        'missing', 'not found', 'permission', 'ownership',
        'log file', 'audit', 'monitoring', 'integrity',
        'certificate', 'ssl', 'tls', 'encryption',
        'network service', 'open port', 'listening'
    ]
    
    LOW_KEYWORDS = [
        'suggestion', 'recommendation', 'consider', 'optional',
        'banner', 'informational', 'documentation', 'optimization',
        'performance', 'best practice'
    ]
    
    # File/permission patterns that indicate high severity
    CRITICAL_FILE_PATTERNS = [
        r'/etc/shadow',
        r'/etc/passwd',
        r'/root/\.ssh',
        r'\.pem$',
        r'\.key$',
        r'private.*key'
    ]
    
    HIGH_FILE_PATTERNS = [
        r'/etc/sudoers',
        r'/etc/ssh/sshd_config',
        r'/etc/pam\.d/',
        r'/boot/',
        r'\.authorized_keys'
    ]
    
    def __init__(self):
        """Initialize the classifier"""
        self.statistics = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
    
    def classify_finding(self, finding: Dict[str, Any]) -> Severity:
        """
        Classify a security finding based on its content.
        
        Args:
            finding: Dictionary containing finding information
                    (must have 'message' key, optionally 'type', 'test_id')
        
        Returns:
            Severity enum value
        """
        message = finding.get('message', '').lower()
        finding_type = finding.get('type', '').lower()
        test_id = finding.get('test_id', '')
        
        # Check for critical indicators
        if finding_type == 'warning' or 'warning' in message:
            # Warnings are at least medium, check if they're higher
            for keyword in self.CRITICAL_KEYWORDS:
                if keyword in message:
                    return Severity.CRITICAL
            
            for keyword in self.HIGH_KEYWORDS:
                if keyword in message:
                    return Severity.HIGH
            
            # Check file patterns
            for pattern in self.CRITICAL_FILE_PATTERNS:
                if re.search(pattern, message, re.IGNORECASE):
                    return Severity.CRITICAL
            
            for pattern in self.HIGH_FILE_PATTERNS:
                if re.search(pattern, message, re.IGNORECASE):
                    return Severity.HIGH
            
            # Default warnings to medium
            return Severity.MEDIUM
        
        # Check suggestions
        if finding_type == 'suggestion' or 'suggest' in message:
            # Check if suggestion is critical
            for keyword in self.CRITICAL_KEYWORDS:
                if keyword in message:
                    return Severity.HIGH  # Suggestions are one level lower
            
            for keyword in self.HIGH_KEYWORDS:
                if keyword in message:
                    return Severity.MEDIUM
            
            # Most suggestions are low
            return Severity.LOW
        
        # General message classification
        for keyword in self.CRITICAL_KEYWORDS:
            if keyword in message:
                return Severity.CRITICAL
        
        for keyword in self.HIGH_KEYWORDS:
            if keyword in message:
                return Severity.HIGH
        
        for keyword in self.MEDIUM_KEYWORDS:
            if keyword in message:
                return Severity.MEDIUM
        
        for keyword in self.LOW_KEYWORDS:
            if keyword in message:
                return Severity.LOW
        
        # Default to info
        return Severity.INFO
    
    def classify_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify multiple findings and add severity to each.
        
        Args:
            findings: List of finding dictionaries
        
        Returns:
            List of findings with added 'severity' key
        """
        classified = []
        
        for finding in findings:
            severity = self.classify_finding(finding)
            finding_with_severity = finding.copy()
            finding_with_severity['severity'] = severity.value
            finding_with_severity['severity_level'] = self._severity_to_level(severity)
            classified.append(finding_with_severity)
            
            # Update statistics
            self.statistics[severity.value] += 1
        
        # Sort by severity (critical first)
        severity_order = {
            'critical': 0,
            'high': 1,
            'medium': 2,
            'low': 3,
            'info': 4
        }
        classified.sort(key=lambda x: severity_order.get(x['severity'], 999))
        
        return classified
    
    def _severity_to_level(self, severity: Severity) -> int:
        """
        Convert severity to numeric level for sorting.
        
        Args:
            severity: Severity enum
        
        Returns:
            Numeric level (0=critical, 4=info)
        """
        mapping = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4
        }
        return mapping.get(severity, 4)
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get severity distribution statistics.
        
        Returns:
            Dictionary with counts for each severity level
        """
        return self.statistics.copy()
    
    def get_summary(self) -> str:
        """
        Get a human-readable summary of findings.
        
        Returns:
            Summary string
        """
        total = sum(self.statistics.values())
        if total == 0:
            return "No findings to analyze"
        
        critical_pct = (self.statistics['critical'] / total) * 100
        high_pct = (self.statistics['high'] / total) * 100
        
        if self.statistics['critical'] > 0:
            return f"CRITICAL: {self.statistics['critical']} critical issues require immediate attention!"
        elif self.statistics['high'] > 0:
            return f"HIGH RISK: {self.statistics['high']} high-priority issues found"
        elif self.statistics['medium'] > 0:
            return f"MODERATE: {self.statistics['medium']} medium-priority issues to address"
        else:
            return f"GOOD: Only {self.statistics['low']} low-priority items found"
    
    def reset_statistics(self):
        """Reset the statistics counters"""
        for key in self.statistics:
            self.statistics[key] = 0
