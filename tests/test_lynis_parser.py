"""
Tests for Lynis output parser.
"""

import pytest
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.lynis_parser import LynisParser


@pytest.fixture
def parser():
    """Create a parser instance."""
    return LynisParser()


@pytest.fixture
def sample_lynis_output():
    """Load sample Lynis output if available."""
    sample_file = project_root / "scans" / "completed" / "20260202_101443_scan_fcd64093" / "lynis_raw_output.txt"
    if sample_file.exists():
        with open(sample_file, 'r') as f:
            return f.read()
    return None


def test_parser_initialization(parser):
    """Test parser initializes with correct constants."""
    assert parser.MAX_WARNINGS_DISPLAY == 10
    assert parser.MAX_SUGGESTIONS_DISPLAY == 20
    assert parser.OUTPUT_PREVIEW_LENGTH == 2000
    assert parser.ansi_escape is not None


def test_strip_ansi_codes(parser):
    """Test ANSI code stripping."""
    test_cases = [
        ("\x1b[1;33mWarning\x1b[0m", "Warning"),
        ("\x1b[0mNormal text", "Normal text"),
        ("No ANSI codes", "No ANSI codes"),
        ("\x1b[31mRed\x1b[0m and \x1b[32mGreen\x1b[0m", "Red and Green"),
    ]
    
    for input_text, expected in test_cases:
        result = parser.strip_ansi_codes(input_text)
        assert result == expected
        assert "\x1b" not in result


def test_parse_summary(parser, sample_lynis_output):
    """Test summary parsing."""
    if not sample_lynis_output:
        pytest.skip("Sample Lynis output not available")
    
    parsed = parser.parse(sample_lynis_output)
    summary = parsed['summary']
    
    assert 'hardening_index' in summary
    assert 'tests_performed' in summary
    assert 'plugins_enabled' in summary
    assert isinstance(summary['hardening_index'], int)
    assert summary['hardening_index'] >= 0
    assert summary['hardening_index'] <= 100


def test_parse_warnings(parser, sample_lynis_output):
    """Test warnings parsing."""
    if not sample_lynis_output:
        pytest.skip("Sample Lynis output not available")
    
    parsed = parser.parse(sample_lynis_output)
    warnings = parsed['warnings']
    
    assert isinstance(warnings, list)
    for warning in warnings:
        assert 'type' in warning
        assert 'message' in warning
        assert warning['type'] == 'warning'


def test_parse_suggestions(parser, sample_lynis_output):
    """Test suggestions parsing."""
    if not sample_lynis_output:
        pytest.skip("Sample Lynis output not available")
    
    parsed = parser.parse(sample_lynis_output)
    suggestions = parsed['suggestions']
    
    assert isinstance(suggestions, list)
    for suggestion in suggestions:
        assert 'message' in suggestion
        assert 'test_id' in suggestion
        assert 'details' in suggestion


def test_parse_system_info(parser, sample_lynis_output):
    """Test system info parsing."""
    if not sample_lynis_output:
        pytest.skip("Sample Lynis output not available")
    
    parsed = parser.parse(sample_lynis_output)
    system_info = parsed['system_info']
    
    assert 'os_name' in system_info
    assert 'os_version' in system_info
    assert 'kernel_version' in system_info
    assert 'hostname' in system_info
    assert 'hardware_platform' in system_info


def test_parse_security_components(parser, sample_lynis_output):
    """Test security components parsing."""
    if not sample_lynis_output:
        pytest.skip("Sample Lynis output not available")
    
    parsed = parser.parse(sample_lynis_output)
    components = parsed['security_components']
    
    assert 'firewall' in components
    assert 'intrusion_software' in components
    assert 'malware_scanner' in components
    assert isinstance(components['firewall'], bool)
    assert isinstance(components['intrusion_software'], bool)
    assert isinstance(components['malware_scanner'], bool)


def test_format_for_display(parser, sample_lynis_output):
    """Test formatting for dashboard display."""
    if not sample_lynis_output:
        pytest.skip("Sample Lynis output not available")
    
    parsed = parser.parse(sample_lynis_output)
    formatted = parser.format_for_display(parsed)
    
    # Check main structure
    assert 'score' in formatted
    assert 'statistics' in formatted
    assert 'system_info' in formatted
    assert 'security_components' in formatted
    assert 'findings' in formatted
    
    # Check score
    score = formatted['score']
    assert 'hardening_index' in score
    assert 'display' in score
    assert 'status' in score
    assert score['status'] in ['excellent', 'good', 'fair', 'poor']
    
    # Check statistics
    stats = formatted['statistics']
    assert 'tests_performed' in stats
    assert 'warnings_count' in stats
    assert 'suggestions_count' in stats
    assert 'plugins_enabled' in stats
    
    # Check findings
    findings = formatted['findings']
    assert 'warnings' in findings
    assert 'suggestions' in findings
    assert len(findings['warnings']) <= parser.MAX_WARNINGS_DISPLAY
    assert len(findings['suggestions']) <= parser.MAX_SUGGESTIONS_DISPLAY


def test_get_score_status(parser):
    """Test score status classification."""
    assert parser._get_score_status(90) == 'excellent'
    assert parser._get_score_status(80) == 'excellent'
    assert parser._get_score_status(70) == 'good'
    assert parser._get_score_status(60) == 'good'
    assert parser._get_score_status(50) == 'fair'
    assert parser._get_score_status(40) == 'fair'
    assert parser._get_score_status(30) == 'poor'
    assert parser._get_score_status(0) == 'poor'


def test_parse_with_empty_output(parser):
    """Test parser handles empty output gracefully."""
    parsed = parser.parse("")
    
    assert 'summary' in parsed
    assert 'warnings' in parsed
    assert 'suggestions' in parsed
    assert 'system_info' in parsed
    assert 'security_components' in parsed


def test_strip_ansi_preserves_content(parser):
    """Test that stripping ANSI codes preserves actual content."""
    text_with_ansi = "\x1b[1;31mError:\x1b[0m Something went wrong on line \x1b[33m42\x1b[0m"
    clean = parser.strip_ansi_codes(text_with_ansi)
    
    assert "Error:" in clean
    assert "Something went wrong on line" in clean
    assert "42" in clean
    assert "\x1b" not in clean
