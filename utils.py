import io
from PIL import Image

TARGET_SIZE = (320, 180)

def process_image(image_file) -> Image.Image:
    """
    Process the uploaded image:
    1. Open image
    2. Convert to Grayscale (L)
    3. Resize to 320x180
    """
    try:
        img = Image.open(image_file)
        img = img.convert("L")  # Convert to grayscale
        img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        return img
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """Convert PIL Image to bytes."""
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format=format)
    return img_byte_arr.getvalue()

def bytes_to_image(image_bytes: bytes) -> Image.Image:
    """Convert bytes to PIL Image."""
    return Image.open(io.BytesIO(image_bytes))
