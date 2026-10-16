import sys
import os
import uvicorn

if __name__ == "__main__":
    # Ensure current directory is on pythonpath
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    print("Starting camOroles server on http://127.0.0.1:8000 ...", flush=True)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")
