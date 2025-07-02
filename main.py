
import uvicorn
from auth.app import app  # Ensure correct import

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
