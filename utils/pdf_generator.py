from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io

def generate_tax_report(products, calculations):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Add title
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Celiac Tax Credit Report", styles['Title']))
    
    # Add summary
    summary_data = [
        ["Total Extra Cost", f"${calculations['total_difference']:.2f}"],
        ["Estimated Tax Credit", f"${calculations['estimated_tax_credit']:.2f}"],
        ["Number of Products", str(calculations['product_count'])],
        ["Average Price Difference", f"${calculations['average_difference']:.2f}"]
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
