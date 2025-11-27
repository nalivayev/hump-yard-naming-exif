"""Create test images for plugin testing.

This script creates sample JPEG and TIFF files with structured filenames
for testing the PhotoNamingExifPlugin.
"""

from pathlib import Path
from PIL import Image, ImageDraw


def create_test_image(filename: str, color: str, description: str) -> None:
    """Create a test image with description text.
    
    Args:
        filename: Name of the file to create
        color: Background color
        description: Text to draw on the image
    """
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)
    
    # Create image
    img = Image.new('RGB', (800, 600), color=color)
    draw = ImageDraw.Draw(img)
    
    # Add description text
    draw.text((50, 250), description, fill='white')
    
    # Save image
    file_path = test_dir / filename
    ext = file_path.suffix.lower()
    fmt = 'JPEG' if ext in ['.jpg', '.jpeg'] else 'TIFF'
    img.save(file_path, fmt, quality=95)
    
    print(f"Created: {filename}")


def main():
    """Create all test images."""
    print("Creating test images...")
    print()
    
    # Test case 1: Exact date with time
    create_test_image(
        "1950.06.15.12.30.45.E.FAM.POR.000001.jpg",
        "lightblue",
        "Exact Date\n1950-06-15 12:30:45\nFamily Portrait"
    )
    
    # Test case 2: Circa month (partial date)
    create_test_image(
        "1965.08.00.00.00.00.C.TRV.LND.000002.jpg",
        "lightgreen",
        "Circa Date\n~August 1965\nTravel Landscape"
    )
    
    # Test case 3: Exact date, no time (TIFF)
    create_test_image(
        "2010.03.20.00.00.00.E.FAM.GRP.000003.tiff",
        "lightyellow",
        "Exact Date (no time)\n2010-03-20\nFamily Group"
    )
    
    # Test case 4: Circa year only
    create_test_image(
        "1970.00.00.00.00.00.C.FAM.GRP.000004.jpg",
        "lightcoral",
        "Circa Date\n~1970\nFamily Group"
    )
    
    # Test case 5: Invalid filename (should be skipped)
    create_test_image(
        "invalid_name.jpg",
        "lightgray",
        "Invalid Filename\nShould NOT be processed"
    )
    
    print()
    print("Done! Created 5 test images in test_images/")
    print()
    print("To test the plugin:")
    print("  1. Run the plugin on these files")
    print("  2. Check that valid files are moved to test_images/processed/")
    print("  3. Verify metadata with ExifTool:")
    print("     exiftool -a -G1 test_images/processed/*.jpg")


if __name__ == "__main__":
    main()
