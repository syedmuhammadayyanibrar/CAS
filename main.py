"""
Root entrypoint forwarder for Contract Agentic Society (CAS).
Exports 'app' for ASGI/WSGI servers (uvicorn, Vercel, Gunicorn).
"""
from backend.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
