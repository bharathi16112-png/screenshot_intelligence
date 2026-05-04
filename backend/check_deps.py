try:
    import fastapi
    import uvicorn
    import sqlalchemy
    import dotenv
    import sentence_transformers
    import numpy
    import langgraph
    import groq
    import PIL
    import easyocr
    print("Dependencies OK")
except ImportError as e:
    print(f"Missing dependency: {e.name}")
