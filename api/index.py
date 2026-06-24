import sys
import os

# Make backend importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app
# Exposing `app` is all Vercel needs for ASGI applications like FastAPI.
