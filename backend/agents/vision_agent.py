import os
import base64
import io
from PIL import Image
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def describe_image_groq(image_bytes: bytes) -> str:
    """
    Describes image using Groq Vision API.
    """
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image in detail. Extract any visible text exactly as it appears. Provide a unified description that includes both the visual context and the text found. Keep it concise but thorough."},
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
        return "Visual description unavailable."

def get_image_description(image_bytes: bytes) -> str:
    """
    API-only vision strategy for cloud deployment.
    """
    return describe_image_groq(image_bytes)
