"""
Simple icon generator for PRISM
Creates basic gradient icons for the application
"""

from PIL import Image, ImageDraw
import os

def create_gradient_circle(size, color1, color2, output_path):
    """Create a circular gradient icon"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient circle
    center = size // 2
    max_radius = size // 2
    
    for i in range(max_radius, 0, -1):
        # Calculate color interpolation
        ratio = i / max_radius
        r = int(color1[0] * ratio + color2[0] * (1 - ratio))
        g = int(color1[1] * ratio + color2[1] * (1 - ratio))
        b = int(color1[2] * ratio + color2[2] * (1 - ratio))
        
        # Calculate alpha for smooth edges
        alpha = 255 if i < max_radius - 2 else int(255 * (i / max_radius))
        
        draw.ellipse(
            [center - i, center - i, center + i, center + i],
            fill=(r, g, b, alpha)
        )
    
    # Add inner glow
    glow_radius = max_radius // 3
    for i in range(glow_radius, 0, -1):
        alpha = int(100 * (i / glow_radius))
        draw.ellipse(
            [center - i, center - i, center + i, center + i],
            fill=(255, 255, 255, alpha)
        )
    
    img.save(output_path)
    print(f"Created: {output_path}")

def main():
    """Generate all required icons"""
    assets_dir = os.path.join(os.path.dirname(__file__), 'ui', 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    
    # Color scheme (purple/blue gradient like in the UI)
    color1 = (102, 126, 234)  # #667eea
    color2 = (118, 75, 162)   # #764ba2
    
    print("Generating PRISM icons...")
    print("=" * 50)
    
    # Main application icon
    create_gradient_circle(
        256, color1, color2,
        os.path.join(assets_dir, 'icon.png')
    )
    
    # Tray icon (smaller)
    create_gradient_circle(
        32, color1, color2,
        os.path.join(assets_dir, 'tray-icon.png')
    )
    
    print("=" * 50)
    print("Icons generated successfully!")
    print(f"Location: {assets_dir}")
    print("\nNote: For .ico file, you can convert icon.png using:")
    print("  - Online: https://convertio.co/png-ico/")
    print("  - Or use: pip install pillow && python -c \"from PIL import Image; Image.open('ui/assets/icon.png').save('ui/assets/icon.ico')\"")

if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("ERROR: PIL/Pillow not installed")
        print("Install with: pip install pillow")
    except Exception as e:
        print(f"ERROR: {e}")
