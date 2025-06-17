"""
Minimal FastAPI backend for Voice Bot application - Deployment Version
Simplified version to resolve middleware compatibility issues
"""
import os
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from routers import chat, voice, websocket

# Create FastAPI app
app = FastAPI(
    title="Voice Bot API",
    description="FastAPI backend for voice-enabled chatbot using Groq APIs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Simple CORS middleware for frontend integration
ALLOWED_ORIGINS = [
    "http://localhost:8504",  # FastHTML frontend
    "http://127.0.0.1:8504",  # Alternative localhost
    "https://localhost:8504",  # HTTPS FastHTML frontend
    "https://127.0.0.1:8504",  # HTTPS Alternative localhost
    "*"  # Allow all origins for deployment (temporary)
]

# Add environment-specific origins
if os.getenv("FRONTEND_URL"):
    ALLOWED_ORIGINS.append(os.getenv("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(voice.router)
app.include_router(websocket.router)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Voice Bot API",
        "version": "1.0.0",
        "description": "FastAPI backend for voice-enabled chatbot using Groq APIs",
        "status": "running",
        "endpoints": {
            "chat": "/api/chat/*",
            "voice": "/api/voice/*",
            "docs": "/docs",
            "health": "/health"
        },
        "features": [
            "Speech-to-Text (Groq Whisper STT)",
            "Text-to-Speech (Multi-provider TTS)",
            "Conversational AI (Groq Chat)",
            "Complete voice conversation workflow"
        ]
    }

@app.get("/health")
async def health_check():
    """Simple health check for the API"""
    try:
        # Basic health check without complex dependencies
        return {
            "status": "healthy",
            "message": "Voice Bot API is operational",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "running",
                "groq_integration": "configured"
            },
            "endpoints_available": [
                "/api/chat/text",
                "/api/voice/transcribe",
                "/api/voice/synthesize",
                "/api/voice/conversation",
                "/api/voice/voices",
                "/ws/voice-chat"
            ]
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": "Health check failed",
                "details": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/config")
async def get_config():
    """Get API configuration information (non-sensitive)"""
    return {
        "groq_models": {
            "chat": ["llama3-8b-8192", "mixtral-8x7b-32768"],
            "whisper": ["whisper-large-v3-turbo", "whisper-large-v3"],
            "tts": ["playai-tts"]
        },
        "supported_audio_formats": ["flac", "mp3", "mp4", "mpeg", "mpga", "m4a", "ogg", "wav", "webm"],
        "max_audio_file_size_mb": 25,
        "max_tts_text_length": 10000,
        "default_settings": {
            "chat_temperature": 0.7,
            "chat_max_tokens": 500,
            "tts_speed": 1.0,
            "stt_language": "en"
        }
    }

# Basic exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested endpoint '{request.url.path}' does not exist",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    print(f"Starting Voice Bot API (Minimal) on http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"API Documentation available at: http://localhost:{port}/docs")

    uvicorn.run(
        "main_minimal:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )
