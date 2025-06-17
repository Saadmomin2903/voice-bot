"""
Direct uvicorn server without proxy headers middleware
"""
import os
import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create the most basic FastAPI app possible
app = FastAPI(title="Voice Bot Direct API")

@app.get("/")
async def root():
    """Basic root endpoint"""
    return {"message": "Voice Bot Direct API", "status": "running"}

@app.get("/health")
async def health():
    """Basic health check"""
    return {"status": "healthy", "message": "Direct API is running"}

async def main():
    """Run the server directly without uvicorn middleware"""
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"Starting Direct API on http://{host}:{port}")
    
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info",
        # Disable proxy headers middleware
        proxy_headers=False,
        forwarded_allow_ips=None,
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
