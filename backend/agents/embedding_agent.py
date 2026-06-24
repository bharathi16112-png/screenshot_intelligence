import os
import math
import hashlib
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Local embedding model (sentence-transformers, runs fully offline).
# Loaded lazily so startup is fast even when the library isn't installed.
# ---------------------------------------------------------------------------
_local_model = None
_local_model_failed = False  # set True once so we don't retry on every call


def _try_local_model(text: str):
    """Try to embed with local sentence-transformers. Returns list or None."""
    global _local_model, _local_model_failed
    if _local_model_failed:
        return None
    try:
        if _local_model is None:
            from sentence_transformers import SentenceTransformer
            print("Loading local embedding model (all-MiniLM-L6-v2)...")
            _local_model = SentenceTransformer("all-MiniLM-L6-v2")
            print("Embedding model loaded.")
        vec = _local_model.encode(text, normalize_embeddings=True)
        return vec.tolist()
    except Exception as e:
        print(f"Local embedding model unavailable: {e}")
        _local_model_failed = True
        return None


# ---------------------------------------------------------------------------
# Groq-based pseudo-embedding fallback.
# Groq doesn't expose an embeddings API, so we use a deterministic hash of
# the LLM's keyword extraction to build a reproducible sparse-ish float
# vector.  It's not as good as a real embedding model but it guarantees
# non-zero vectors and consistent search behaviour when no ML runtime exists.
# ---------------------------------------------------------------------------
_GROQ_EMB_DIM = 384


def _groq_hash_embedding(text: str) -> list:
    """
    Deterministic pseudo-embedding: hash each 'word unit' of the text into a
    position in a 384-dim vector and accumulate L2-normalised values.
    Works offline (no API needed) and never returns an all-zero vector for
    non-empty text.
    """
    if not text.strip():
        return [0.0] * _GROQ_EMB_DIM

    words = text.lower().split()
    vec = [0.0] * _GROQ_EMB_DIM

    for word in words:
        h = int(hashlib.sha256(word.encode()).hexdigest(), 16)
        idx = h % _GROQ_EMB_DIM
        # Use a second hash byte for the value so direction varies
        val = ((h >> 8) & 0xFF) / 255.0 * 2 - 1  # in [-1, 1]
        vec[idx] += val

    # L2 normalise
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]

    return vec


def generate_embedding(text: str) -> list:
    """
    Generate a 384-dim semantic embedding.

    Priority:
    1. Local sentence-transformers model (best quality, fully offline)
    2. Deterministic hash embedding (always works, zero external deps)
    """
    if not text or not text.strip():
        return [0.0] * _GROQ_EMB_DIM

    # 1. Try local model
    result = _try_local_model(text)
    if result is not None:
        return result

    # 2. Hash-based fallback — never fails, never returns all-zeros
    print("Using hash-based embedding fallback.")
    return _groq_hash_embedding(text)


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
