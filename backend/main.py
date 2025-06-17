"""
FastAPI backend for Voice Bot application
"""
import os
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv

# Configure structured logging first
from utils.logging_config import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

# Import error handling
from utils.error_handler import error_handler
# Temporarily disable middleware imports for deployment debugging
# from middleware.error_middleware import (
#     ErrorHandlingMiddleware,
#     RequestLoggingMiddleware,
#     SecurityHeadersMiddleware,
#     PerformanceMonitoringMiddleware
# )

# Rate limiting imports
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    logger.warning("Rate limiting not available. Install slowapi for production use.")

# Load environment variables
load_dotenv()

# Import routers
from routers import chat, voice, websocket

# Initialize rate limiter
if RATE_LIMITING_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
else:
    limiter = None

# Create FastAPI app
app = FastAPI(
    title="Voice Bot API",
    description="FastAPI backend for voice-enabled chatbot using Groq APIs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware in correct order (last added = first executed)
# Simplified middleware for deployment
try:
    # Only add essential middleware for now
    logger.info("Loading essential middleware only for deployment")
except Exception as e:
    logger.warning(f"Middleware loading error: {e}")
    # Continue without problematic middleware

# Add rate limiting middleware if available
if RATE_LIMITING_AVAILABLE and limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware for frontend integration
# Production-ready CORS configuration
ALLOWED_ORIGINS = [
    "http://localhost:8504",  # FastHTML frontend
    "http://127.0.0.1:8504",  # Alternative localhost
    "https://localhost:8504",  # HTTPS FastHTML frontend
    "https://127.0.0.1:8504",  # HTTPS Alternative localhost
    "http://localhost:3000",  # Development frontend
    "http://127.0.0.1:3000",  # Alternative development
    "https://localhost:3000",  # HTTPS Development frontend
    "https://127.0.0.1:3000",  # HTTPS Alternative development
]

# Add environment-specific origins
if os.getenv("FRONTEND_URL"):
    ALLOWED_ORIGINS.append(os.getenv("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
)

# Include routers
app.include_router(chat.router)
app.include_router(voice.router)
app.include_router(websocket.router)

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Voice Bot API",
        "version": "1.0.0",
        "description": "FastAPI backend for voice-enabled chatbot using Groq APIs",
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

# Input sanitization utility
def sanitize_text_input(text: str, max_length: int = 10000) -> str:
    """Sanitize text input to prevent XSS and other attacks"""
    if not text:
        return ""

    # Basic HTML/script tag removal
    import re
    text = re.sub(r'<[^>]*>', '', text)

    # Remove potentially dangerous characters
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('"', '&quot;').replace("'", '&#x27;')

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    return text.strip()

@app.get("/health")
async def health_check(request: Request):
    """
    Overall health check for the API
    """
    # Apply rate limiting if available
    if RATE_LIMITING_AVAILABLE and limiter:
        try:
            await limiter.limit("30/minute")(request)
        except:
            pass  # Continue without rate limiting if it fails

    try:
        # Use secure API key manager for health check
        from utils.api_key_manager import api_key_manager

        security_status = api_key_manager.check_system_security()

        # Check if required keys are properly configured
        required_keys_valid = security_status["required_keys"]["valid"]
        required_keys_total = security_status["required_keys"]["total"]

        if required_keys_valid == 0:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": "No valid API keys configured",
                    "security_level": security_status["security_level"],
                    "services": {
                        "api": "running",
                        "groq_integration": "not_configured"
                    },
                    "recommendations": security_status["recommendations"][:3]  # Show top 3 recommendations
                }
            )
        elif required_keys_valid < required_keys_total:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "degraded",
                    "error": f"Only {required_keys_valid}/{required_keys_total} required API keys are valid",
                    "security_level": security_status["security_level"],
                    "services": {
                        "api": "running",
                        "groq_integration": "partial"
                    },
                    "recommendations": security_status["recommendations"][:3]
                }
            )

        return {
            "status": "healthy",
            "message": "Voice Bot API is operational",
            "security_level": security_status["security_level"],
            "services": {
                "api": "running",
                "groq_integration": "configured"
            },
            "api_keys": {
                "required_valid": f"{required_keys_valid}/{required_keys_total}",
                "optional_configured": security_status["optional_keys"]["configured"]
            },
            "endpoints_available": [
                "/api/chat/text",
                "/api/chat/sample-questions",
                "/api/voice/transcribe",
                "/api/voice/synthesize",
                "/api/voice/conversation",
                "/api/voice/voices",
                "/ws/voice-chat",
                "/ws/status"
            ]
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": "Health check failed",
                "details": str(e),
                "services": {
                    "api": "running",
                    "groq_integration": "error"
                }
            }
        )

