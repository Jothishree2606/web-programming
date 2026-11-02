import uvicorn
import os
from api.config import PORT

if __name__ == "__main__":
    port = int(os.getenv("PORT", PORT))
    print(f"[FRYCHO] Starting Backend Server on http://127.0.0.1:{port}")
    print(f"[FRYCHO] Interactive API Docs available at http://127.0.0.1:{port}/api/docs")
    uvicorn.run("api.index:app", host="127.0.0.1", port=port, reload=True)
