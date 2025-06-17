"""
Debug version of FastAPI backend - Absolute minimal configuration
Used to isolate the middleware unpacking error
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create the most basic FastAPI app possible
app = FastAPI(title="Voice Bot Debug API")

# Add only CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Basic root endpoint"""
    return {"message": "Voice Bot Debug API", "status": "running"}

@app.get("/health")
async def health():
    """Basic health check"""
    return {"status": "healthy", "message": "Debug API is running"}

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"Starting Debug API on http://{host}:{port}")
    
    uvicorn.run(
        "main_debug:app",
        host=host,
        port=port,
        log_level="info"
    )
