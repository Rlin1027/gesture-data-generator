from PIL import Image
import os

def create_dummy_image():
    # Create a 320x180 grayscale image
    img = Image.new('L', (320, 180), color=128)
    img.save('dummy_seed.png')
    print("Created dummy_seed.png")

if __name__ == "__main__":
    create_dummy_image()
