import os
import psycopg2
from dotenv import load_dotenv
import traceback

load_dotenv()
url = os.getenv("DATABASE_URL")

try:
    print(f"Connecting to {url.split('@')[1]}...")
    conn = psycopg2.connect(url, connect_timeout=10)
    print("Connection successful!")
    print(f"Server version: {conn.server_version}")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
    traceback.print_exc()
