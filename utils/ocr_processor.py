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
    description: Optional[str] = None
    discount: Optional[float] = None
    final_price: Optional[float] = None
    gf_confidence: Optional[float] = None

def is_gluten_free(text: str) -> float:
    """
    Check if an item description indicates it's gluten-free
    Returns a confidence score between 0 and 1
    """
    text = text.lower()
    
    # Direct indicators (highest confidence)
    direct_indicators = ['gluten free', 'gluten-free', ' gf ', 'gf:', '(gf)']
    for indicator in direct_indicators:
        if indicator in text:
            return 1.0
            
    # Partial indicators (medium confidence)
    partial_indicators = ['gf', 'g/f', 'g-f', 'gluten']
    for indicator in partial_indicators:
        if indicator in text:
            return 0.8
            
    # Common GF product keywords (lower confidence)
    gf_keywords = ['rice', 'quinoa', 'corn', 'buckwheat', 'sorghum', 'millet']
    for keyword in gf_keywords:
        if keyword in text:
            return 0.4
            
    return 0.0

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
    Extract items with their prices and descriptions
    Returns a list of ItemPrice objects
    """
    items = []
    
    # Split text into lines for better processing
    lines = text.split('\n')
    current_item = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Pattern to match prices with optional descriptions
        price_match = re.search(r'\$\s*(\d+[.,]\d{2})', line)
        
        if price_match:
            price = float(price_match.group(1).replace(',', '.'))
            # Extract item name and description
            description = line[:price_match.start()].strip()
            if not description and current_item:
                description = current_item
            
            if description:
                # Check if it might be gluten-free
                gf_confidence = is_gluten_free(description)
                
                # Look for discount
                discount_match = re.search(r'-\$\s*(\d+[.,]\d{2})', line)
                discount = float(discount_match.group(1).replace(',', '.')) if discount_match else None
                
                final_price = price - discount if discount else price
                
                items.append(ItemPrice(
                    item_name=description.split(':')[0].strip(),
                    original_price=price,
                    description=description,
                    discount=discount,
                    final_price=final_price,
                    gf_confidence=gf_confidence
                ))
                current_item = None
        else:
            # This might be an item description without a price
            current_item = line
    
    return items

def extract_prices_from_image(image_bytes: bytes) -> Optional[List[ItemPrice]]:
    """
    Extract items and prices from receipt image using OCR
    Returns a list of ItemPrice objects or None if processing fails
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
            return None
        
        return items
        
    except Exception as e:
        raise Exception(f"Error processing receipt: {str(e)}")

def get_highest_prices(prices: Optional[List[float]], num_prices: int = 2) -> Tuple[Optional[float], Optional[float]]:
    """
    Get the highest prices from the list
    """
    if not prices or len(prices) < num_prices:
        return None, None
    
    # Sort prices and remove duplicates
    unique_sorted_prices = sorted(set(prices), reverse=True)
    
    if len(unique_sorted_prices) < num_prices:
        return None, None
    
    return unique_sorted_prices[0], unique_sorted_prices[1]
