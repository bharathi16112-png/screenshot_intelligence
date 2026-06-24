"""
Re-generates embeddings for all stored screenshots using the local
sentence-transformers model. Run once after switching from the HF API:

    py reembed.py
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from db.database import SessionLocal, Screenshot, Embedding
from agents.embedding_agent import generate_embedding

db = SessionLocal()
try:
    screenshots = db.query(Screenshot).all()
    print(f"Found {len(screenshots)} screenshots to re-embed.\n")

    for s in screenshots:
        unified = f"Text found: {s.extracted_text or ''}. Visual context: {s.image_description or ''}"
        new_vec = generate_embedding(unified)

        # Check it's a real vector
        import numpy as np
        norm = float(np.linalg.norm(new_vec))
        print(f"  Screenshot {s.id}: norm={norm:.4f}  text={repr(unified[:60])}")

        emb = db.query(Embedding).filter(Embedding.screenshot_id == s.id).first()
        if emb:
            emb.vector = json.dumps(new_vec)
        else:
            db.add(Embedding(screenshot_id=s.id, vector=json.dumps(new_vec)))

    db.commit()
    print("\nDone — all embeddings updated.")
finally:
    db.close()
