import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import io
import imghdr
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
import numpy as np
import cv2

@dataclass
class ItemPrice:
    item_name: str
    original_price: float
    description: Optional[str] = None
    discount: Optional[float] = None
    final_price: Optional[float] = None
    gf_confidence: Optional[float] = None

def preprocess_image(image: Image.Image) -> Image.Image:
    """Enhanced image preprocessing for Masstown Market receipts"""
    try:
        # Convert PIL Image to OpenCV format
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Increase resolution for better text recognition
        scale_factor = 2
        img_array = cv2.resize(img_array, None, fx=scale_factor, fy=scale_factor, 
                             interpolation=cv2.INTER_LANCZOS4)
        
        # Enhance contrast for better text recognition
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        img_array = clahe.apply(img_array)
        
        # Deskew image to handle any rotation
        coords = np.column_stack(np.where(img_array > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) > 0.5:
            (h, w) = img_array.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            img_array = cv2.warpAffine(img_array, M, (w, h),
                                     flags=cv2.INTER_CUBIC,
                                     borderMode=cv2.BORDER_REPLICATE)
        
        # Bilateral filtering for noise reduction while preserving edges
        img_array = cv2.bilateralFilter(img_array, 9, 75, 75)
        
        # Adaptive thresholding optimized for receipt text
        img_array = cv2.adaptiveThreshold(
            img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 21, 11
        )
        
        # Convert back to PIL Image
        enhanced_image = Image.fromarray(img_array)
        
        # Additional sharpening for text clarity
        enhanced_image = enhanced_image.filter(ImageFilter.SHARPEN)
        enhanced_image = enhanced_image.filter(ImageFilter.UnsharpMask(radius=2, percent=150))
        
        return enhanced_image
    except Exception as e:
        raise Exception(f"Error preprocessing image: {str(e)}")

def clean_text(text: str) -> str:
    """Enhanced text cleanup for Masstown Market receipt format"""
    # Preserve price parentheses and discount indicators
    text = re.sub(r'[^\w\s$%():.-]', '', text)
    
    # Fix common OCR errors
    text = text.replace('S', '$').replace('s', '$')
    text = text.replace('0O', '00').replace('O0', '00')
    
    # Standardize discount notation
    text = text.replace('Item discount', 'Item discount ')
    text = text.replace('Discount:', 'Item discount ')
    text = text.replace('DISCOUNT:', 'Item discount ')
    
    # Normalize price formats while preserving parentheses
    text = re.sub(r'(\d+)\.(\d{2})', r'\1.\2', text)
    
    return text.strip()

def process_multiline_item(lines: List[str], start_idx: int) -> Tuple[Optional[Dict], int]:
    """Process multi-line items with discounts"""
    if start_idx >= len(lines):
        return None, start_idx
        
    current_line = lines[start_idx].strip()
    
    # Match main item line with price
    main_pattern = r'^(?P<name>.*?)\s+\$(?P<price>\d+\.\d{2})$'
    main_match = re.match(main_pattern, current_line)
    
    if not main_match:
        return None, start_idx
        
    item_data = {
        'name': main_match.group('name').strip(),
        'price': float(main_match.group('price')),
        'discount': None,
        'description': current_line
    }
    
    # Check next line for discount
    if start_idx + 1 < len(lines):
        next_line = lines[start_idx + 1].strip()
        discount_pattern = r'^Item\s+discount\s+(?P<percent>\d+)%\s*\((?:\$)?(?P<amount>\d+\.\d{2})\)$'
        discount_match = re.match(discount_pattern, next_line)
        
        if discount_match:
            item_data['discount'] = float(discount_match.group('amount'))
            item_data['description'] += f"\n{next_line}"
            return item_data, start_idx + 2
    
    return item_data, start_idx + 1

def get_items_with_prices(text: str) -> List[ItemPrice]:
    """Enhanced item and price extraction for Masstown Market receipt format"""
    try:
        items = []
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        i = 0
        while i < len(lines):
            try:
                item_data, next_i = process_multiline_item(lines, i)
                
                if item_data:
                    items.append(ItemPrice(
                        item_name=item_data['name'],
                        original_price=item_data['price'],
                        description=item_data['description'],
                        discount=item_data['discount'],
                        final_price=item_data['price'] - (item_data['discount'] or 0),
                        gf_confidence=is_gluten_free(item_data['name'])
                    ))
                
                i = next_i
            
            except Exception as e:
                print(f"Warning: Error processing line: {str(e)}")
                i += 1
        
        return items
    except Exception as e:
        raise Exception(f"Error extracting prices: {str(e)}")

def extract_prices_from_image(image_bytes: bytes) -> Optional[List[ItemPrice]]:
    """Extract prices from receipt image with enhanced error handling"""
    try:
        # Validate image
        is_valid, error_message = validate_image(image_bytes)
        if not is_valid:
            raise ValueError(error_message)
        
        # Load and preprocess image
        image = Image.open(io.BytesIO(image_bytes))
        processed_image = preprocess_image(image)
        
        # Configure tesseract for Masstown Market receipt format
        custom_config = (
            '--oem 3 '  # LSTM OCR Engine
            '--psm 6 '  # Uniform block of text
            '-c tessedit_char_whitelist="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$%().,-: " '
            '-c tessedit_write_images=true'
        )
        
        # Extract text
        text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        if not text.strip():
            raise ValueError("No text could be extracted. Please ensure the receipt is clearly visible.")
        
        # Clean text
        text = clean_text(text)
        
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
