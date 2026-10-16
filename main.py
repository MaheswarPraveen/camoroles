import os
import sys
import uvicorn

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app

if __name__ == "__main__":
    print("Starting Camouroles production server on http://127.0.0.1:8000 ...", flush=True)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")
