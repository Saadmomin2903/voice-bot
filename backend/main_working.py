"""
FastAPI with known working middleware configuration
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Voice Bot Working API",
    description="FastAPI with working middleware configuration",
    version="1.0.0"
)

# Add CORS middleware using the exact pattern from FastAPI docs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    """Root endpoint"""
    return {
        "message": "Voice Bot Working API",
        "status": "running",
        "framework": "fastapi",
        "middleware": "working_configuration"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Working API is running",
        "framework": "fastapi"
    }

@app.get("/config")
async def get_config():
    """Configuration endpoint"""
    return {
        "framework": "fastapi",
        "version": "1.0.0",
        "middleware": "cors_enabled",
        "status": "working"
    }

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"Starting Working FastAPI on http://{host}:{port}")
    
    uvicorn.run(
        "main_working:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
