import json
import hashlib
import math
from agents.embedding_agent import generate_embedding
from db.database import SessionLocal, Screenshot, Embedding


def get_content_hash(text, description):
    """Generates a stable hash for content deduplication."""
    clean_text = " ".join(str(text or "").lower().split())
    clean_desc = " ".join(str(description or "").lower().split())
    combined = f"{clean_text}|{clean_desc}"
    return hashlib.md5(combined.encode()).hexdigest()


def _cosine_similarity(q_vec, e_vec):
    """Compute cosine similarity; returns 0.0 if either vector is all zeros."""
    norm_q = math.sqrt(sum(v*v for v in q_vec))
    norm_e = math.sqrt(sum(v*v for v in e_vec))
    if norm_q == 0 or norm_e == 0:
        # Zero-vector: fall back to a neutral score so the record is still surfaced
        return 0.0
    dot_product = sum(q*e for q, e in zip(q_vec, e_vec))
    return float(dot_product / (norm_q * norm_e))


def get_relevant_memories(query_text: str, limit: int = 5):
    """
    Retrieves deduplicated memories based on semantic similarity.
    Falls back to keyword search when semantic scores are too low.
    """
    query_embedding = generate_embedding(query_text)
    db = SessionLocal()

    # Increase buffer to allow for deduplication
    fetch_limit = max(limit * 3, 20)

    try:
        from sqlalchemy import text

        formatted_results = []
        semantic_ok = False

        # ------------------------------------------------------------------ #
        # 1. In-memory cosine similarity (works for both SQLite & PostgreSQL
        #    without requiring the pgvector extension to be installed).
        # ------------------------------------------------------------------ #
        if query_embedding and len(query_embedding) >= 10:
            q_vec = query_embedding
            all_embeddings = db.query(Embedding).all()
            in_memory_results = []

            for emb in all_embeddings:
                try:
                    if not emb.vector:
                        continue
                    raw = json.loads(emb.vector)
                    e_vec = raw
                    if len(e_vec) != len(q_vec):
                        continue
                    similarity = _cosine_similarity(q_vec, e_vec)
                    in_memory_results.append((emb.screenshot_id, similarity))
                except Exception as ex:
                    print(f"Skipping corrupted embedding for screenshot {emb.screenshot_id}: {ex}")
                    continue

            in_memory_results.sort(key=lambda x: x[1], reverse=True)
            formatted_results = in_memory_results[:fetch_limit]
            semantic_ok = True
            print(f"In-memory semantic search returned {len(formatted_results)} candidates. "
                  f"Top score: {formatted_results[0][1]:.4f}" if formatted_results else
                  "In-memory semantic search: no candidates found.")
        else:
            print("Invalid query embedding — skipping semantic search.")

        # ------------------------------------------------------------------ #
        # 2. Keyword fallback — used when semantic search returned nothing OR
        #    the best semantic score is very low (< 0.05).
        # ------------------------------------------------------------------ #
        top_semantic = formatted_results[0][1] if formatted_results else 0.0
        use_keyword_fallback = (not formatted_results) or (top_semantic < 0.05)

        if use_keyword_fallback:
            print("Trying keyword fallback search...")
            search_pattern = f"%{query_text}%"
            keyword_results = db.query(Screenshot).filter(
                (Screenshot.extracted_text.ilike(search_pattern)) |
                (Screenshot.image_description.ilike(search_pattern))
            ).limit(limit).all()

            # Build a lookup of existing scores so keyword hits can override
            # zero-score semantic entries (which happen when embeddings are all zeros)
            existing_scores = {sid: score for sid, score in formatted_results}
            for screenshot in keyword_results:
                existing_scores[screenshot.id] = max(existing_scores.get(screenshot.id, 0.0), 0.5)

            # Rebuild formatted_results with the updated scores
            all_ids = list(existing_scores.keys())
            formatted_results = sorted(
                [(sid, existing_scores[sid]) for sid in all_ids],
                key=lambda x: x[1],
                reverse=True,
            )

        # ------------------------------------------------------------------ #
        # 3. Fetch metadata & deduplicate by content hash
        # ------------------------------------------------------------------ #
        memories = []
        seen_hashes = set()
        top_score = formatted_results[0][1] if formatted_results else 0.0

        for screenshot_id, similarity in formatted_results:
            screenshot = db.query(Screenshot).filter(Screenshot.id == screenshot_id).first()
            if screenshot:
                c_hash = get_content_hash(screenshot.extracted_text, screenshot.image_description)
                if c_hash in seen_hashes:
                    continue
                seen_hashes.add(c_hash)

                memories.append({
                    "id": screenshot.id,
                    "image_url": screenshot.image_url,
                    "extracted_text": screenshot.extracted_text,
                    "image_description": screenshot.image_description,
                    "similarity": similarity,
                })

                if len(memories) >= limit:
                    break

        return {"results": memories, "top_score": top_score}

    finally:
        db.close()
