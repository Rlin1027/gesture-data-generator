from PIL import Image
import os

# Paths
INPUT_PATH = ""
OUTPUT_PATH = ""

def process_image():
    if not os.path.exists(INPUT_PATH):
        print(f"Error: Input file not found at {INPUT_PATH}")
        return

    try:
        with Image.open(INPUT_PATH) as img:
            # 1. Convert to Grayscale
            img_gray = img.convert("L")
            
            # 2. Resize to 320x180
            # We use LANCZOS for high quality downsampling
            img_resized = img_gray.resize((320, 180), Image.Resampling.LANCZOS)
            
            # 3. Save
            img_resized.save(OUTPUT_PATH)
            print(f"Successfully processed and saved to {OUTPUT_PATH}")
            print(f"Format: {img_resized.mode}, Size: {img_resized.size}")

    except Exception as e:
        print(f"Error processing image: {e}")

if __name__ == "__main__":
    process_image()
