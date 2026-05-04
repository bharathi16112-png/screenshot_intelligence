import os
import sqlite3

db_path = os.path.join(os.getcwd(), "db", "visual_memory.db")

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update localhost:8001/images to 127.0.0.1:8010/images
        print("Migrating records from port 8001 to 127.0.0.1:8010...")
        cursor.execute("UPDATE screenshots SET image_url = REPLACE(image_url, 'localhost:8001', '127.0.0.1:8010')")
        cursor.execute("UPDATE screenshots SET image_url = REPLACE(image_url, '127.0.0.1:8001', '127.0.0.1:8010')")
        
        updated_rows = conn.total_changes
        conn.commit()
        conn.close()
        print(f"Successfully updated {updated_rows} rows in the database.")
    except Exception as e:
        print(f"Migration error: {e}")
else:
    print(f"Database not found at {db_path}")
