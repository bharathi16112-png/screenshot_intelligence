import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def fix_sequences():
    with engine.begin() as conn:
        try:
            # Reset sequence for screenshots
            conn.execute(text("SELECT setval('screenshots_id_seq', (SELECT MAX(id) FROM screenshots))"))
            print("Reset sequence for screenshots.")
        except Exception as e:
            print(f"Failed to reset screenshots sequence: {e}")

        try:
            # Reset sequence for tags
            conn.execute(text("SELECT setval('tags_id_seq', (SELECT MAX(id) FROM tags))"))
            print("Reset sequence for tags.")
        except Exception as e:
            print(f"Failed to reset tags sequence: {e}")

        try:
            # Reset sequence for embeddings
            conn.execute(text("SELECT setval('embeddings_id_seq', (SELECT MAX(id) FROM embeddings))"))
            print("Reset sequence for embeddings.")
        except Exception as e:
            print(f"Failed to reset embeddings sequence: {e}")

if __name__ == "__main__":
    fix_sequences()