@app.get("/config")
async def get_config():
    """
    Get API configuration information (non-sensitive)
    """
    return {
        "groq_models": {
            "chat": ["llama3-8b-8192", "mixtral-8x7b-32768"],
            "whisper": ["whisper-large-v3-turbo", "whisper-large-v3", "distil-whisper-large-v3-en"],
            "tts": ["playai-tts", "playai-tts-arabic"]
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

@app.get("/security/api-keys")
async def get_api_key_security_status(request: Request):
    """
    Get API key security status (admin endpoint)
    """
    # Apply rate limiting if available
    if RATE_LIMITING_AVAILABLE and limiter:
        try:
            await limiter.limit("10/minute")(request)
        except:
            pass  # Continue without rate limiting if it fails

    try:
        from utils.api_key_manager import api_key_manager

        security_status = api_key_manager.check_system_security()

        # Remove sensitive details for API response
        safe_status = {
            "security_level": security_status["security_level"],
            "required_keys": {
                "total": security_status["required_keys"]["total"],
                "valid": security_status["required_keys"]["valid"],
                "missing": security_status["required_keys"]["missing"],
                "invalid": security_status["required_keys"]["invalid"]
            },
            "optional_keys": {
                "total": security_status["optional_keys"]["total"],
                "valid": security_status["optional_keys"]["valid"],
                "configured": security_status["optional_keys"]["configured"]
            },
            "recommendations": security_status["recommendations"],
            "timestamp": datetime.now().isoformat()
        }

        # Add masked key information (safe to expose)
        safe_status["key_details"] = {}
        for key_name, details in security_status["required_keys"]["details"].items():
            safe_status["key_details"][key_name] = {
                "status": details["status"],
                "masked_key": details["masked_key"],
                "provider": details["provider"]
            }

        return safe_status

    except Exception as e:
        logger.error(f"Error getting API key security status: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to get security status",
                "details": str(e)
            }
        )

@app.get("/performance")
async def get_performance_metrics():
    """
    Get system performance metrics and statistics
    """
    try:
        from utils.performance_optimizer import performance_monitor, memory_manager

        # Get comprehensive performance report
        performance_report = performance_monitor.get_performance_report()

        # Add memory management stats
        memory_stats = {
            "current_usage_mb": round(memory_manager.get_memory_usage(), 1),
            "max_memory_mb": memory_manager.max_memory_mb,
            "memory_pressure": memory_manager.check_memory_pressure(),
            "cached_audio_files": len(memory_manager.audio_cache),
            "cache_size_limit": memory_manager.cache_size_limit
        }

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "performance": performance_report,
            "memory": memory_stats,
            "optimization": {
                "async_optimization": True,
                "memory_management": True,
                "performance_monitoring": True
            }
        }

    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return {
            "status": "error",
            "error": "Performance metrics unavailable",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Standardized exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors with standardized response"""
    from utils.error_handler import ErrorCategory, ErrorSeverity

    context = error_handler.extract_context(request)
    error = error_handler.create_standard_error(
        status_code=404,
        message="Endpoint not found",
        details=f"The requested endpoint '{request.url.path}' does not exist",
        context=context,
        category=ErrorCategory.NOT_FOUND,
        severity=ErrorSeverity.LOW,
        suggestions=[
            "Check the endpoint URL for typos",
            "Refer to the API documentation at /docs",
            "Ensure you're using the correct HTTP method"
        ]
    )

    error_handler.log_error(error, exc)
    return JSONResponse(status_code=404, content=error.to_dict())

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors with standardized response"""
    return error_handler.handle_generic_exception(request, exc)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions with standardized response"""
    return error_handler.handle_http_exception(request, exc)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with standardized response"""
    return error_handler.handle_validation_error(request, exc)

if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    use_ssl = os.getenv("USE_SSL", "false").lower() == "true"

    # SSL configuration
    ssl_keyfile = None
    ssl_certfile = None
    if use_ssl:
        ssl_keyfile = "../ssl_certs/key.pem"
        ssl_certfile = "../ssl_certs/cert.pem"
        protocol = "https"
    else:
        protocol = "http"

    print(f"Starting Voice Bot API on {protocol}://{host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"SSL enabled: {use_ssl}")
    print(f"API Documentation available at: {protocol}://localhost:{port}/docs")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug",
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile
    )
