import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")

try:
    print(f"Connecting to {url}...")
    conn = psycopg2.connect(url, connect_timeout=5)
    print("Connection successful!")
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print(cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
