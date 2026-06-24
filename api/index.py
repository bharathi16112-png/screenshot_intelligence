import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from main import app
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except Exception as e:
    err_msg = traceback.format_exc()
    print("CRITICAL IMPORT ERROR:\n" + err_msg)
    
    # Fallback ASGI app to render the error
    async def fallback_app(scope, receive, send):
        await send({
            "type": "http.response.start",
            "status": 500,
            "headers": [(b"content-type", b"text/plain")],
        })
        await send({
            "type": "http.response.body",
            "body": f"Backend Module Crash:\n{err_msg}".encode("utf-8"),
        })
    
    # If mangum itself crashed, this will still fail, but if main crashed, this will surface the error
    from mangum import Mangum
    handler = Mangum(fallback_app, lifespan="off")
