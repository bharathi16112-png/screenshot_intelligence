import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app
from db.database import init_db

# Ensure tables are created when this lambda cold-starts
init_db()
