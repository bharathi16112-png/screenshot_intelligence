import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from main import app
except Exception as e:
    err_msg = traceback.format_exc()
    print("CRITICAL IMPORT ERROR:\n" + err_msg)
    
    # Fallback ASGI app to render the error
    async def app(scope, receive, send):
        if scope["type"] == "http":
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [(b"content-type", b"text/plain")],
            })
            await send({
                "type": "http.response.body",
                "body": f"Backend Module Crash:\n{err_msg}".encode("utf-8"),
            })
