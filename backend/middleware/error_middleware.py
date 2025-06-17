"""
Error handling middleware for consistent error responses and logging
"""

import uuid
import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError
from utils.error_handler import error_handler, ErrorCategory, ErrorSeverity
from utils.validation import SecurityError
from utils.api_key_manager import APIKeySecurityError

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling and request tracking"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "user_agent": request.headers.get("user-agent"),
                "ip_address": request.client.host if request.client else None
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log successful response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": round(process_time, 3)
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time, 3))
            
            return response
            
        except ValidationError as exc:
            # Handle Pydantic validation errors
            logger.warning(f"Validation error in request {request_id}: {exc}")
            return error_handler.handle_validation_error(request, exc)
            
        except SecurityError as exc:
            # Handle custom security validation errors
            context = error_handler.extract_context(request)
            error = error_handler.create_standard_error(
                status_code=400,
                message="Security validation failed",
                details=str(exc),
                context=context,
                category=ErrorCategory.SECURITY,
                severity=ErrorSeverity.MEDIUM
            )
            error_handler.log_error(error, exc)
            return JSONResponse(status_code=400, content=error.to_dict())
            
        except APIKeySecurityError as exc:
            # Handle API key security errors
            context = error_handler.extract_context(request)
            error = error_handler.create_standard_error(
                status_code=401,
                message="API key validation failed",
                details=str(exc),
                context=context,
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.HIGH
            )
            error_handler.log_error(error, exc)
            return JSONResponse(status_code=401, content=error.to_dict())
            
        except Exception as exc:
            # Handle unexpected exceptions
            logger.error(f"Unexpected error in request {request_id}: {exc}", exc_info=True)
            return error_handler.handle_generic_exception(request, exc)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for detailed request/response logging"""
    
    def __init__(self, app, log_body: bool = False, max_body_size: int = 1024):
        super().__init__(app)
        self.log_body = log_body
        self.max_body_size = max_body_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Log request details
        request_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "path_params": request.path_params,
            "query_params": dict(request.query_params)
        }
        
        # Optionally log request body (be careful with sensitive data)
        if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if len(body) <= self.max_body_size:
                    # Don't log binary data or very large payloads
                    if body and not self._is_binary(body):
                        request_data["body_preview"] = body.decode('utf-8', errors='ignore')[:self.max_body_size]
            except Exception:
                pass  # Skip body logging if there's an issue
        
        logger.debug("Detailed request log", extra=request_data)
        
        # Process request
        response = await call_next(request)
        
        # Log response details
        response_data = {
            "request_id": request_id,
            "status_code": response.status_code,
            "response_headers": dict(response.headers)
        }
        
        logger.debug("Detailed response log", extra=response_data)
        
        return response
    
    def _is_binary(self, data: bytes) -> bool:
        """Check if data appears to be binary"""
        try:
            data.decode('utf-8')
            return False
        except UnicodeDecodeError:
            return True

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for performance monitoring and optimization"""

    def __init__(self, app, slow_request_threshold: float = 3.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold

        # Import performance components
        try:
            from utils.performance_optimizer import performance_monitor, memory_manager
            self.performance_monitor = performance_monitor
            self.memory_manager = memory_manager
            self.performance_enabled = True
        except ImportError:
            self.performance_enabled = False
            logger.warning("Performance optimizer not available")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Check memory before processing request
        if self.performance_enabled:
            await self.memory_manager.cleanup_if_needed()

        response = await call_next(request)

        process_time = time.time() - start_time

        # Record performance metrics
        if self.performance_enabled:
            self.performance_monitor.record_request(process_time)

        # Log slow requests with more detail
        if process_time > self.slow_request_threshold:
            extra_info = {
                "request_id": getattr(request.state, 'request_id', 'unknown'),
                "process_time": round(process_time, 3),
                "threshold": self.slow_request_threshold,
                "method": request.method,
                "path": request.url.path
            }

            # Add memory info if available
            if self.performance_enabled:
                extra_info["memory_usage_mb"] = round(self.memory_manager.get_memory_usage(), 1)

            logger.warning(f"Slow request detected: {request.method} {request.url.path}", extra=extra_info)

        # Add enhanced performance headers
        response.headers["X-Response-Time"] = str(round(process_time * 1000, 2))  # in milliseconds

        if self.performance_enabled:
            response.headers["X-Memory-Usage"] = str(round(self.memory_manager.get_memory_usage(), 1))
            response.headers["X-Request-Count"] = str(self.performance_monitor.metrics.request_count)

        return response
