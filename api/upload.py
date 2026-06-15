import sys
import os
import uuid

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

@app.post("/api/upload")
@app.post("/")
async def upload_image(request: Request, file: UploadFile = File(...)):
    try:
        from agents.graph import ingestion_graph
        from db.database import init_db
        init_db()

        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        image_bytes = await file.read()

        import requests as req
        blob_token = os.environ.get("BLOB_READ_WRITE_TOKEN")
        if blob_token:
            url = f"https://blob.vercel-storage.com/{unique_filename}"
            headers = {"authorization": f"Bearer {blob_token}", "x-api-version": "7"}
            response = req.put(url, headers=headers, data=image_bytes)
            response.raise_for_status()
            image_url = response.json()["url"]
        else:
            raise HTTPException(status_code=500, detail="BLOB_READ_WRITE_TOKEN not set")

        initial_state = {
            "image_bytes": image_bytes, "image_url": image_url,
            "extracted_text": "", "image_description": "",
            "unified_description": "", "tags": [], "embedding": [], "screenshot_id": 0
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

handler = Mangum(app, lifespan="off")
