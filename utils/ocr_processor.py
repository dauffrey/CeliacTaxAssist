import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import io
import imghdr
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class ItemPrice:
    item_name: str
    original_price: float
    discount: Optional[float] = None
    final_price: Optional[float] = None

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

def get_items_with_prices(text: str) -> List[ItemPrice]:
    """
    Extract items with their prices, including discounts
    Returns a list of ItemPrice objects
    """
    items = []
    
    # Pattern to match item with price and optional discount
    # Format examples:
    # "Item Name: $XX.XX"
    # "Item Name: $XX.XX (with XX% discount: -$X.XX)"
    item_pattern = r'([^:\n]+):\s*\$(\d+[.,]\d{2})(?:\s*\(with\s+(\d+)%\s+discount:\s*-\$(\d+[.,]\d{2})\))?'
    
    matches = re.finditer(item_pattern, text)
    
    for match in matches:
        item_name = match.group(1).strip()
        original_price = float(match.group(2).replace(',', '.'))
        
        # Check if there's a discount
        if match.group(3) and match.group(4):
            discount = float(match.group(4).replace(',', '.'))
            final_price = original_price - discount
        else:
            discount = None
            final_price = original_price
            
        items.append(ItemPrice(
            item_name=item_name,
            original_price=original_price,
            discount=discount,
            final_price=final_price
        ))
    
    return items

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
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        # Get items with prices
        items = get_items_with_prices(text)
        
        if not items:
            # Fallback to simple price detection if no structured items found
            price_pattern = r'\$\s*\d+[.,]\d{2}'
            prices = re.findall(price_pattern, text)
            
            if not prices:
                # Try alternative pattern without $ symbol
                alt_pattern = r'\b\d+[.,]\d{2}\b'
                prices = re.findall(alt_pattern, text)
            
            # Clean and convert prices to float
            cleaned_prices = []
            for price in prices:
                clean_price = float(price.replace('$', '').replace(' ', '').replace(',', '.'))
                if clean_price > 0:  # Only include positive prices
                    cleaned_prices.append(clean_price)
            
            return cleaned_prices if cleaned_prices else None
        
        # Return final prices from structured items
        return [item.final_price for item in items if item.final_price > 0]
        
    except Exception as e:
        raise Exception(f"Error processing receipt: {str(e)}")

def get_highest_prices(prices: Optional[List[float]], num_prices: int = 2) -> Tuple[Optional[float], Optional[float]]:
    """
    Get the highest prices from the list
    Usually the higher price would be GF and lower would be regular
    """
    if not prices or len(prices) < num_prices:
        return None, None
    
    # Sort prices and remove duplicates
    unique_sorted_prices = sorted(set(prices), reverse=True)
    
    if len(unique_sorted_prices) < num_prices:
        return None, None
    
    return unique_sorted_prices[0], unique_sorted_prices[1]
