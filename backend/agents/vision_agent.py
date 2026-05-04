import os
import base64
import io
from PIL import Image
from groq import Groq
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Local BLIP model initialization
processor = None
model = None

def load_local_blip():
    global processor, model
    if processor is None or model is None:
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def describe_image_groq(image_bytes: bytes) -> str:
    """
    Attempts to describe image using Groq Vision API.
    """
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image in detail focusing on objects, context, and actions. Keep it under 200 words."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model="llama-3.2-11b-vision-preview",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Groq Vision failed: {e}")
        return None

def describe_image_blip(image_bytes: bytes) -> str:
    """
    Fallback image description using local BLIP model.
    """
    try:
        load_local_blip()
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs)
        return processor.decode(out[0], skip_special_tokens=True)
    except Exception as e:
        print(f"Local BLIP failed: {e}")
        return "Visual description unavailable."

def get_image_description(image_bytes: bytes) -> str:
    """
    Hybrid Strategy: Primary Groq -> Fallback BLIP.
    """
    description = describe_image_groq(image_bytes)
    if not description:
        print("Falling back to local BLIP...")
        description = describe_image_blip(image_bytes)
    return description
