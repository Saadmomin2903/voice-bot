"""
Clean FastAPI backend - Absolute minimal version for debugging middleware issues
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create the most basic FastAPI app possible
app = FastAPI(title="Voice Bot Clean API")

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
    return {"message": "Voice Bot Clean API", "status": "running"}

@app.get("/health")
async def health():
    """Basic health check"""
    return {"status": "healthy", "message": "Clean API is running"}

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"Starting Clean API on http://{host}:{port}")
    
    uvicorn.run(
        "main_clean:app",
        host=host,
        port=port,
        log_level="info"
    )
