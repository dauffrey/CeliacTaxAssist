import pytesseract
from PIL import Image
import re
import io

def extract_prices_from_image(image_bytes):
    """
    Extract prices from receipt image using OCR
    Returns a list of detected prices
    """
    # Convert bytes to image
    image = Image.open(io.BytesIO(image_bytes))
    
    # Extract text from image
    text = pytesseract.image_to_string(image)
    
    # Find all price patterns ($XX.XX or $XX,XX)
    price_pattern = r'\$\s*\d+[.,]\d{2}'
    prices = re.findall(price_pattern, text)
    
    # Clean and convert prices to float
    cleaned_prices = []
    for price in prices:
        # Remove $ and whitespace, replace comma with period
        clean_price = float(price.replace('$', '').replace(' ', '').replace(',', '.'))
        cleaned_prices.append(clean_price)
    
    return cleaned_prices

def get_highest_prices(prices, num_prices=2):
    """
    Get the highest prices from the list
    Usually the higher price would be GF and lower would be regular
    """
    if len(prices) < num_prices:
        return None, None
    
    sorted_prices = sorted(prices, reverse=True)
    return sorted_prices[0], sorted_prices[1]
