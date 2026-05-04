from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from agents.ocr_agent import extract_text_from_image
from agents.vision_agent import get_image_description
from agents.embedding_agent import generate_tags, generate_embedding
from db.database import SessionLocal, Screenshot, Tag, Embedding

class AgentState(TypedDict):
    image_bytes: bytes
    image_url: str
    extracted_text: str
    image_description: str
    unified_description: str
    tags: List[str]
    embedding: List[float]
    screenshot_id: int

def ocr_node(state: AgentState):
    extracted_text = extract_text_from_image(state['image_bytes'])
    return {"extracted_text": extracted_text}

def vision_node(state: AgentState):
    image_description = get_image_description(state['image_bytes'])
    return {"image_description": image_description}

def understanding_node(state: AgentState):
    unified = f"Text found: {state['extracted_text']}. Visual context: {state['image_description']}"
    return {"unified_description": unified}

def tagging_node(state: AgentState):
    tags = generate_tags(state['unified_description'])
    return {"tags": tags}

def embedding_node(state: AgentState):
    embedding = generate_embedding(state['unified_description'])
    return {"embedding": embedding}

def storage_node(state: AgentState):
    db = SessionLocal()
    try:
        # Create screenshot entry
        screenshot = Screenshot(
            image_url=state['image_url'],
            extracted_text=state['extracted_text'],
            image_description=state['image_description']
        )
        db.add(screenshot)
        db.commit()
        db.refresh(screenshot)
        
        # Add tags
        for tag_name in state['tags']:
            db.add(Tag(screenshot_id=screenshot.id, tag_name=tag_name))
        
        # Add embedding
        import json
        db.add(Embedding(screenshot_id=screenshot.id, vector=json.dumps(state['embedding'])))
        
        db.commit()
        return {"screenshot_id": screenshot.id}
    finally:
        db.close()

# Define the graph
workflow = StateGraph(AgentState)

workflow.add_node("ocr", ocr_node)
workflow.add_node("vision", vision_node)
workflow.add_node("understanding", understanding_node)
workflow.add_node("tagging", tagging_node)
workflow.add_node("embedding", embedding_node)
workflow.add_node("storage", storage_node)

workflow.set_entry_point("ocr")
workflow.add_edge("ocr", "vision")
workflow.add_edge("vision", "understanding")
workflow.add_edge("understanding", "tagging")
workflow.add_edge("tagging", "embedding")
workflow.add_edge("embedding", "storage")
workflow.add_edge("storage", END)

ingestion_graph = workflow.compile()
