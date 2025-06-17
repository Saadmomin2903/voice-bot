"""
Starlette-based backend - Bypass FastAPI middleware issues
"""
import os
import json
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def root(request):
    """Basic root endpoint"""
    return JSONResponse({
        "message": "Voice Bot Starlette API", 
        "status": "running",
        "framework": "starlette"
    })

async def health(request):
    """Basic health check"""
    return JSONResponse({
        "status": "healthy", 
        "message": "Starlette API is running",
        "framework": "starlette"
    })

# Define routes
routes = [
    Route("/", root),
    Route("/health", health),
]

# Define middleware
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

# Create Starlette app
app = Starlette(
    routes=routes,
    middleware=middleware
)

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"Starting Starlette API on http://{host}:{port}")
    
    uvicorn.run(
        "main_starlette:app",
        host=host,
        port=port,
        log_level="info"
    )
