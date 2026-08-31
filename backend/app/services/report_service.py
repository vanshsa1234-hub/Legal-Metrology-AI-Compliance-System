"""
Legal Lens - PDF Report Generation Service using ReportLab
Generates official, government-grade compliance inspection reports.
"""
import os
import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header line
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 800, 555, 800)
        self.drawString(40, 805, "LEGAL LENS — AI-Assisted Product Inspection & Compliance System")
        self.drawRightString(555, 805, "CONFIDENTIAL / STATUTORY INSPECTION RECORD")
        
        # Footer line
        self.line(40, 45, 555, 45)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(555, 32, page_text)
        self.drawString(40, 32, f"Generated on {datetime.datetime.utcnow().strftime('%d-%b-%Y %H:%M:%S UTC')} | Official Verification Copy")
        self.restoreState()

class ReportService:
    @staticmethod
    def generate_inspection_pdf(
        report_code: str,
        inspection,
        product,
        declarations,
        compliance_results,
        output_dir: str
    ) -> str:
        """
        Build an official PDF compliance report.
        """
        os.makedirs(output_dir, exist_ok=True)
        pdf_filename = f"{report_code}.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=55,
            bottomMargin=55
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0f172a')
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#2563eb')
        )
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#1e3a8a'),
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#334155')
        )
        bold_label = ParagraphStyle(
            'BoldLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#0f172a')
        )
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#64748b')
        )

        story = []

        # 1. Header Banner
        header_data = [
            [
                Paragraph("<b>LEGAL LENS</b><br/><font color='#2563eb' size='9'>AI-Assisted Consumer Compliance & Inspection Platform</font>", title_style),
                Paragraph(f"<b>REPORT ID:</b> {report_code}<br/><b>INSPECTION ID:</b> {inspection.inspection_code}<br/><b>DATE:</b> {inspection.created_at.strftime('%d-%b-%Y %H:%M')}", body_style)
            ]
        ]
        header_table = Table(header_data, colWidths=[315, 200])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceBefore=2, spaceAfter=10))

        # 2. Executive Summary / Overall Result Banner
        status_bg = colors.HexColor('#fee2e2') if 'NON-COMPLIANCE' in inspection.overall_result.upper() else colors.HexColor('#fef3c7') if 'REVIEW' in inspection.overall_result.upper() else colors.HexColor('#dcfce7')
        status_text_color = colors.HexColor('#991b1b') if 'NON-COMPLIANCE' in inspection.overall_result.upper() else colors.HexColor('#92400e') if 'REVIEW' in inspection.overall_result.upper() else colors.HexColor('#166534')

        summary_data = [
            [
                Paragraph("<b>OVERALL COMPLIANCE STATUS:</b>", ParagraphStyle('SumH', parent=bold_label, fontSize=10, textColor=status_text_color)),
                Paragraph(f"<b>{inspection.overall_result.upper()}</b>", ParagraphStyle('SumVal', parent=bold_label, fontSize=11, textColor=status_text_color))
            ],
            [
                Paragraph(f"<b>Rules Checked:</b> {inspection.rules_checked_count} &nbsp;|&nbsp; <b>No Issue:</b> {inspection.no_issue_count} &nbsp;|&nbsp; <b>Review Required:</b> {inspection.review_required_count} &nbsp;|&nbsp; <b>Potential Issues:</b> {inspection.non_compliance_count}", body_style),
                Paragraph(f"<b>Confidence:</b> {inspection.confidence_score:.1f}% &nbsp;|&nbsp; <b>Officer Status:</b> {inspection.officer_review_status}", body_style)
            ]
        ]
        summary_table = Table(summary_data, colWidths=[260, 255])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), status_bg),
            ('BOX', (0, 0), (-1, -1), 1, status_text_color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 10))

        # 3. Product Details Section
        story.append(Paragraph("1. PRODUCT IDENTIFICATION & METADATA", section_heading))
        
        prod_name = product.product_name if product else (inspection.product_name or "N/A")
        brand = product.brand if product else (inspection.brand or "N/A")
        category = product.category if product else (inspection.category or "Packaged Food")
        barcode = inspection.barcode or (product.barcode if product else "N/A")
        mrp = product.mrp if product else "N/A"
        net_qty = product.net_quantity if product else "N/A"
        mfg_date = product.mfg_date if product else "N/A"
        best_before = product.best_before if product else "N/A"
        batch = product.batch_number if product else "N/A"
        mfg_address = product.manufacturer if product else "N/A"
        fssai = product.fssai_license if product else "N/A"
        veg = product.veg_non_veg if product else "Vegetarian"

        prod_data = [
            [Paragraph("<b>Product Name:</b>", bold_label), Paragraph(str(prod_name), body_style), Paragraph("<b>Brand:</b>", bold_label), Paragraph(str(brand), body_style)],
            [Paragraph("<b>Barcode / EAN:</b>", bold_label), Paragraph(str(barcode), body_style), Paragraph("<b>Category:</b>", bold_label), Paragraph(str(category), body_style)],
            [Paragraph("<b>Declared MRP:</b>", bold_label), Paragraph(str(mrp), body_style), Paragraph("<b>Net Quantity:</b>", bold_label), Paragraph(str(net_qty), body_style)],
            [Paragraph("<b>Batch Number:</b>", bold_label), Paragraph(str(batch), body_style), Paragraph("<b>Mfg / Pkg Date:</b>", bold_label), Paragraph(str(mfg_date), body_style)],
            [Paragraph("<b>Best Before:</b>", bold_label), Paragraph(str(best_before), body_style), Paragraph("<b>Veg / Non-Veg:</b>", bold_label), Paragraph(str(veg), body_style)],
            [Paragraph("<b>FSSAI License:</b>", bold_label), Paragraph(str(fssai), body_style), Paragraph("<b>Manufacturer:</b>", bold_label), Paragraph(str(mfg_address)[:45], body_style)],
        ]
        prod_table = Table(prod_data, colWidths=[100, 155, 95, 165])
        prod_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f8fafc')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(prod_table)
        story.append(Spacer(1, 10))

        # 4. Extracted Declarations & Evidence Table
        story.append(Paragraph("2. AI EXTRACTED DECLARATIONS (EVIDENCE-FIRST MAPPING)", section_heading))
        dec_headers = [
            Paragraph("<b>Mandatory Field</b>", bold_label),
            Paragraph("<b>Detected Value</b>", bold_label),
            Paragraph("<b>Confidence</b>", bold_label),
            Paragraph("<b>Source</b>", bold_label)
        ]
        dec_rows = [dec_headers]
        for d in declarations[:8]:
            conf_badge = f"{d.confidence:.1f}% ({d.confidence_level})"
            dec_rows.append([
                Paragraph(f"<b>{d.field_name}</b>", body_style),
                Paragraph(str(d.detected_value)[:80], body_style),
                Paragraph(conf_badge, body_style),
                Paragraph(f"{d.evidence_image_type.capitalize()} Image", body_style)
            ])

        dec_table = Table(dec_rows, colWidths=[130, 235, 80, 70])
        dec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(dec_table)
        story.append(Spacer(1, 10))

        # 5. Rule-by-Rule Compliance Evaluation Table
        story.append(Paragraph("3. STATUTORY RULE COMPLIANCE EVALUATION", section_heading))
        rule_headers = [
            Paragraph("<b>Rule & Reg</b>", bold_label),
            Paragraph("<b>Requirement / Finding</b>", bold_label),
            Paragraph("<b>Result</b>", bold_label),
            Paragraph("<b>Evidence</b>", bold_label)
        ]
        rule_rows = [rule_headers]
        for r in compliance_results:
            status_style = ParagraphStyle(
                'ResStatus',
                parent=bold_label,
                fontSize=8,
                textColor=colors.HexColor('#b91c1c') if 'NON-COMPLIANCE' in r.status else colors.HexColor('#b45309') if 'REVIEW' in r.status else colors.HexColor('#15803d')
            )
            rule_info = f"<b>{r.rule_id}</b><br/><font size='7.5' color='#64748b'>{r.clause or ''}</font>"
            finding_info = f"<b>{r.rule_title}</b><br/>{r.reason}"
            rule_rows.append([
                Paragraph(rule_info, body_style),
                Paragraph(finding_info, body_style),
                Paragraph(f"<b>{r.status}</b><br/><font size='7.5' color='#64748b'>{r.confidence:.0f}% Conf</font>", status_style),
                Paragraph(r.evidence_type, body_style)
            ])

        rule_table = Table(rule_rows, colWidths=[100, 255, 100, 60])
        rule_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(rule_table)
        story.append(Spacer(1, 10))

        # 6. Officer Human-in-the-Loop Review & Remarks Box
        story.append(Paragraph("4. ENFORCEMENT OFFICER VERIFICATION & ACTION", section_heading))
        officer_text = inspection.officer_remarks or "Pending Officer Review and field inspection scheduling."
        officer_data = [
            [
                Paragraph(f"<b>Officer Status:</b> {inspection.officer_review_status}", bold_label),
                Paragraph("<b>Officer Seal & Signature:</b>", bold_label)
            ],
            [
                Paragraph(f"<b>Officer Remarks / Notes:</b><br/>{officer_text}", body_style),
                Paragraph("<br/><br/>_______________________________<br/><font size='7.5' color='#64748b'>Designated Metrology Officer</font>", body_style)
            ]
        ]
        officer_table = Table(officer_data, colWidths=[330, 185])
        officer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#94a3b8')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(KeepTogether([officer_table]))
        story.append(Spacer(1, 12))

        # 7. Official Legal Disclaimer
        disclaimer_text = (
            "<b>STATUTORY DISCLAIMER:</b> This automated compliance screening report is generated by Legal Lens "
            "as an AI-assisted decision support tool under the Legal Metrology (Packaged Commodities) Rules and FSSAI Regulations. "
            "It does not constitute a final legal adjudication or penalty. All flagged issues represent potential non-compliances "
            "subject to mandatory statutory verification, lab sample testing, and formal hearing by authorized enforcement officers."
        )
        story.append(Paragraph(disclaimer_text, disclaimer_style))

        # Build document with NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)
        return pdf_path
