import os
import re
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from groq import Groq
from dotenv import load_dotenv
from agents.retrieval_agent import get_relevant_memories

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class RetrievalState(TypedDict):
    query: str
    refined_query: str
    results: List[dict]
    top_score: float
    confidence_message: str
    answer: str

def query_understanding_node(state: RetrievalState):
    """
    Refines the user query by extracting key visual attributes.
    """
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Visual Attribute Extraction Agent. Your goal is to take a natural language user query "
                        "and extract key visual attributes for semantic search. Focus on:\n"
                        "- Primary Colors\n- Objects/People\n- Scene/Context\n- Key Actions\n\n"
                        "Return a concise list of these keywords separated by spaces. "
                        "Example: 'yellow saree' -> 'yellow saree clothing person'"
                    )
                },
                {
                    "role": "user",
                    "content": f"Extract attributes from: {state['query']}"
                }
            ],
            model="llama-3.1-8b-instant",
        )
        refined_query = response.choices[0].message.content
        return {"refined_query": refined_query}
    except Exception as e:
        print(f"Query refinement failed: {e}")
        return {"refined_query": state['query']}

def retrieval_node(state: RetrievalState):
    """
    Performs vector search with a larger limit to provide candidates for reranking.
    """
    search_data = get_relevant_memories(state['refined_query'], limit=10)
    results = search_data["results"]
    top_score = search_data["top_score"]

    # Dynamic threshold logic
    if top_score > 0.7:
        threshold = 0.5
    elif top_score > 0.5:
        threshold = 0.35
    else:
        threshold = 0.25
    
    filtered_results = [r for r in results if r["similarity"] >= threshold]
    
    confidence_message = ""
    if not filtered_results:
        confidence_message = "No strong matches found."
    elif top_score < 0.45:
        confidence_message = "Showing closest matches (low confidence)."
    else:
        confidence_message = "Found relevant matches."

    return {
        "results": filtered_results, 
        "top_score": top_score, 
        "confidence_message": confidence_message
    }

def reranking_node(state: RetrievalState):
    """
    Uses a powerful LLM to rerank the filtered candidates for maximum relevance.
    """
    if not state['results'] or len(state['results']) <= 1:
        return {"results": state['results']}

    # Prepare candidates for the LLM evaluation
    candidates_text = ""
    for i, res in enumerate(state['results']):
        candidates_text += f"[{i}] OCR: {res.get('extracted_text', '')[:100]} | Desc: {res.get('image_description', '')[:200]}\n"

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Visual Search Reranker. Your task is to rank the provided image candidates "
                        "based on how well they match the User Query. Consider both visual descriptions and OCR text.\n\n"
                        "Return ONLY a comma-separated list of indices in the order of most relevant to least relevant. "
                        "Example: '2, 0, 1'. Return only the numbers and commas."
                    )
                },
                {
                    "role": "user",
                    "content": f"User Query: {state['query']}\n\nCandidates:\n{candidates_text}"
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0,
        )
        
        raw_output = response.choices[0].message.content.strip()
        # Extract indices using regex to be robust
        indices = [int(idx) for idx in re.findall(r'\d+', raw_output)]
        
        # Build reranked list
        reranked = []
        seen = set()
        for idx in indices:
            if idx < len(state['results']) and idx not in seen:
                reranked.append(state['results'][idx])
                seen.add(idx)
        
        # Add back any candidates the LLM missed (safety)
        for i, res in enumerate(state['results']):
            if i not in seen:
                reranked.append(res)
        
        return {"results": reranked[:5]} # Return top 5 reranked results
    except Exception as e:
        print(f"Reranking failed: {e}")
        return {"results": state['results'][:5]}

def response_node(state: RetrievalState):
    """
    Generates an intelligent answer based on confidence level and results.
    """
    if not state['results']:
        return {"answer": f"{state.get('confidence_message', 'No matches found.')} Try a more specific description of colors, objects, or the scene."}

    context = ""
    for res in state['results']:
        context += f"- ID: {res['id']}, Similarity: {res['similarity']:.2f}, Text: {res.get('extracted_text', '')}, Description: {res.get('image_description', '')}\n"

    prompt_prefix = "You are a helpful Visual Memory Assistant."
    if "low confidence" in state.get('confidence_message', '').lower():
        prompt_prefix += " Note: The matches found have low visual similarity, so be cautious and mention they are 'closest matches'."

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"{prompt_prefix} Based ON THE PROVIDED CONTEXT, answer the user's question accurately. Be conversational and friendly."
                },
                {
                    "role": "user",
                    "content": f"User Query: {state['query']}\n\nConfidence: {state.get('confidence_message', 'Normal')}\nRetrieved Context:\n{context}"
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        answer = response.choices[0].message.content
        return {"answer": answer}
    except Exception as e:
        print(f"Response generation failed: {e}")
        return {"answer": f"{state.get('confidence_message', 'I found some matches.')} Take a look at the results below."}

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
