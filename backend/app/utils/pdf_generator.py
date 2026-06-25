"""
PDF Report Generation Utility
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generate PDF reports for diagnosis results"""
    
    @staticmethod
    def generate_diagnosis_report(
        diagnosis_data: Dict[str, Any],
        remediation_data: Optional[Dict[str, Any]] = None,
        user_data: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ) -> BytesIO:
        """
        Generate a comprehensive PDF report
        
        Args:
            diagnosis_data: Diagnosis information
            treatment_data: Treatment recommendations
            user_data: User information
            language: Report language
        
        Returns:
            BytesIO buffer containing PDF
        """
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2E7D32'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#1976D2'),
                spaceAfter=12,
                spaceBefore=12
            )
            
            normal_style = styles['Normal']
            
            # Title
            title = Paragraph("Crop Disease Diagnosis Report", title_style)
            story.append(title)
            story.append(Spacer(1, 0.3 * inch))
            
            # Report metadata
            metadata_data = [
                ['Report Date:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')],
                ['Report ID:', diagnosis_data.get('id', 'N/A')],
            ]
            
            if user_data:
                metadata_data.append(['Farmer Name:', user_data.get('name', 'N/A')])
            
            metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
            metadata_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(metadata_table)
            story.append(Spacer(1, 0.3 * inch))
            
            # Diagnosis Results
            story.append(Paragraph("Diagnosis Results", heading_style))
            
            diagnosis_info = [
                ['Crop Type:', diagnosis_data.get('crop_type', 'N/A')],
                ['Disease Detected:', diagnosis_data.get('disease_name', 'N/A')],
                ['Confidence Score:', f"{diagnosis_data.get('confidence', 0) * 100:.2f}%"],
                ['Severity Level:', diagnosis_data.get('severity', 'N/A').upper()],
                ['Analysis Date:', diagnosis_data.get('created_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')],
            ]
            
            diagnosis_table = Table(diagnosis_info, colWidths=[2*inch, 4*inch])
            diagnosis_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FFF3E0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(diagnosis_table)
            story.append(Spacer(1, 0.3 * inch))
            
            # Images
            PDFReportGenerator._add_image_section(
                story,
                heading_style,
                "Captured Image",
                diagnosis_data.get("image_url")
            )
            PDFReportGenerator._add_image_section(
                story,
                heading_style,
                "Heatmap",
                diagnosis_data.get("heatmap_url")
            )

            # Remediation Content
            if remediation_data:
                description = remediation_data.get("description")
                if description:
                    story.append(Paragraph("Disease Overview", heading_style))
                    story.append(Paragraph(description, normal_style))
                    story.append(Spacer(1, 0.2 * inch))

                severity_guidance = remediation_data.get("severity_guidance")
                if severity_guidance:
                    story.append(Paragraph("Severity Guidance", heading_style))
                    story.append(Paragraph(severity_guidance, normal_style))
                    story.append(Spacer(1, 0.2 * inch))

                for label, treatment_key in [
                    ("Organic Treatment", "organic_treatment"),
                    ("Chemical Treatment", "chemical_treatment"),
                ]:
                    treatment_data = remediation_data.get(treatment_key)
                    if not treatment_data or not treatment_data.get("steps"):
                        continue

                    story.append(Paragraph(label, heading_style))
                    treatment_type = treatment_data.get("type", "")
                    if treatment_type:
                        story.append(Paragraph(f"<b>Treatment Type:</b> {treatment_type.upper()}", normal_style))
                    story.append(Spacer(1, 0.1 * inch))

                    steps = treatment_data.get("steps", [])
                    if steps:
                        story.append(Paragraph("<b>Treatment Steps:</b>", normal_style))
                        for i, step in enumerate(steps, 1):
                            step_text = f"{i}. {step.get('description', 'N/A')}"
                            if step.get("safety_warning"):
                                step_text += f" <font color='red'><b>⚠ {step['safety_warning']}</b></font>"
                            story.append(Paragraph(step_text, normal_style))
                            story.append(Spacer(1, 0.05 * inch))

                    if treatment_data.get("dosage"):
                        story.append(Spacer(1, 0.1 * inch))
                        story.append(Paragraph(f"<b>Dosage:</b> {treatment_data['dosage']}", normal_style))

                    if treatment_data.get("frequency"):
                        story.append(Paragraph(f"<b>Frequency:</b> {treatment_data['frequency']}", normal_style))

                    if treatment_data.get("cost_estimate"):
                        story.append(Paragraph(f"<b>Cost Estimate:</b> {treatment_data['cost_estimate']}", normal_style))

                    story.append(Spacer(1, 0.3 * inch))

                prevention_tips = remediation_data.get("prevention_tips", [])
                if prevention_tips:
                    story.append(Paragraph("Prevention Tips", heading_style))
                    for i, tip in enumerate(prevention_tips, 1):
                        story.append(Paragraph(f"{i}. {tip}", normal_style))
                        story.append(Spacer(1, 0.05 * inch))

                community_tips = remediation_data.get("community_tips", [])
                if community_tips:
                    story.append(Paragraph("Community Tips", heading_style))
                    for i, tip in enumerate(community_tips, 1):
                        story.append(Paragraph(f"{i}. {tip}", normal_style))
                        story.append(Spacer(1, 0.05 * inch))
            
            # Safety warnings
            story.append(Spacer(1, 0.3 * inch))
            warning_text = """
            <font color='red'><b>SAFETY WARNINGS:</b></font><br/>
            • Always wear protective equipment when applying chemicals<br/>
            • Follow dosage instructions carefully<br/>
            • Do not exceed recommended application frequency<br/>
            • Keep away from water sources and livestock<br/>
            • Consult an agricultural expert for severe cases
            """
            story.append(Paragraph(warning_text, normal_style))
            
            # Footer
            story.append(Spacer(1, 0.5 * inch))
            footer_text = """
            <i>This report is generated automatically by the Crop Disease Detection System. 
            For best results, consult with a local agricultural extension officer.</i>
            """
            story.append(Paragraph(footer_text, normal_style))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise

    @staticmethod
    def _add_image_section(
        story: list,
        heading_style: ParagraphStyle,
        title: str,
        image_url: Optional[str]
    ) -> None:
        """Add a local image to the report if available."""
        if not image_url:
            return

        file_path = PDFReportGenerator._resolve_local_path(image_url)
        if file_path is None:
            return

        try:
            image_path = str(file_path)
            story.append(Paragraph(title, heading_style))
            story.append(Spacer(1, 0.1 * inch))
            story.append(Image(image_path, width=5.5 * inch, height=3.2 * inch))
            story.append(Spacer(1, 0.2 * inch))
        except Exception as e:
            logger.error(f"Error adding image to report: {e}")

    @staticmethod
    def _resolve_local_path(image_url: str) -> Optional[Path]:
        """Resolve /uploads/... URL to local file path."""
        if not image_url:
            return None

        if image_url.startswith("/uploads/"):
            relative_path = image_url.replace("/uploads/", "")
        else:
            return None

        file_path = Path(settings.UPLOAD_DIR) / relative_path
        if not file_path.exists():
            return None

        return file_path
