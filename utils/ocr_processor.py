import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import io
import imghdr
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
from decimal import Decimal
import numpy as np
from fuzzywuzzy import fuzz

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
    direct_indicators = ['gluten free', 'gluten-free', ' gf ', 'gf:', '(gf)', 'g-free']
    for indicator in direct_indicators:
        if indicator in text:
            return 1.0
            
    # Partial indicators (medium confidence)
    partial_indicators = ['gf', 'g/f', 'g-f', 'gluten']
    for indicator in partial_indicators:
        if indicator in text:
            return 0.8
            
    # Common GF product keywords (lower confidence)
    gf_keywords = ['rice', 'quinoa', 'corn', 'buckwheat', 'sorghum', 'millet', 'tapioca']
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
    Enhanced preprocessing for better OCR results
    """
    try:
        # Increase resolution (2x upscaling)
        new_size = (image.width * 2, image.height * 2)
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to grayscale
        image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        # Apply denoising using median filter
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        # Apply adaptive thresholding
        image = image.point(lambda x: 0 if x < 128 else 255, '1')
        
        # Additional sharpening after threshold
        image = image.filter(ImageFilter.SHARPEN)
        
        return image
    except Exception as e:
        raise Exception(f"Error preprocessing image: {str(e)}")

def merge_multiline_items(lines: List[str]) -> List[str]:
    """
    Merge multi-line items into single lines
    """
    merged_lines = []
    current_line = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_line:
                merged_lines.append(current_line)
                current_line = ""
            continue
        
        # If line contains price, it's likely the end of an item
        if re.search(r'\$\d+\.\d{2}', line):
            if current_line:
                current_line += " " + line
                merged_lines.append(current_line)
                current_line = ""
            else:
                merged_lines.append(line)
        else:
            # If no price, it's probably part of item description
            if current_line:
                current_line += " " + line
            else:
                current_line = line
    
    # Add any remaining line
    if current_line:
        merged_lines.append(current_line)
    
    return merged_lines

def fuzzy_match_product(text: str, common_products: List[str], threshold: int = 80) -> Optional[str]:
    """
    Find closest matching product name using fuzzy matching
    """
    best_match = None
    best_score = 0
    
    for product in common_products:
        score = fuzz.ratio(text.lower(), product.lower())
        if score > threshold and score > best_score:
            best_match = product
            best_score = score
    
    return best_match

def get_items_with_prices(text: str) -> List[ItemPrice]:
    """
    Extract items with their prices and descriptions with improved handling
    """
    items = []
    common_products = [
        "Bread", "Roll", "Muffin", "Bagel", "Cereal",
        "Pasta", "Cookie", "Cake", "Crackers", "Pizza"
    ]
    
    # Split and merge multi-line items
    lines = merge_multiline_items(text.split('\n'))
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Updated price pattern to handle various formats including discounts
        price_pattern = r'\$(\d+\.\d{2})(?:\s*(?:,\s*|\s+)?(?:(?:-\s*\$(\d+\.\d{2})|(?:\d+%\s*(?:off|discount):?\s*-?\$?(\d+\.\d{2}))))?'
        price_matches = list(re.finditer(price_pattern, line))
        
        if price_matches:
            # Get the main price
            original_price = float(price_matches[0].group(1))
            
            # Get discount if present (either direct amount or calculated from percentage)
            discount = None
            if len(price_matches[0].groups()) > 1:
                discount_amount = price_matches[0].group(2) or price_matches[0].group(3)
                if discount_amount:
                    discount = float(discount_amount)
            
            # Extract item description (everything before the first price)
            description = line[:price_matches[0].start()].strip()
            description = re.sub(r'\s+', ' ', description)  # Clean up whitespace
            
            # Try to match with common product names
            item_name = fuzzy_match_product(description, common_products) or description.split(':')[0].strip()
            
            # Calculate final price
            final_price = original_price - (discount if discount else 0)
            
            # Check if it might be gluten-free
            gf_confidence = is_gluten_free(description)
            
            items.append(ItemPrice(
                item_name=item_name,
                original_price=original_price,
                description=description,
                discount=discount,
                final_price=final_price,
                gf_confidence=gf_confidence
            ))
    
    return items

def extract_prices_from_image(image_bytes: bytes) -> Optional[List[ItemPrice]]:
    """
    Extract items and prices from receipt image using enhanced OCR
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
        
        # Extract text with improved configuration
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_blacklist=|~`'
        text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        # Get items with prices
        items = get_items_with_prices(text)
        
        return items if items else None
        
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
