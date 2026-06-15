import os
from fastapi import FastAPI, UploadFile, File, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from agents.graph import ingestion_graph
from agents.retrieval_graph import retrieval_graph
from db.database import init_db, SessionLocal, Screenshot
import shutil
import uuid

app = FastAPI(title="Multimodal Visual Memory Assistant")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files - only mount locally, not on Vercel (ephemeral filesystem)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IS_VERCEL = os.environ.get("VERCEL", False)

if IS_VERCEL:
    UPLOAD_DIR = "/tmp/uploads"
else:
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

if not IS_VERCEL:
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    from fastapi.staticfiles import StaticFiles
    app.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")

DB_INIT_ERROR = None
try:
    print("Initializing database...")
    init_db()
    print("Database initialized successfully.")
except Exception as e:
    import traceback
    DB_INIT_ERROR = str(e) + "\n" + traceback.format_exc()
    print(f"Database initialization failed: {e}")

@app.on_event("startup")
def startup():
    # Keep for local backward compatibility, but actual init happens above
    pass

@app.get("/api/")
@app.get("/")
def read_root():
    return {"message": "Multimodal Visual Memory AI is online."}

@app.post("/api/upload")
@app.post("/upload")
async def upload_image(request: Request, file: UploadFile = File(...)):
    """
    Ingests an image, runs multi-agent processing, and saves to memory.
    """
    try:
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Read file for processing and uploading
        image_bytes = await file.read()
        
        import requests as req
        blob_token = os.environ.get("BLOB_READ_WRITE_TOKEN")
        if blob_token:
            # Upload to Vercel Blob
            url = f"https://blob.vercel-storage.com/{unique_filename}"
            headers = {
                "authorization": f"Bearer {blob_token}",
                "x-api-version": "7"
            }
            response = req.put(url, headers=headers, data=image_bytes)
            response.raise_for_status()
            image_url = response.json()["url"]
        else:
            # Fallback to local file system
            if not os.path.exists(UPLOAD_DIR):
                os.makedirs(UPLOAD_DIR)
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            with open(file_path, "wb") as buffer:
                buffer.write(image_bytes)
            
            base_url = str(request.base_url).rstrip("/")
            if "localhost" not in base_url and "127.0.0.1" not in base_url:
                base_url = base_url.replace("http://", "https://")
                
            image_url = f"{base_url}/images/{unique_filename}"
        
        # Run LangGraph Ingestion
        initial_state = {
            "image_bytes": image_bytes,
            "image_url": image_url,
            "extracted_text": "",
            "image_description": "",
            "unified_description": "",
            "tags": [],
            "embedding": [],
            "screenshot_id": 0
        }
        
        final_state = ingestion_graph.invoke(initial_state)
        
        return {
            "status": "success",
            "screenshot_id": final_state["screenshot_id"],
            "image_url": image_url,
            "tags": final_state["tags"]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        if DB_INIT_ERROR:
            return {"error": f"Database Init Failed: {DB_INIT_ERROR}", "traceback": traceback.format_exc()}
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.get("/api/search")
@app.get("/search")
def search_memories(q: str = Query(...)):
    """
    Performs agentic search across stored visual memories.
    """
    try:
        initial_state = {
            "query": q,
            "refined_query": "",
            "results": [],
            "top_score": 0.0,
            "confidence_message": "",
            "answer": ""
        }
        
        final_state = retrieval_graph.invoke(initial_state)
        
        return {
            "query": q,
            "answer": final_state["answer"],
            "results": final_state["results"],
            "top_score": final_state.get("top_score", 0.0),
            "confidence_message": final_state.get("confidence_message", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/memories")
@app.delete("/memories")
def clear_memories():
    """
    Wipes all memories from the database.
    """
    db = SessionLocal()
    try:
        from db.database import Tag, Embedding
        db.query(Embedding).delete()
        db.query(Tag).delete()
        db.query(Screenshot).delete()
        db.commit()
        
        if not os.environ.get("BLOB_READ_WRITE_TOKEN") and os.path.exists(UPLOAD_DIR):
            shutil.rmtree(UPLOAD_DIR)
            os.makedirs(UPLOAD_DIR)
            
        return {"status": "success", "message": "All memories cleared."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/memories")
@app.get("/memories")
def list_memories():
    """
    Lists all memories.
    """
    try:
        db = SessionLocal()
        try:
            memories = db.query(Screenshot).all()
            result = []
            for mem in memories:
                result.append({
                    "id": mem.id,
                    "image_url": mem.image_url,
                    "extracted_text": mem.extracted_text,
                    "image_description": mem.image_description,
                    "created_at": mem.created_at.isoformat() if mem.created_at else None,
                    "tags": [tag.tag_name for tag in mem.tags] if mem.tags else []
                })
            return result
        finally:
            db.close()
    except Exception as e:
        import traceback
        if DB_INIT_ERROR:
            return {"error": f"Database Init Failed: {DB_INIT_ERROR}", "traceback": traceback.format_exc()}
        return {"error": str(e), "traceback": traceback.format_exc()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8010))
    uvicorn.run(app, host="0.0.0.0", port=port)
