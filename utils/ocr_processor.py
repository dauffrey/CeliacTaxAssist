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

def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Enhanced image preprocessing specifically for receipt scanning
    """
    try:
        # Convert PIL Image to OpenCV format
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Increase resolution for better text recognition
        scale_factor = 2
        img_array = cv2.resize(img_array, None, fx=scale_factor, fy=scale_factor, 
                             interpolation=cv2.INTER_LANCZOS4)
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        img_array = clahe.apply(img_array)
        
        # Apply bilateral filtering for noise reduction while preserving edges
        img_array = cv2.bilateralFilter(img_array, 9, 75, 75)
        
        # Apply adaptive thresholding with optimal parameters for receipt text
        img_array = cv2.adaptiveThreshold(
            img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 15, 8
        )
        
        # Deskew image if needed
        coords = np.column_stack(np.where(img_array > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) > 0.5:  # Only rotate if angle is significant
            (h, w) = img_array.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            img_array = cv2.warpAffine(img_array, M, (w, h),
                                     flags=cv2.INTER_CUBIC,
                                     borderMode=cv2.BORDER_REPLICATE)
        
        # Convert back to PIL Image
        enhanced_image = Image.fromarray(img_array)
        
        # Additional sharpening for text clarity
        enhanced_image = enhanced_image.filter(ImageFilter.SHARPEN)
        enhanced_image = enhanced_image.filter(ImageFilter.UnsharpMask(radius=2, percent=150))
        
        return enhanced_image
    except Exception as e:
        raise Exception(f"Error preprocessing image: {str(e)}")

def clean_text(text: str) -> str:
    """
    Enhanced text cleanup for receipt format
    """
    # Remove unwanted characters while preserving essential ones
    text = re.sub(r'[^\w\s$%.:()-]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common OCR errors
    text = text.replace('S', '$').replace('s', '$')
    text = text.replace('0O', '00').replace('O0', '00')
    
    # Normalize price formats
    text = re.sub(r'(\d+)\.(\d{2})', r'\1.\2', text)
    
    # Fix discount notation
    text = text.replace('off-', 'off: -')
    text = text.replace('discount-', 'discount: -')
    
    return text.strip()

def get_items_with_prices(text: str) -> List[ItemPrice]:
    """
    Enhanced item and price extraction for Masstown Market receipt format
    """
    try:
        items = []
        
        # Clean and normalize text
        text = clean_text(text)
        
        # Split into lines and process each line
        lines = text.split('\n')
        
        # Enhanced price pattern for Masstown Market format
        price_pattern = (
            r'\$(\d+\.\d{2})'  # Base price
            r'(?:\s*'  # Optional whitespace
            r'(?:\((?:Item\s+)?(?:discount\s+)?(\d+)%'  # Percentage in parentheses
            r'(?:\s*[-:]\s*\$(\d+\.\d{2}))?\)|'  # Optional amount after percentage
            r'\s*[-:]\s*\$(\d+\.\d{2}))?'  # Direct discount amount
        )
        
        current_item = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            try:
                # Check for price matches
                price_matches = list(re.finditer(price_pattern, line))
                
                if price_matches:
                    # Get the main price
                    original_price = float(price_matches[0].group(1))
                    
                    # Extract item name (everything before the price)
                    item_name = line[:price_matches[0].start()].strip()
                    
                    # Handle discount
                    discount = None
                    if len(price_matches[0].groups()) > 1:
                        # Check for percentage discount
                        discount_percent = price_matches[0].group(2)
                        discount_amount = price_matches[0].group(3) or price_matches[0].group(4)
                        
                        if discount_amount:
                            discount = float(discount_amount)
                        elif discount_percent:
                            # Calculate discount from percentage
                            discount = (float(discount_percent) / 100) * original_price
                    
                    # Calculate final price
                    final_price = original_price - (discount if discount else 0)
                    
                    # Create ItemPrice object
                    items.append(ItemPrice(
                        item_name=item_name,
                        original_price=original_price,
                        description=line,
                        discount=discount,
                        final_price=final_price,
                        gf_confidence=is_gluten_free(item_name)
                    ))
            
            except Exception as e:
                print(f"Warning: Error processing line '{line}': {str(e)}")
                continue
        
        return items
    except Exception as e:
        raise Exception(f"Error extracting prices: {str(e)}")

def extract_prices_from_image(image_bytes: bytes) -> Optional[List[ItemPrice]]:
    """
    Extract prices from receipt image with enhanced error handling
    """
    try:
        # Validate image
        is_valid, error_message = validate_image(image_bytes)
        if not is_valid:
            raise ValueError(error_message)
        
        # Load and preprocess image
        image = Image.open(io.BytesIO(image_bytes))
        processed_image = preprocess_image(image)
        
        # Configure tesseract for receipt format
        custom_config = (
            '--oem 3 '  # Use LSTM OCR Engine
            '--psm 6 '  # Assume uniform block of text
            '-c tessedit_char_whitelist="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$%().,-: " '
            '-c tessedit_write_images=true'
        )
        
        # Extract text
        text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        if not text.strip():
            raise ValueError("No text could be extracted. Please ensure the receipt is clearly visible.")
        
        # Process items
        items = get_items_with_prices(text)
        
        if not items:
            raise ValueError("No valid items or prices found. Please ensure the receipt format is correct.")
        
        return items
        
    except Exception as e:
        raise Exception(f"Error processing receipt: {str(e)}")

def validate_image(image_bytes: bytes) -> Tuple[bool, str]:
    """Validate image format and quality"""
    try:
        # Check format
        image_format = imghdr.what(None, h=image_bytes)
        if not image_format:
            return False, "Invalid image format"
        
        # Open image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Check dimensions
        if image.width < 300 or image.height < 300:
            return False, "Image resolution too low"
        
        return True, ""
    except Exception as e:
        return False, str(e)

def is_gluten_free(text: str) -> float:
    """Check if item is gluten-free"""
    text = text.lower()
    if any(indicator in text for indicator in ['gluten-free', 'gluten free', 'gf']):
        return 1.0
    return 0.0
