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
    try:
        items = []
        common_products = [
            "Bread", "Roll", "Muffin", "Bagel", "Cereal",
            "Pasta", "Cookie", "Cake", "Crackers", "Pizza"
        ]
        
        # Split and merge multi-line items
        lines = merge_multiline_items(text.split('\n'))
        
        # Updated price pattern with corrected regex as per manager's request
        price_pattern = r'\$(\d+\.\d{2})(?:\s*(?:,\s*|\s+)?(?:(?:-\s*\$(\d+\.\d{2})|(?:\d+%\s*(?:off|discount):?\s*-?\$?(\d+\.\d{2}))))*'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            try:
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
            except re.error as e:
                # Handle regex-specific errors for each line
                print(f"Warning: Could not process line due to regex error: {str(e)}")
                continue
        
        return items
    except Exception as e:
        raise Exception(f"Error extracting prices: {str(e)}")

def extract_prices_from_image(image_bytes: bytes) -> Optional[List[ItemPrice]]:
    """
    Extract items and prices from receipt image using enhanced OCR with improved error handling
    """
    try:
        # Validate image
        is_valid, error_message = validate_image(image_bytes)
        if not is_valid:
            raise ValueError(error_message)
        
        # Convert bytes to image
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValueError(f"Unable to open image: {str(e)}. Please ensure the image is not corrupted.")
        
        # Preprocess image
        try:
            processed_image = preprocess_image(image)
        except Exception as e:
            raise ValueError(f"Error during image preprocessing: {str(e)}. Please try with a clearer image.")
        
        # Extract text with improved configuration
        try:
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_blacklist=|~`'
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            
            if not text.strip():
                raise ValueError("No text could be extracted from the image. Please ensure the receipt text is clear and readable.")
        except Exception as e:
            raise ValueError(f"Error during text extraction: {str(e)}. Please ensure tesseract is properly installed.")
        
        # Get items with prices
        try:
            items = get_items_with_prices(text)
            
            if not items:
                return None
            
            return items
            
        except re.error as e:
            raise ValueError(f"Error parsing prices: {str(e)}. Please ensure prices are in standard format ($XX.XX).")
        except Exception as e:
            raise ValueError(f"Error processing receipt text: {str(e)}")
        
    except ValueError as e:
        # Propagate user-friendly error messages
        raise ValueError(str(e))
    except Exception as e:
        # Catch any other unexpected errors
        raise Exception(f"Unexpected error processing receipt: {str(e)}")
