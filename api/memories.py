import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from db.database import SessionLocal, Screenshot

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/memories")
@app.get("/")
def list_memories():
    db = SessionLocal()
    try:
        memories = db.query(Screenshot).all()
        result = []
        for m in memories:
            result.append({
                "id": m.id,
                "image_url": m.image_url,
                "extracted_text": m.extracted_text,
                "image_description": m.image_description,
                "created_at": str(m.created_at) if m.created_at else None,
                "tags": [t.tag_name for t in m.tags] if m.tags else []
            })
        return result
    finally:
        db.close()

@app.delete("/api/memories")
@app.delete("/")
def clear_memories():
    from db.database import Tag, Embedding
    db = SessionLocal()
    try:
        db.query(Embedding).delete()
        db.query(Tag).delete()
        db.query(Screenshot).delete()
        db.commit()
        return {"status": "success", "message": "All memories cleared."}
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

handler = Mangum(app, lifespan="off")
