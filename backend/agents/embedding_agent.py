import os
import requests
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Hugging Face Inference API settings
HF_API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
HF_TOKEN = os.getenv("HF_TOKEN", "") 

def generate_embedding(text: str) -> list:
    """
    Generate semantic embedding using Hugging Face Inference API.
    """
    if not text:
        return [0.0] * 384
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    payload = {"inputs": text}
    
    try:
        # Short timeout to prevent 500 errors if API is slow
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=10)
        
        # Handle model loading (503 error)
        if response.status_code == 503:
            print("HF Model loading... retrying in 2s")
            time.sleep(2)
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=10)
            
        result = response.json()
        if isinstance(result, list):
            return result
        else:
            print(f"Embedding API error: {result}")
            return [0.0] * 384
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return [0.0] * 384

def generate_tags(text: str) -> list:
    """
    Generate tags from text using Groq LLM.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return ["memory"]
        
    client = Groq(api_key=api_key)

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
