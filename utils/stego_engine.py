"""
Production-Grade LSB Steganography Engine
Algorithm: Least Significant Bit substitution with capacity management
"""

import os
from pathlib import Path
from typing import Tuple, Dict, Optional
from PIL import Image
import io
from stegano import lsb
import hashlib


class StegoEngine:
    """Production steganography engine with validation"""
    
    SUPPORTED_FORMATS = ['PNG', 'BMP', 'TIFF']
    MIN_DIMENSION = 100
    METADATA_OVERHEAD = 200  # bytes
    
    @staticmethod
    def validate_image(image_path: str) -> Tuple[bool, str, Dict]:
        """
        Comprehensive image validation
        
        Returns:
            (is_valid, message, stats)
        """
        try:
            if not os.path.exists(image_path):
                return False, "Image file not found", {}
            
            img = Image.open(image_path)
            width, height = img.size
            format_name = img.format or "Unknown"
            mode = img.mode
            
            stats = {
                'width': width,
                'height': height,
                'format': format_name,
                'mode': mode,
                'size_kb': os.path.getsize(image_path) / 1024,
                'pixels': width * height
            }
            
            # Check format
            if format_name not in StegoEngine.SUPPORTED_FORMATS:
                return False, f"❌ Format {format_name} not supported. Use PNG/BMP/TIFF", stats
            
            # Check dimensions
            if width < StegoEngine.MIN_DIMENSION or height < StegoEngine.MIN_DIMENSION:
                return False, f"❌ Image too small ({width}x{height}). Minimum: {StegoEngine.MIN_DIMENSION}x{StegoEngine.MIN_DIMENSION}", stats
            
            # Calculate capacity
            capacity = StegoEngine.calculate_capacity(image_path)
            stats['capacity_bytes'] = capacity
            stats['capacity_kb'] = capacity / 1024
            
            if capacity < 1000:
                return False, f"❌ Insufficient capacity ({capacity} bytes)", stats
            
            return True, f"✅ Valid image: {width}x{height}, {capacity/1024:.1f} KB capacity", stats
        
        except Exception as e:
            return False, f"❌ Invalid image: {str(e)}", {}
    
    @staticmethod
    def calculate_capacity(image_path: str) -> int:
        """Calculate maximum payload capacity in bytes"""
        img = Image.open(image_path)
        width, height = img.size
        
        # Convert to RGB if needed
        if img.mode not in ['RGB', 'RGBA']:
            img = img.convert('RGB')
        
        # RGB has 3 channels, each can hide 1 bit in LSB
        channels = 3 if img.mode == 'RGB' else 4
        total_bits = width * height * channels
        
        # Convert to bytes and subtract overhead
        max_bytes = (total_bits // 8) - StegoEngine.METADATA_OVERHEAD
        return max_bytes
    
    @staticmethod
    def prepare_image(image_path: str, output_path: Optional[str] = None) -> str:
        """
        Prepare image for steganography (convert format, strip metadata)
        
        Returns:
            Path to prepared image
        """
        img = Image.open(image_path)
        
        # Convert to RGB if needed
        if img.mode not in ['RGB', 'RGBA']:
            img = img.convert('RGB')
        
        # Strip metadata
        data = list(img.getdata())
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(data)
        
        # Save as PNG
        if output_path is None:
            output_path = str(Path(image_path).with_suffix('.png'))
        
        clean_img.save(output_path, format='PNG', optimize=True)
        return output_path
    
    @staticmethod
    def hide(cover_path: str, secret_data: str, output_path: str, 
             password: Optional[str] = None) -> Dict:
        """
        Hide encrypted data in image using LSB
        
        Returns:
            Statistics dictionary
        """
        # Validate
        is_valid, msg, stats = StegoEngine.validate_image(cover_path)
        if not is_valid:
            raise ValueError(msg)
        
        # Check capacity
        data_size = len(secret_data.encode('utf-8'))
        if data_size > stats['capacity_bytes']:
            raise ValueError(
                f"Data too large ({data_size} bytes). "
                f"Maximum: {stats['capacity_bytes']} bytes"
            )
        
        # Prepare image
        prepared_path = StegoEngine.prepare_image(cover_path)
        
        # Embed using LSB
        stego_img = lsb.hide(prepared_path, secret_data)
        stego_img.save(output_path, format='PNG', optimize=True)
        
        # Clean up temporary file
        if prepared_path != cover_path and os.path.exists(prepared_path):
            os.remove(prepared_path)
        
        # Calculate stats
        result_stats = {
            'cover_size_kb': stats['size_kb'],
            'stego_size_kb': os.path.getsize(output_path) / 1024,
            'payload_bytes': data_size,
            'payload_kb': data_size / 1024,
            'capacity_used_percent': (data_size / stats['capacity_bytes']) * 100,
            'dimensions': f"{stats['width']}x{stats['height']}",
            'format': stats['format']
        }
        
        return result_stats
    
    @staticmethod
    def reveal(stego_path: str) -> str:
        """
        Extract hidden data from stego image
        
        Returns:
            Extracted payload string
        """
        if not os.path.exists(stego_path):
            raise ValueError("Stego image not found")
        
        try:
            secret_data = lsb.reveal(stego_path)
            
            if secret_data is None or len(secret_data) == 0:
                raise ValueError("No hidden data detected in image")
            
            return secret_data
        
        except Exception as e:
            raise ValueError(f"Extraction failed: {str(e)}")
    
    @staticmethod
    def compare_images(original_path: str, stego_path: str) -> Dict:
        """
        Compare original and stego images
        
        Returns:
            Comparison statistics
        """
        orig_img = Image.open(original_path)
        stego_img = Image.open(stego_path)
        
        # Calculate PSNR (Peak Signal-to-Noise Ratio)
        import numpy as np
        
        orig_array = np.array(orig_img)
        stego_array = np.array(stego_img)
        
        mse = np.mean((orig_array.astype(float) - stego_array.astype(float)) ** 2)
        
        if mse == 0:
            psnr = float('inf')
        else:
            max_pixel = 255.0
            psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
        
        return {
            'psnr_db': psnr,
            'mse': mse,
            'identical': mse == 0,
            'visually_identical': psnr > 40  # > 40 dB is imperceptible
        }
