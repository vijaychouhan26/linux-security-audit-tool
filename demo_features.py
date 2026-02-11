#!/usr/bin/env python3
"""
Visual Demonstration of New Features
Shows human-readable output with severity indicators
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.severity_classifier import SeverityClassifier
from src.utils.lynis_parser import LynisParser
import json

# ANSI color codes for terminal output
COLORS = {
    'critical': '\033[91m',  # Red
    'high': '\033[93m',      # Yellow/Orange
    'medium': '\033[94m',    # Blue
    'low': '\033[96m',       # Cyan
    'reset': '\033[0m',
    'bold': '\033[1m',
    'green': '\033[92m',
}

def print_banner():
    print(f"{COLORS['bold']}{'='*70}{COLORS['reset']}")
    print(f"{COLORS['bold']}  Linux Security Audit Tool - Human-Readable Output Demo{COLORS['reset']}")
    print(f"{COLORS['bold']}{'='*70}{COLORS['reset']}\n")

def print_severity_summary(severity_summary, risk_summary):
    print(f"{COLORS['bold']}📊 SECURITY FINDINGS BY SEVERITY{COLORS['reset']}\n")
    
    # Print severity boxes
    for severity, count in [('critical', severity_summary.get('critical', 0)),
                             ('high', severity_summary.get('high', 0)),
                             ('medium', severity_summary.get('medium', 0)),
                             ('low', severity_summary.get('low', 0))]:
        if count > 0:
            color = COLORS.get(severity, '')
            label = severity.upper()
            print(f"{color}┌─────────────┐{COLORS['reset']}")
            print(f"{color}│   {count:^5}     │{COLORS['reset']}")
            print(f"{color}│  {label:^9} │{COLORS['reset']}")
            print(f"{color}└─────────────┘{COLORS['reset']}\n")
    
    print(f"{COLORS['bold']}Risk Assessment:{COLORS['reset']} {risk_summary}\n")

def print_top_findings(findings):
    print(f"{COLORS['bold']}🔍 TOP PRIORITY FINDINGS{COLORS['reset']}\n")
    
    # Show critical findings
    critical = findings.get('critical', [])
    if critical:
        print(f"{COLORS['critical']}{COLORS['bold']}CRITICAL ISSUES:{COLORS['reset']}")
        for idx, finding in enumerate(critical[:3], 1):
            msg = finding.get('message', 'No description')
            print(f"  {idx}. {COLORS['critical']}⚠️  {msg}{COLORS['reset']}")
        print()
    
    # Show high findings
    high = findings.get('high', [])
    if high:
        print(f"{COLORS['high']}{COLORS['bold']}HIGH PRIORITY:{COLORS['reset']}")
        for idx, finding in enumerate(high[:3], 1):
            msg = finding.get('message', 'No description')
            print(f"  {idx}. {COLORS['high']}⚠️  {msg}{COLORS['reset']}")
        print()
    
    # Show medium findings
    medium = findings.get('medium', [])
    if medium:
        print(f"{COLORS['medium']}{COLORS['bold']}MEDIUM PRIORITY:{COLORS['reset']}")
        for idx, finding in enumerate(medium[:2], 1):
            msg = finding.get('message', 'No description')
            print(f"  {idx}. {COLORS['medium']}ℹ️  {msg}{COLORS['reset']}")
        print()

def print_system_info(system_info, score):
    print(f"{COLORS['bold']}💻 SYSTEM INFORMATION{COLORS['reset']}\n")
    print(f"  OS: {system_info.get('os_name', 'Unknown')} {system_info.get('os_version', '')}")
    print(f"  Kernel: {system_info.get('kernel_version', 'Unknown')}")
    print(f"  Hostname: {system_info.get('hostname', 'Unknown')}")
    print(f"  Platform: {system_info.get('hardware_platform', 'Unknown')}")
    
    hardening_index = score.get('hardening_index', 0)
    status = score.get('status', 'unknown')
    
    # Color code the score
    if hardening_index >= 80:
        score_color = COLORS['green']
    elif hardening_index >= 60:
        score_color = COLORS['low']
    elif hardening_index >= 40:
        score_color = COLORS['high']
    else:
        score_color = COLORS['critical']
    
    print(f"\n  {COLORS['bold']}Security Score:{COLORS['reset']} {score_color}{hardening_index}/100{COLORS['reset']} ({status})")
    print()

def main():
    print_banner()
    
    # Load sample scan data
    scan_dir = Path('scans/completed/20260202_101443_scan_fcd64093')
    
    if not scan_dir.exists():
        print(f"{COLORS['critical']}Error: No sample scan data found{COLORS['reset']}")
        print("Please run a scan first")
        return
    
    # Load and parse data
    with open(scan_dir / 'lynis_raw_output.txt', 'r') as f:
        raw_output = f.read()
    
    parser = LynisParser()
    parsed = parser.parse(raw_output)
    formatted = parser.format_for_display(parsed)
    
    # Display human-readable output
    print_severity_summary(
        formatted['severity_summary'],
        formatted['risk_summary']
    )
    
    print_system_info(
        formatted['system_info'],
        formatted['score']
    )
    
    print_top_findings(formatted['findings'])
    
    # Show PDF generation capability
    print(f"{COLORS['bold']}📄 PDF REPORT GENERATION{COLORS['reset']}\n")
    print(f"  {COLORS['green']}✓{COLORS['reset']} Professional PDF reports available")
    print(f"  {COLORS['green']}✓{COLORS['reset']} Human-readable format for non-technical users")
    print(f"  {COLORS['green']}✓{COLORS['reset']} Executive summaries and recommendations")
    print(f"  {COLORS['green']}✓{COLORS['reset']} Download via: /api/scans/<scan_id>/pdf")
    print()
    
    # Show dashboard features
    print(f"{COLORS['bold']}🎨 DASHBOARD FEATURES{COLORS['reset']}\n")
    print(f"  {COLORS['green']}✓{COLORS['reset']} Color-coded severity indicators")
    print(f"  {COLORS['green']}✓{COLORS['reset']} Interactive severity badges")
    print(f"  {COLORS['green']}✓{COLORS['reset']} PDF download buttons in history tables")
    print(f"  {COLORS['green']}✓{COLORS['reset']} Detailed finding cards with severity labels")
    print()
    
    print(f"{COLORS['bold']}{COLORS['green']}✨ All features implemented successfully!{COLORS['reset']}\n")
    print(f"{COLORS['bold']}{'='*70}{COLORS['reset']}")

if __name__ == '__main__':
    main()
