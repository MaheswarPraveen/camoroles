import sys
import os
import uvicorn

if __name__ == "__main__":
    # Ensure current directory is on pythonpath
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    print("Starting Camouroles server on 0.0.0.0:8000 ...", flush=True)
    print("  Local: http://127.0.0.1:8000", flush=True)
    print("  Phone (Hotspot): http://10.205.207.182:8000", flush=True)
    while True:
        try:
            uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
            break
        except KeyboardInterrupt:
            print("Server stopped by user.", flush=True)
            break
        except Exception as e:
            print(f"Uvicorn encountered an error: {e}. Restarting in 2s...", flush=True)
            time.sleep(2)
