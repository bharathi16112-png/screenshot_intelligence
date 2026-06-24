"""
Diagnostic script: run this to see exactly what's in the DB and what
the retrieval path returns. Execute with:
    py diag_search.py "your search query"
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

query = sys.argv[1] if len(sys.argv) > 1 else "test"

# ── 1. DB contents ─────────────────────────────────────────────────────────
from db.database import SessionLocal, Screenshot, Embedding

db = SessionLocal()
screenshots = db.query(Screenshot).all()
embeddings  = db.query(Embedding).all()

print(f"\n=== DB CONTENTS ===")
print(f"Screenshots : {len(screenshots)}")
print(f"Embeddings  : {len(embeddings)}")

for s in screenshots[:5]:
    print(f"\n  Screenshot id={s.id}")
    print(f"    url  : {s.image_url}")
    print(f"    text : {repr((s.extracted_text or '')[:80])}")
    print(f"    desc : {repr((s.image_description or '')[:80])}")

for e in embeddings[:5]:
    try:
        vec = json.loads(e.vector)
        if isinstance(vec, list) and vec and isinstance(vec[0], list):
            print(f"  Embedding id={e.id} screenshot_id={e.screenshot_id} => NESTED LIST (shape [{len(vec)}][{len(vec[0])}]) ← bug!")
        else:
            import numpy as np
            arr = [float(x) for x in vec]
            norm = float(__import__('numpy').linalg.norm(arr))
            print(f"  Embedding id={e.id} screenshot_id={e.screenshot_id} len={len(arr)} norm={norm:.4f} first3={arr[:3]}")
    except Exception as ex:
        print(f"  Embedding id={e.id} screenshot_id={e.screenshot_id} PARSE ERROR: {ex}")
        print(f"    raw[:100]: {repr(e.vector[:100])}")

db.close()

# ── 2. Embedding for query ──────────────────────────────────────────────────
print(f"\n=== QUERY EMBEDDING ===")
print(f"Query: {query!r}")
from agents.embedding_agent import generate_embedding
q_emb = generate_embedding(query)
print(f"Type      : {type(q_emb)}")
if isinstance(q_emb, list) and q_emb:
    if isinstance(q_emb[0], list):
        print(f"Shape     : NESTED [{len(q_emb)}][{len(q_emb[0])}]  ← unwrap needed")
    else:
        import numpy as np
        norm = float(np.linalg.norm(q_emb))
        print(f"Length    : {len(q_emb)}")
        print(f"Norm      : {norm:.4f}")
        print(f"First 3   : {q_emb[:3]}")
else:
    print(f"Value     : {q_emb}")

# ── 3. Full retrieval path ──────────────────────────────────────────────────
print(f"\n=== RETRIEVAL RESULT ===")
from agents.retrieval_agent import get_relevant_memories
result = get_relevant_memories(query, limit=5)
print(f"top_score : {result['top_score']}")
print(f"results   : {len(result['results'])}")
for r in result['results']:
    print(f"  id={r['id']} similarity={r['similarity']:.4f} desc={repr((r['image_description'] or '')[:60])}")

if not result['results']:
    print("  (empty — check output above for clues)")
