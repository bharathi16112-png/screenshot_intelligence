import sys
import os

# Make backend importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app
from mangum import Mangum

# Vercel invokes this handler for every routed request
handler = Mangum(app, lifespan="off")
