import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/search")
@app.get("/")
def search_memories(q: str = Query(...)):
    try:
        from agents.retrieval_graph import retrieval_graph
        initial_state = {
            "query": q, "refined_query": "", "results": [],
            "top_score": 0.0, "confidence_message": "", "answer": ""
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

handler = Mangum(app, lifespan="off")
