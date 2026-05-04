import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

PG_URL = os.getenv("DATABASE_URL")
SQLITE_PATH = "db/visual_memory.db"

def migrate():
    # Connect SQLite
    print(f"Reading from {SQLITE_PATH}...")
    sl_conn = sqlite3.connect(SQLITE_PATH)
    sl_cur = sl_conn.cursor()
    
    # Connect PG
    print(f"Connecting to PG at {PG_URL}...")
    pg_conn = psycopg2.connect(PG_URL)
    pg_cur = pg_conn.cursor()
    
    # Get SQLite data
    sl_cur.execute("SELECT id, image_url, extracted_text, image_description, created_at FROM screenshots")
    screenshots = sl_cur.fetchall()
    
    for row in screenshots:
        s_id, img_url, ext_text, img_desc, created_at = row
        print(f"Migrating screenshot {s_id}...")
        
        # Correct URL if needed (port 8010 is the current one)
        img_url = img_url.replace(":8001", ":8010")
        
        # Insert Screenshots
        pg_cur.execute(
            "INSERT INTO screenshots (id, image_url, extracted_text, image_description, created_at) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
            (s_id, img_url, ext_text, img_desc, created_at)
        )
        
        # Migrate Tags
        sl_cur.execute("SELECT screenshot_id, tag_name FROM tags WHERE screenshot_id = ?", (s_id,))
        tags = sl_cur.fetchall()
        for tag in tags:
            pg_cur.execute(
                "INSERT INTO tags (screenshot_id, tag_name) VALUES (%s, %s)",
                tag
            )
            
        # Migrate Embeddings
        sl_cur.execute("SELECT screenshot_id, vector FROM embeddings WHERE screenshot_id = ?", (s_id,))
        embeddings = sl_cur.fetchall()
        for emb in embeddings:
            pg_cur.execute(
                "INSERT INTO embeddings (screenshot_id, vector) VALUES (%s, %s)",
                emb
            )

    pg_conn.commit()
    print(f"Migration complete! {len(screenshots)} screenshots moved to PostgreSQL.")
    
    sl_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    migrate()
