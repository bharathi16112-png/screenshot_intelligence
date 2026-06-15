import os
import re
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from groq import Groq
from dotenv import load_dotenv
from agents.retrieval_agent import get_relevant_memories

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

class RetrievalState(TypedDict):
    query: str
    refined_query: str
    results: List[dict]
    top_score: float
    confidence_message: str
    answer: str

def query_understanding_node(state: RetrievalState):
    if not client: return {"refined_query": state['query']}
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Extract visual keywords for search. Return ONLY keywords."},
                {"role": "user", "content": state['query']}
            ],
            model="llama-3.1-8b-instant",
        )
        return {"refined_query": response.choices[0].message.content}
    except Exception:
        return {"refined_query": state['query']}

def retrieval_node(state: RetrievalState):
    try:
        search_data = get_relevant_memories(
            state['refined_query'],
            limit=10,
            original_query=state['query']  # Always search with original user query too
        )
        results = search_data.get("results", [])
        top_score = search_data.get("top_score", 0.0)
        
        # Simple threshold
        filtered_results = [r for r in results if r.get("similarity", 0) >= 0.2]
        return {"results": filtered_results, "top_score": top_score, "confidence_message": "Found results"}
    except Exception as e:
        print(f"Retrieval node failed: {e}")
        return {"results": [], "top_score": 0.0, "confidence_message": "Search error"}

def reranking_node(state: RetrievalState):
    # Skip reranking for simplicity and stability for now
    return {"results": state['results'][:5]}

def response_node(state: RetrievalState):
    if not state['results']:
        return {"answer": "No matches found. Try uploading more images or using different keywords."}
    
    if not client:
        return {"answer": "I found some matches for you. Please see the results below."}

    try:
        context = "\n".join([f"- {r.get('image_description', '')[:100]}" for r in state['results']])
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Answer the user query based on the provided context."},
                {"role": "user", "content": f"Query: {state['query']}\nContext: {context}"}
            ],
            model="llama-3.1-8b-instant",
        )
        return {"answer": response.choices[0].message.content}
    except Exception:
        return {"answer": "I found some matches. Check the results below!"}

# Define the graph
workflow = StateGraph(RetrievalState)
workflow.add_node("query_understanding", query_understanding_node)
workflow.add_node("retrieval", retrieval_node)
workflow.add_node("reranking", reranking_node)
workflow.add_node("response", response_node)

workflow.set_entry_point("query_understanding")
workflow.add_edge("query_understanding", "retrieval")
workflow.add_edge("retrieval", "reranking")
workflow.add_edge("reranking", "response")
workflow.add_edge("response", END)

retrieval_graph = workflow.compile()
