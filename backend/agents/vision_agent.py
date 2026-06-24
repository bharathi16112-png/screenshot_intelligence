import os
import base64
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_image_description(image_bytes: bytes) -> str:
    """
    Describes an image using Groq's Llama-3.2-11b-vision-preview (Cloud-based).
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Description unavailable: No API Key"

    client = Groq(api_key=api_key)

    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this screenshot in detail, focusing on key elements, text, and context."},
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
        print(f"Vision analysis failed: {e}")
        return f"Description unavailable: {str(e)}"
