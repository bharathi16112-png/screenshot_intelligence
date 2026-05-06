import os
import base64
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extracts text using Groq's Vision model (Cloud-based).
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return ""

    client = Groq(api_key=api_key)
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all readable text from this image. Return ONLY the text, nothing else."},
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
        return response.choices[0].message.content
    except Exception as e:
        print(f"Cloud OCR failed: {e}")
        return ""
