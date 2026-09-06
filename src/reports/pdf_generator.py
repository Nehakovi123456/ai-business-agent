import re
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib import colors
from src.config import UPLOAD_DIR

def md_to_reportlab_html(text: str) -> str:
    """Safely converts markdown bold (**), italic (*), and code (`) tags to ReportLab HTML tags."""
    if not text:
        return ""
    # Replace Rupee symbol with Rs. to prevent ReportLab Helvetica font black square glyph fallback
    text = text.replace('₹', 'Rs. ')
    # Escape raw XML special characters first
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # Convert **bold**
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Convert *italic*
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Convert `code`
    text = re.sub(r'`(.*?)`', r'<font name="Courier" color="#1D4ED8">\1</font>', text)
    return text

def generate_pdf_report(report_markdown: str, filename: str = "business_decision_report.pdf") -> str:
    """
    Converts markdown business decision report into a styled PDF document using ReportLab.
    """
    pdf_dir = UPLOAD_DIR / "pdf_reports"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / filename

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=8
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1D4ED8'),
        spaceBefore=10,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=4
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    table_body_style = ParagraphStyle(
        'TableBody',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1F2937')
    )

    story = []
    lines = report_markdown.split('\n')
    i = 0

    while i < len(lines):
        line_str = lines[i].strip()
        if not line_str:
            story.append(Spacer(1, 3))
            i += 1
            continue

        # Header 1
        if line_str.startswith('# '):
            clean_text = md_to_reportlab_html(line_str.replace('# ', '').replace('📊 ', ''))
            story.append(Paragraph(clean_text, title_style))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3A8A'), spaceAfter=8))
            i += 1
            continue

        # Header 2
        if line_str.startswith('## '):
            clean_text = md_to_reportlab_html(line_str.replace('## ', ''))
            story.append(Spacer(1, 4))
            story.append(Paragraph(clean_text, heading_style))
            i += 1
            continue

        # Header 3
        if line_str.startswith('### '):
            clean_text = md_to_reportlab_html(line_str.replace('### ', ''))
            story.append(Paragraph(f"<b>{clean_text}</b>", body_style))
            i += 1
            continue

        # Horizontal Rule
        if line_str in ['---', '***']:
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=6, spaceBefore=4))
            i += 1
            continue

        # Markdown Table Parsing
        if line_str.startswith('|'):
            table_rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                row_str = lines[i].strip()
                # Skip markdown delimiter line like | --- | --- |
                if '---' not in row_str:
                    cells = [cell.strip() for cell in row_str.split('|')[1:-1]]
                    if cells:
                        table_rows.append(cells)
                i += 1

            if table_rows:
                # Build ReportLab Table Flowable
                formatted_table_data = []
                # Header row
                header_row = [Paragraph(md_to_reportlab_html(c), table_header_style) for c in table_rows[0]]
                formatted_table_data.append(header_row)

                # Data rows
                for r in table_rows[1:]:
                    data_row = [Paragraph(md_to_reportlab_html(c), table_body_style) for c in r]
                    formatted_table_data.append(data_row)

                t = Table(formatted_table_data, hAlign='LEFT')
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(t)
                story.append(Spacer(1, 6))
            continue

        # Bullet List
        if line_str.startswith('- '):
            clean_text = md_to_reportlab_html(line_str[2:])
            story.append(Paragraph(f"• {clean_text}", body_style))
            i += 1
            continue

        # Standard Paragraph
        clean_text = md_to_reportlab_html(line_str)
        story.append(Paragraph(clean_text, body_style))
        i += 1

    try:
        doc.build(story)
        print(f"[PDF] Report successfully generated: {pdf_path}")
        return str(pdf_path)
    except Exception as e:
        print(f"[PDF] ReportLab generation error: {e}")
        return ""
