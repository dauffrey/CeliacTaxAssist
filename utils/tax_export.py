import csv
import json
from datetime import datetime
import io

def generate_turbotax_csv(products, calculations):
    """Generate CSV file compatible with TurboTax import format"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Description', 'Regular Price', 'GF Price', 'Difference', 'Category'])
    
    # Write product data
    for product in products:
        writer.writerow([
            product['date_added'].strftime('%m/%d/%Y'),
            product['product_name'],
            f"{float(product['regular_price']):.2f}",
            f"{float(product['gf_price']):.2f}",
            f"{float(product['difference']):.2f}",
            'Medical Expenses - Gluten Free Products'
        ])
    
    # Write summary
    writer.writerow([])
    writer.writerow(['Summary', '', '', '', ''])
    writer.writerow(['Total Extra Cost', '', '', '', f"{float(calculations['total_difference']):.2f}"])
    writer.writerow(['Estimated Tax Credit', '', '', '', f"{float(calculations['estimated_tax_credit']):.2f}"])
    
    return output.getvalue()

def generate_quicken_qif(products):
    """Generate QIF file for Quicken import"""
    output = []
    
    # QIF header
    output.append('!Type:Expenses')
    
    # Add each product as a transaction
    for product in products:
        output.extend([
            'D' + product['date_added'].strftime('%m/%d/%Y'),
            'P' + product['product_name'],
            'T' + f"{float(product['difference']):.2f}",
            'LMedical:Celiac Disease:Gluten Free Products',
            'MMedical expense - GF product price difference',
            '^'
        ])
    
    return '\n'.join(output)

def generate_json_export(products, calculations):
    """Generate detailed JSON export"""
    export_data = {
        'products': [
            {
                'date': product['date_added'].strftime('%Y-%m-%d'),
                'name': product['product_name'],
                'regular_price': float(product['regular_price']),
                'gf_price': float(product['gf_price']),
                'difference': float(product['difference'])
            }
            for product in products
        ],
        'summary': {
            'total_difference': float(calculations['total_difference']),
            'product_count': calculations['product_count'],
            'average_difference': float(calculations['average_difference']),
            'estimated_tax_credit': float(calculations['estimated_tax_credit'])
        },
        'metadata': {
            'export_date': datetime.now().strftime('%Y-%m-%d'),
            'currency': 'USD'
        }
    }
    
    return json.dumps(export_data, indent=2)
