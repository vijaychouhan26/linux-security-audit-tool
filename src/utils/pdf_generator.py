#!/usr/bin/env python3
"""
PDF Report Generator for Security Audit Results
Generates human-readable PDF reports from Lynis scan results.
"""

import io
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PDFReportGenerator:
    """
    Generate professional PDF reports from security scan results.
    """
    
    # Color scheme for severity levels
    SEVERITY_COLORS = {
        'critical': colors.HexColor('#DC2626'),  # Red
        'high': colors.HexColor('#EA580C'),      # Orange
        'medium': colors.HexColor('#D97706'),    # Amber
        'low': colors.HexColor('#0891B2'),       # Cyan
        'info': colors.HexColor('#64748B'),      # Gray
    }
    
    def __init__(self):
        """Initialize the PDF generator"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is not installed. Install it with: pip install reportlab")
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#475569'),
            spaceAfter=20,
            fontName='Helvetica-Bold'
        ))
        
        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderColor=colors.HexColor('#E2E8F0'),
            borderPadding=5,
        ))
        
        # Severity label
        self.styles.add(ParagraphStyle(
            name='SeverityLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
    
    def generate_report(self, scan_data: Dict[str, Any], output_path: Optional[Path] = None) -> bytes:
        """
        Generate a PDF report from scan data.
        
        Args:
            scan_data: Dictionary containing scan results and metadata
            output_path: Optional path to save the PDF file
        
        Returns:
            PDF file as bytes
        """
        # Create a buffer for the PDF
        buffer = io.BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        # Build the document content
        story = []
        
        # Add header
        story.extend(self._create_header(scan_data))
        
        # Add executive summary
        story.extend(self._create_executive_summary(scan_data))
        
        # Add severity overview
        story.extend(self._create_severity_overview(scan_data))
        
        # Add system information
        story.extend(self._create_system_info(scan_data))
        
        # Add security score
        story.extend(self._create_security_score(scan_data))
        
        # Add findings by severity
        story.extend(self._create_findings_section(scan_data))
        
        # Add recommendations
        story.extend(self._create_recommendations(scan_data))
        
        # Add footer
        story.extend(self._create_footer(scan_data))
        
        # Build the PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Optionally save to file
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
        
        return pdf_bytes
    
    def _create_header(self, scan_data: Dict[str, Any]) -> List:
        """Create the report header"""
        elements = []
        
        # Title
        title = Paragraph(
            "Linux Security Audit Report",
            self.styles['CustomTitle']
        )
        elements.append(title)
        
        # Scan ID and timestamp
        scan_id = scan_data.get('scan_id', 'Unknown')
        timestamp = scan_data.get('completed_at', scan_data.get('timestamp', 'Unknown'))
        
        if timestamp and timestamp != 'Unknown':
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%B %d, %Y at %I:%M %p')
            except:
                formatted_time = timestamp
        else:
            formatted_time = 'Unknown'
        
        subtitle = Paragraph(
            f"Scan ID: {scan_id}<br/>Generated: {formatted_time}",
            self.styles['CustomSubtitle']
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_executive_summary(self, scan_data: Dict[str, Any]) -> List:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Get parsed results
        parsed_results = scan_data.get('parsed_results', {})
        severity_summary = parsed_results.get('severity_summary', {})
        risk_summary = parsed_results.get('risk_summary', 'No summary available')
        
        # Create summary text
        critical = severity_summary.get('critical', 0)
        high = severity_summary.get('high', 0)
        medium = severity_summary.get('medium', 0)
        low = severity_summary.get('low', 0)
        
        summary_text = f"""
        <b>Overall Assessment:</b> {risk_summary}<br/><br/>
        
        This security audit identified a total of <b>{critical + high + medium + low}</b> findings 
        across different severity levels. The findings include configuration issues, missing security 
        controls, and recommendations for hardening the system.<br/><br/>
        
        <b>Priority Actions:</b><br/>
        """
        
        if critical > 0:
            summary_text += f"• <b style='color: #DC2626;'>CRITICAL:</b> {critical} issues require immediate attention<br/>"
        if high > 0:
            summary_text += f"• <b style='color: #EA580C;'>HIGH:</b> {high} issues should be addressed soon<br/>"
        if medium > 0:
            summary_text += f"• <b style='color: #D97706;'>MEDIUM:</b> {medium} issues for planned remediation<br/>"
        if low > 0:
            summary_text += f"• <b style='color: #0891B2;'>LOW:</b> {low} minor improvements recommended<br/>"
        
        elements.append(Paragraph(summary_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_severity_overview(self, scan_data: Dict[str, Any]) -> List:
        """Create severity overview table"""
        elements = []
        
        elements.append(Paragraph("Security Findings Overview", self.styles['SectionHeader']))
        
        parsed_results = scan_data.get('parsed_results', {})
        severity_summary = parsed_results.get('severity_summary', {})
        
        # Create data for table
        data = [
            ['Severity Level', 'Count', 'Description'],
            [
                'CRITICAL',
                str(severity_summary.get('critical', 0)),
                'Requires immediate action'
            ],
            [
                'HIGH',
                str(severity_summary.get('high', 0)),
                'Should be addressed soon'
            ],
            [
                'MEDIUM',
                str(severity_summary.get('medium', 0)),
                'Plan for remediation'
            ],
            [
                'LOW',
                str(severity_summary.get('low', 0)),
                'Minor improvements'
            ],
        ]
        
        # Create table
        table = Table(data, colWidths=[1.5*inch, 1*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_system_info(self, scan_data: Dict[str, Any]) -> List:
        """Create system information section"""
        elements = []
        
        elements.append(Paragraph("System Information", self.styles['SectionHeader']))
        
        parsed_results = scan_data.get('parsed_results', {})
        system_info = parsed_results.get('system_info', {})
        
        # Create data for table
        data = [
            ['Property', 'Value'],
            ['Operating System', system_info.get('os_name', 'Unknown')],
            ['OS Version', system_info.get('os_version', 'Unknown')],
            ['Kernel Version', system_info.get('kernel_version', 'Unknown')],
            ['Hostname', system_info.get('hostname', 'Unknown')],
            ['Hardware Platform', system_info.get('hardware_platform', 'Unknown')],
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_security_score(self, scan_data: Dict[str, Any]) -> List:
        """Create security score section"""
        elements = []
        
        parsed_results = scan_data.get('parsed_results', {})
        score = parsed_results.get('score', {})
        stats = parsed_results.get('statistics', {})
        
        hardening_index = score.get('hardening_index', 0)
        status = score.get('status', 'unknown')
        
        elements.append(Paragraph("Security Hardening Score", self.styles['SectionHeader']))
        
        # Score description
        score_text = f"""
        <b>Hardening Index:</b> {hardening_index}/100<br/>
        <b>Status:</b> {status.upper()}<br/>
        <b>Tests Performed:</b> {stats.get('tests_performed', 0)}<br/><br/>
        
        The hardening index represents the overall security posture of the system. 
        A score of 80+ is excellent, 60-79 is good, 40-59 is fair, and below 40 requires attention.
        """
        
        elements.append(Paragraph(score_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_findings_section(self, scan_data: Dict[str, Any]) -> List:
        """Create detailed findings section"""
        elements = []
        
        parsed_results = scan_data.get('parsed_results', {})
        findings = parsed_results.get('findings', {})
        
        # Create sections for each severity level
        for severity in ['critical', 'high', 'medium', 'low']:
            severity_findings = findings.get(severity, [])
            
            if not severity_findings:
                continue
            
            # Add page break before critical and high findings for emphasis
            if severity in ['critical', 'high'] and elements:
                elements.append(PageBreak())
            
            # Section header with color
            header_text = f"{severity.upper()} Priority Findings ({len(severity_findings)})"
            elements.append(Paragraph(header_text, self.styles['SectionHeader']))
            
            # Add findings
            for idx, finding in enumerate(severity_findings[:30], 1):  # Limit to 30 per severity
                finding_elements = self._create_finding_item(finding, idx, severity)
                elements.extend(finding_elements)
            
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_finding_item(self, finding: Dict[str, Any], index: int, severity: str) -> List:
        """Create a single finding item"""
        elements = []
        
        message = finding.get('message', 'No description available')
        test_id = finding.get('test_id', '')
        details = finding.get('details', [])
        
        # Create finding box
        severity_color = self.SEVERITY_COLORS.get(severity, colors.gray)
        
        finding_data = [[
            Paragraph(f"<b>#{index}</b>", self.styles['Normal']),
            Paragraph(f"<b>{severity.upper()}</b>", self.styles['SeverityLabel']),
            Paragraph(message, self.styles['Normal'])
        ]]
        
        if test_id:
            finding_data[0].append(Paragraph(f"<i>{test_id}</i>", self.styles['Normal']))
        
        table = Table(finding_data, colWidths=[0.4*inch, 0.8*inch, 4*inch, 0.8*inch] if test_id else [0.4*inch, 0.8*inch, 4.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('TEXTCOLOR', (1, 0), (1, 0), severity_color),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1, severity_color),
        ]))
        
        elements.append(KeepTogether(table))
        
        # Add details if present
        if details:
            details_text = "<br/>".join([f"  • {d}" for d in details[:3]])
            elements.append(Paragraph(details_text, self.styles['Normal']))
        
        elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _create_recommendations(self, scan_data: Dict[str, Any]) -> List:
        """Create recommendations section"""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("Next Steps & Recommendations", self.styles['SectionHeader']))
        
        recommendations_text = """
        <b>1. Address Critical Issues Immediately</b><br/>
        Review and remediate all critical severity findings as soon as possible. 
        These represent significant security risks that could be exploited.<br/><br/>
        
        <b>2. Plan for High Priority Items</b><br/>
        Schedule time to address high severity findings within the next week. 
        These issues may not be immediately exploitable but represent important security gaps.<br/><br/>
        
        <b>3. Implement Medium Priority Fixes</b><br/>
        Include medium severity items in your regular maintenance schedule. 
        While not urgent, addressing these will improve overall security posture.<br/><br/>
        
        <b>4. Consider Low Priority Improvements</b><br/>
        Low severity findings are suggestions for best practices. 
        Implement these as time and resources allow.<br/><br/>
        
        <b>5. Schedule Regular Audits</b><br/>
        Run security audits regularly (weekly or monthly) to track improvements 
        and catch new issues early.<br/><br/>
        
        <b>6. Document Changes</b><br/>
        Keep a record of all security changes made in response to this audit 
        for compliance and future reference.<br/>
        """
        
        elements.append(Paragraph(recommendations_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_footer(self, scan_data: Dict[str, Any]) -> List:
        """Create report footer"""
        elements = []
        
        footer_text = f"""
        <br/><br/>
        ────────────────────────────────────────────────────────────────<br/>
        <i>This report was automatically generated by Linux Security Audit Tool using Lynis.<br/>
        For questions or support, consult your security team or system administrator.</i><br/>
        Report ID: {scan_data.get('scan_id', 'Unknown')}<br/>
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        footer_para = Paragraph(footer_text, self.styles['Normal'])
        elements.append(footer_para)
        
        return elements
