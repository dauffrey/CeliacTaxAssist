import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import io
import imghdr
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
import numpy as np
import cv2
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
    Enhanced image validation with detailed feedback
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
        img = Image.open(io.BytesIO(image_bytes))
        
        # Check image size
        if img.width < 300 or img.height < 300:
            return False, "Image resolution is too low. Please provide a clearer, higher-resolution image."
        
        # Check if image is too large
        max_size = 4000  # pixels
        if img.width > max_size or img.height > max_size:
            return False, f"Image is too large. Maximum dimensions are {max_size}x{max_size} pixels."
        
        return True, ""
    except Exception as e:
        return False, f"Error processing image: {str(e)}"

def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Enhanced image preprocessing for better OCR results
    """
    try:
        # Convert PIL Image to OpenCV format
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Increase resolution (2x upscaling)
        scale_factor = 2
        img_array = cv2.resize(img_array, None, fx=scale_factor, fy=scale_factor, 
                             interpolation=cv2.INTER_LANCZOS4)
        
        # Apply denoising
        img_array = cv2.fastNlMeansDenoising(img_array)
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        img_array = clahe.apply(img_array)
        
        # Apply adaptive thresholding
        img_array = cv2.adaptiveThreshold(
            img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Convert back to PIL Image
        enhanced_image = Image.fromarray(img_array)
        
        # Additional PIL enhancements
        enhanced_image = enhanced_image.filter(ImageFilter.SHARPEN)
        
        return enhanced_image
    except Exception as e:
        raise Exception(f"Error preprocessing image: {str(e)}")

def merge_multiline_items(lines: List[str]) -> List[str]:
    """
    Improved multi-line item merging with better pattern recognition
    """
    merged_lines = []
    current_line = ""
    price_pattern = r'\$\d+\.\d{2}'
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_line:
                merged_lines.append(current_line)
                current_line = ""
            continue
        
        # Check if line contains a price
        has_price = bool(re.search(price_pattern, line))
        
        # Check if line starts with common item indicators
        item_indicators = ['qty', 'quantity', 'item', '#', '@']
        starts_with_indicator = any(line.lower().startswith(ind) for ind in item_indicators)
        
        if has_price or starts_with_indicator:
            if current_line:
                merged_lines.append(current_line)
            current_line = line
        else:
            if current_line:
                current_line += " " + line
            else:
                current_line = line
    
    if current_line:
        merged_lines.append(current_line)
    
    return merged_lines

def clean_text(text: str) -> str:
    """
    Enhanced text cleanup for better parsing
    """
    # Remove unwanted characters
    text = re.sub(r'[^\w\s$%.:()-]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common OCR errors
    text = text.replace('S', '$').replace('s', '$')
    
    # Normalize price formats
    text = re.sub(r'(\d+)\.(\d{2})', r'\1.\2', text)
    
    return text.strip()

def get_items_with_prices(text: str) -> List[ItemPrice]:
    """
    Enhanced item and price extraction with improved pattern matching
    """
    try:
        items = []
        common_products = [
            "Bread", "Roll", "Muffin", "Bagel", "Cereal",
            "Pasta", "Cookie", "Cake", "Crackers", "Pizza"
        ]
        
        # Clean and normalize text
        text = clean_text(text)
        
        # Split and merge multi-line items
        lines = merge_multiline_items(text.split('\n'))
        
        # Enhanced price pattern with support for various formats
        price_pattern = (
            r'\$(\d+\.\d{2})'  # Base price
            r'(?:\s*(?:,\s*|\s+)?'  # Optional separator
            r'(?:'  # Start of discount group
            r'(?:-\s*\$(\d+\.\d{2})|'  # Direct discount amount
            r'(?:(\d+)%\s*(?:off|discount):?\s*-?\$?(\d+\.\d{2}))*'  # Percentage discount
            r')'  # End of discount group
            r')*'  # Make the entire discount group optional
        )
        
        for line in lines:
            try:
                price_matches = list(re.finditer(price_pattern, line))
                
                if price_matches:
                    # Get the main price
                    original_price = float(price_matches[0].group(1))
                    
                    # Calculate discount
                    discount = None
                    if len(price_matches[0].groups()) > 1:
                        # Try direct discount amount
                        direct_discount = price_matches[0].group(2)
                        if direct_discount:
                            discount = float(direct_discount)
                        else:
                            # Try percentage discount
                            percent = price_matches[0].group(3)
                            discount_amount = price_matches[0].group(4)
                            if percent and discount_amount:
                                discount = float(discount_amount)
                    
                    # Extract and clean description
                    description = line[:price_matches[0].start()].strip()
                    description = clean_text(description)
                    
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
                print(f"Warning: Could not process line '{line}' due to regex error: {str(e)}")
                continue
            except Exception as e:
                print(f"Warning: Error processing line '{line}': {str(e)}")
                continue
        
        return items
    except Exception as e:
        raise Exception(f"Error extracting prices: {str(e)}")

def extract_prices_from_image(image_bytes: bytes) -> Optional[List[ItemPrice]]:
    """
    Enhanced price extraction with improved error handling and feedback
    """
    try:
        # Validate image
        is_valid, error_message = validate_image(image_bytes)
        if not is_valid:
            raise ValueError(error_message)
        
        # Convert bytes to image with error handling
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValueError(f"Unable to open image: {str(e)}. Please ensure the image is not corrupted.")
        
        # Preprocess image with error handling
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
        
        # Process extracted text
        try:
            items = get_items_with_prices(text)
            
            if not items:
                raise ValueError("No valid items or prices found in the receipt. Please ensure prices are clearly visible and in standard format ($XX.XX).")
            
            return items
            
        except Exception as e:
            raise ValueError(f"Error processing receipt text: {str(e)}")
        
    except ValueError as e:
        raise ValueError(str(e))
    except Exception as e:
        raise Exception(f"Unexpected error processing receipt: {str(e)}")

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
