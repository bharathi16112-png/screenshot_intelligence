import os
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
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
    allow_origins=["*"],
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

@app.get("/")
def read_root():
    return {"message": "Multimodal Visual Memory AI is online."}

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Ingests an image, runs multi-agent processing, and saves to memory.
    """
    try:
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        port = os.getenv("PORT", 8010)
        image_url = f"http://127.0.0.1:{port}/images/{unique_filename}"
        
        # Read file for processing
        with open(file_path, "rb") as f:
            image_bytes = f.read()
        
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
    uvicorn.run(app, host="127.0.0.1", port=port)
