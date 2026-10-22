import os
import sys
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.main import app

if __name__ == "__main__":
    print("Starting Camouroles server on 0.0.0.0:8000 ...", flush=True)
    print("  Local: http://127.0.0.1:8000", flush=True)
    print("  Phone (Hotspot): http://10.205.207.182:8000", flush=True)
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
