import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import io
import imghdr
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
import numpy as np
import cv2
import signal
from functools import wraps
import time

class OCRTimeoutError(Exception):
    """Raised when OCR processing exceeds timeout limit"""
    pass

def timeout_handler(signum, frame):
    raise OCRTimeoutError("OCR processing timed out")

def with_timeout(timeout=30):
    """Decorator to add timeout to a function"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Set the signal handler and a timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
            try:
                result = func(*args, **kwargs)
            finally:
                # Disable the alarm
                signal.alarm(0)
            return result
        return wrapper
    return decorator

@dataclass
class ItemPrice:
    item_name: str
    original_price: float
    description: Optional[str] = None
    discount: Optional[float] = None
    final_price: Optional[float] = None
    gf_confidence: Optional[float] = None

def validate_image(image_bytes: bytes) -> Tuple[bool, str]:
    """Enhanced image validation with detailed feedback"""
    try:
        # Check format
        image_format = imghdr.what(None, h=image_bytes)
        if not image_format:
            return False, "Invalid image format. Please upload a valid image file (JPEG, PNG, BMP, or TIFF)."
        
        if image_format.lower() not in ['jpeg', 'jpg', 'png', 'bmp', 'tiff']:
            return False, f"Unsupported image format: {image_format}. Please use JPEG, PNG, BMP, or TIFF format."
        
        # Open and validate image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Check dimensions
        if image.width < 300 or image.height < 300:
            return False, "Image resolution too low. Please provide a clearer image (minimum 300x300 pixels)."
        
        if image.width > 4000 or image.height > 4000:
            return False, "Image dimensions too large. Maximum size is 4000x4000 pixels."
        
        return True, ""
    except Exception as e:
        return False, f"Error validating image: {str(e)}"

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
        
        # Deskew image if needed
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
        raise Exception(f"Error preprocessing image: {str(e)}. Please ensure the image is not corrupted.")

def clean_text(text: str) -> str:
    """Enhanced text cleanup for Masstown Market receipt format"""
    try:
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
    except Exception as e:
        raise Exception(f"Error cleaning text: {str(e)}")

def process_multiline_item(lines: List[str], start_idx: int) -> Tuple[Optional[Dict], int]:
    """Process multi-line items with discounts"""
    if start_idx >= len(lines):
        return None, start_idx
    
    try:
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
    except Exception as e:
        raise Exception(f"Error processing line: {str(e)}")

@with_timeout(30)  # Set 30-second timeout for OCR processing
def perform_ocr(image: Image.Image, config: str) -> str:
    """Perform OCR with timeout"""
    return pytesseract.image_to_string(image, config=config)

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
        
        if not items:
            raise ValueError("No valid items found in the receipt text")
        
        return items
    except Exception as e:
        raise Exception(f"Error extracting prices: {str(e)}")

def extract_prices_from_image(image_bytes: bytes) -> Optional[List[ItemPrice]]:
    """Extract prices from receipt image with enhanced error handling and timeout"""
    try:
        # Validate image
        is_valid, error_message = validate_image(image_bytes)
        if not is_valid:
            raise ValueError(error_message)
        
        # Load and preprocess image
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValueError(f"Error loading image: {str(e)}. Please ensure the image is not corrupted.")
        
        try:
            processed_image = preprocess_image(image)
        except Exception as e:
            raise ValueError(f"Error preprocessing image: {str(e)}. Please try with a clearer image.")
        
        # Configure tesseract for Masstown Market receipt format
        custom_config = (
            '--oem 3 '  # LSTM OCR Engine
            '--psm 6 '  # Uniform block of text
            '-c tessedit_char_whitelist="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$%().,-: " '
            '-c tessedit_write_images=true'
        )
        
        try:
            # Perform OCR with timeout
            text = perform_ocr(processed_image, custom_config)
            
            if not text.strip():
                raise ValueError("No text could be extracted. Please ensure the receipt is clearly visible and properly lit.")
            
            # Clean text
            text = clean_text(text)
            
            # Process items
            items = get_items_with_prices(text)
            return items
            
        except OCRTimeoutError:
            raise ValueError("OCR processing timed out. Please try again with a clearer image or contact support if the issue persists.")
        except Exception as e:
            raise ValueError(f"Error performing OCR: {str(e)}. Please ensure the image is clear and properly formatted.")
        
    except ValueError as e:
        raise ValueError(str(e))
    except Exception as e:
        raise Exception(f"Unexpected error processing receipt: {str(e)}")

def is_gluten_free(text: str) -> float:
    """Check if item is gluten-free"""
    try:
        text = text.lower()
        if any(indicator in text for indicator in ['gluten-free', 'gluten free', 'gf']):
            return 1.0
        return 0.0
    except Exception as e:
        print(f"Warning: Error checking gluten-free status: {str(e)}")
        return 0.0
