import json
from sentence_transformers import SentenceTransformer
from agents.embedding_agent import generate_embedding
from db.database import SessionLocal, Screenshot, Embedding

# Load model locally
model = SentenceTransformer('all-MiniLM-L6-v2')

import hashlib

def get_content_hash(text, description):
    """Generates a stable hash for content deduplication."""
    # Normalize: lowercase and remove extra whitespace
    clean_text = " ".join(str(text or "").lower().split())
    clean_desc = " ".join(str(description or "").lower().split())
    combined = f"{clean_text}|{clean_desc}"
    return hashlib.md5(combined.encode()).hexdigest()

def get_relevant_memories(query_text: str, limit: int = 5):
    """
    Retrieves deduplicated memories based on semantic similarity.
    """
    query_embedding = generate_embedding(query_text)
    db = SessionLocal()
    
    # Increase buffer to allow for deduplication
    fetch_limit = max(limit * 3, 20)
    
    try:
        from sqlalchemy import text
        import numpy as np

        try:
            # 1. Try optimal pgvector search
            sql_query = text("""
                SELECT screenshot_id, 1 - (vector::vector <=> :vec) as similarity
                FROM embeddings
                ORDER BY vector::vector <=> :vec
                LIMIT :limit
            """)
            vec_str = "[" + ",".join(map(str, query_embedding)) + "]"
            results = db.execute(sql_query, {"vec": vec_str, "limit": fetch_limit}).fetchall()
            
            formatted_results = []
            for row in results:
                formatted_results.append((row[0], float(row[1])))
        
        except Exception as e:
            # 2. Fallback to in-memory similarity if pgvector extension is missing
            db.rollback() 
            print(f"SQL search failed: {e}")
            
            all_embeddings = db.query(Embedding).all()
            in_memory_results = []
            q_vec = np.array(query_embedding)
            
            for emb in all_embeddings:
                try:
                    e_vec = np.array(json.loads(emb.vector))
                    norm_q = np.linalg.norm(q_vec)
                    norm_e = np.linalg.norm(e_vec)
                    if norm_q > 0 and norm_e > 0:
                        similarity = np.dot(q_vec, e_vec) / (norm_q * norm_e)
                        in_memory_results.append((emb.screenshot_id, float(similarity)))
                except: continue
            
            in_memory_results.sort(key=lambda x: x[1], reverse=True)
            formatted_results = in_memory_results[:fetch_limit]

        # Fetch metadata and deduplicate
        memories = []
        seen_hashes = set()
        top_score = formatted_results[0][1] if formatted_results else 0.0

        for screenshot_id, similarity in formatted_results:
            screenshot = db.query(Screenshot).filter(Screenshot.id == screenshot_id).first()
            if screenshot:
                # Content-based hash for deduplication
                c_hash = get_content_hash(screenshot.extracted_text, screenshot.image_description)
                if c_hash in seen_hashes:
                    continue
                seen_hashes.add(c_hash)

                memories.append({
                    "id": screenshot.id,
                    "image_url": screenshot.image_url,
                    "extracted_text": screenshot.extracted_text,
                    "image_description": screenshot.image_description,
                    "similarity": similarity
                })
                
                # Stop if we have reached the requested limit
                if len(memories) >= limit:
                    break
        
        return {
            "results": memories,
            "top_score": top_score
        }
    finally:
        db.close()
