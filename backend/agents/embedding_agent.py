from sentence_transformers import SentenceTransformer
import numpy as np

# Load model globally
model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text: str) -> list:
    """
    Generate semantic embedding for a given text.
    """
    if not text:
        return None
    embedding = model.encode(text)
    return embedding.tolist()

def generate_tags(text: str) -> list:
    """
    Generate tags from text (simple logic for now, could be LLM-based).
    """
    # Using LLM for better tagging performance
    import os
    from groq import Groq
    from dotenv import load_dotenv

    load_dotenv()
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Extract 5-7 semantic tags from the following text and visual description. Return ONLY a comma-separated list: {text}"
                }
            ],
            model="llama-3.1-8b-instant",
        )
        tags = response.choices[0].message.content.split(",")
        return [tag.strip() for tag in tags]
    except Exception as e:
        print(f"Tag generation failed: {e}")
        return ["memory", "screenshot"]
