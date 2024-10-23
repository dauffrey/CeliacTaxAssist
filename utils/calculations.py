import pandas as pd

def calculate_tax_credit(products):
    """Calculate the tax credit based on CRA guidelines"""
    df = pd.DataFrame(products)
    
    # Calculate total difference
    total_difference = df['difference'].sum()
    
    # CRA allows medical expense tax credit if expenses exceed 
    # lesser of $2,421 or 3% of net income (using 2021 values)
    # This is a simplified calculation
    tax_credit_rate = 0.15  # Federal tax credit rate
    
    # Convert Decimal to float before multiplication
    total_difference_float = float(total_difference)
    
    return {
        'total_difference': total_difference,
        'estimated_tax_credit': total_difference_float * tax_credit_rate,
        'product_count': len(df),
        'average_difference': float(df['difference'].mean() if not df.empty else 0)
    }
