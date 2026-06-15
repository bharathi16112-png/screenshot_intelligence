import json

def handler(request):
    """Simple health check - no imports needed"""
    body = json.dumps({"status": "ok", "message": "Python is alive on Vercel!"})
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": body
    }
