"""
Ultra-clean FastAPI backend - Absolute minimum configuration
"""
import os
from fastapi import FastAPI

# Create the most basic FastAPI app possible
app = FastAPI()

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
