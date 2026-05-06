import os
import requests
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Hugging Face Inference API settings
# We use all-MiniLM-L6-v2 which is free and fast
HF_API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
# Note: Token is optional for low usage but recommended. 
# We'll use the same GROQ_API_KEY as a placeholder or tell the user to add HF_TOKEN
HF_TOKEN = os.getenv("HF_TOKEN", "") 

def generate_embedding(text: str) -> list:
    """
    Generate semantic embedding using Hugging Face Inference API (Zero RAM).
    """
    if not text:
        return None
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    payload = {"inputs": text}
    
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload)
        
        # Handle model loading (503 error)
        if response.status_code == 503:
            time.sleep(2)
            response = requests.post(HF_API_URL, headers=headers, json=payload)
            
        result = response.json()
        if isinstance(result, list):
            return result
        else:
            print(f"Embedding API error: {result}")
            return [0.0] * 384 # Fallback dimension for this model
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return [0.0] * 384

def generate_tags(text: str) -> list:
    """
    Generate tags from text using Groq LLM.
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a visual memory tagger. Extract 5-7 semantic tags from the provided text."
                },
                {
                    "role": "user",
                    "content": f"Extract tags for: {text}. Return ONLY a comma-separated list."
                }
            ],
            model="llama-3.1-8b-instant",
        )
        tags = response.choices[0].message.content.split(",")
        return [tag.strip() for tag in tags]
    except Exception as e:
        print(f"Tag generation failed: {e}")
        return ["memory", "screenshot"]
