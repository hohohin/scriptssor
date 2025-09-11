#!/usr/bin/env python3
"""
Create PNG icons for Chrome extension
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size):
    """Create a square icon with gradient background and text"""
    # Create image with RGBA mode
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Create gradient background
    for y in range(size):
        # Calculate gradient color
        ratio = y / size
        r = int(59 + (139 - 59) * ratio)
        g = int(130 + (92 - 130) * ratio)
        b = int(246 + (246 - 246) * ratio)
        
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    
    # Draw text
    try:
        # Try to use a font
        font_size = int(size * 0.6)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fall back to default font
        font = ImageFont.load_default()
    
    # Get text size
    text = "S"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center text
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    return img

def main():
    """Create icons in different sizes"""
    sizes = [16, 32, 48, 128]
    
    # Create output directory
    output_dir = "browser-extension-store/icons"
    os.makedirs(output_dir, exist_ok=True)
    
    for size in sizes:
        print(f"Creating {size}x{size} icon...")
        icon = create_icon(size)
        output_path = os.path.join(output_dir, f"icon{size}.png")
        icon.save(output_path, "PNG")
        print(f"Saved: {output_path}")
    
    print("All icons created successfully!")

if __name__ == "__main__":
    try:
        from PIL import Image, ImageDraw, ImageFont
        main()
    except ImportError:
        print("PIL library not found. Installing...")
        import subprocess
        import sys
        
        # Install PIL
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        
        # Retry
        from PIL import Image, ImageDraw, ImageFont
        main()
    except Exception as e:
        print(f"Error creating icons: {e}")
        print("Please create PNG icons manually using an image editor.")
        print("Required sizes: 16x16, 32x32, 48x48, 128x128")
        print("Design: Blue gradient background with white 'S' text")