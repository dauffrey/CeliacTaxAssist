import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import io
import imghdr
from typing import Tuple, List, Optional

def validate_image(image_bytes: bytes) -> Tuple[bool, str]:
    """
    Validate image format and content
    Returns: (is_valid, error_message)
    """
    try:
        # Check if it's a valid image format
        image_format = imghdr.what(None, h=image_bytes)
        if not image_format:
            return False, "Invalid image format. Please upload a valid image file."
        
        # Check if it's a supported format
        supported_formats = ['jpeg', 'jpg', 'png', 'bmp', 'tiff']
        if image_format.lower() not in supported_formats:
            return False, f"Unsupported image format: {image_format}. Please upload a JPEG, PNG, BMP, or TIFF file."
        
        # Try opening the image to verify it's not corrupted
        Image.open(io.BytesIO(image_bytes))
        return True, ""
    except Exception as e:
        return False, f"Error processing image: {str(e)}"

def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Preprocess image for better OCR results
    """
    try:
        # Convert to grayscale
        image = image.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Apply slight blur to reduce noise
        image = image.filter(ImageFilter.GaussianBlur(1))
        
        # Apply threshold to make text more clear
        image = image.point(lambda x: 0 if x < 128 else 255, '1')
        
        return image
    except Exception as e:
        raise Exception(f"Error preprocessing image: {str(e)}")

def extract_prices_from_image(image_bytes: bytes) -> Optional[List[float]]:
    """
    Extract prices from receipt image using OCR with improved handling
    Returns a list of detected prices or None if processing fails
    """
    try:
        # Validate image
        is_valid, error_message = validate_image(image_bytes)
        if not is_valid:
            raise ValueError(error_message)
        
        # Convert bytes to image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Preprocess image
        processed_image = preprocess_image(image)
        
        # Extract text from image with improved confidence
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist="0123456789,.$"'
        text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        # Find all price patterns ($XX.XX or $XX,XX)
        price_pattern = r'\$\s*\d+[.,]\d{2}'
        prices = re.findall(price_pattern, text)
        
        if not prices:
            # Try alternative pattern without $ symbol
            alt_pattern = r'\b\d+[.,]\d{2}\b'
            prices = re.findall(alt_pattern, text)
        
        # Clean and convert prices to float
        cleaned_prices = []
        for price in prices:
            # Remove $ and whitespace, replace comma with period
            clean_price = float(price.replace('$', '').replace(' ', '').replace(',', '.'))
            if clean_price > 0:  # Only include positive prices
                cleaned_prices.append(clean_price)
        
        return cleaned_prices if cleaned_prices else None
        
    except Exception as e:
        raise Exception(f"Error processing receipt: {str(e)}")

def get_highest_prices(prices: Optional[List[float]], num_prices: int = 2) -> Tuple[Optional[float], Optional[float]]:
    """
    Get the highest prices from the list
    Usually the higher price would be GF and lower would be regular
    """
    if not prices or len(prices) < num_prices:
        return None, None
    
    sorted_prices = sorted(prices, reverse=True)
    return sorted_prices[0], sorted_prices[1]
