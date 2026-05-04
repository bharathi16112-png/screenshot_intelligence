import easyocr
import io
from PIL import Image
import numpy as np

# Load reader globally for efficiency
# Using 'en' as default
reader = easyocr.Reader(['en'])

def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extracts text from image bytes using EasyOCR.
    """
    image = Image.open(io.BytesIO(image_bytes))
    image_np = np.array(image)
    
    # Read text from image
    results = reader.readtext(image_np, detail=0)
    
    # Combine results into a single string
    full_text = " ".join(results)
    return full_text
