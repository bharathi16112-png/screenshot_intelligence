import psycopg2
import os

try:
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="B#@rathi-",
        host="127.0.0.1",
        port=5432
    )
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
