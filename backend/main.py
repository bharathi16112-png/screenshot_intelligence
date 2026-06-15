import os
from fastapi import FastAPI, UploadFile, File, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from agents.graph import ingestion_graph
from agents.retrieval_graph import retrieval_graph
from db.database import init_db, SessionLocal, Screenshot
import shutil
import uuid

app = FastAPI(title="Multimodal Visual Memory Assistant")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Keeping * but ensuring headers are robust
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for image serving
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")

@app.on_event("startup")
def startup():
    try:
        print("Initializing database...")
        init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise e

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
        
        import requests
        blob_token = os.environ.get("BLOB_READ_WRITE_TOKEN")
        if blob_token:
            # Upload to Vercel Blob
            url = f"https://blob.vercel-storage.com/{unique_filename}"
            headers = {
                "authorization": f"Bearer {blob_token}",
                "x-api-version": "7"
            }
            response = requests.put(url, headers=headers, data=image_bytes)
            response.raise_for_status()
            image_url = response.json()["url"]
        else:
            # Fallback to local file system
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            with open(file_path, "wb") as buffer:
                buffer.write(image_bytes)
            
            # Dynamically determine base URL from request
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search")
@app.get("/search")
def search_memories(q: str = Query(...)):
    """
    Performs agentic search across stored visual memories.
    """
    try:
        # Run Retrieval Graph
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
        
        # Also try to clear local files if not using Blob
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
    db = SessionLocal()
    try:
        memories = db.query(Screenshot).all()
        return memories
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8010))
    uvicorn.run(app, host="0.0.0.0", port=port)
