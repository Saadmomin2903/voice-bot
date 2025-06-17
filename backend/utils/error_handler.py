"""
Standardized error handling system for Voice Bot API
Provides consistent error responses, logging, and exception management
"""

import logging
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# Configure structured logging
logger = logging.getLogger(__name__)

class ErrorCategory(Enum):
    """Error categories for classification"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    RATE_LIMIT = "rate_limit"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL = "internal"
    SECURITY = "security"
    BUSINESS_LOGIC = "business_logic"

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorContext:
    """Context information for errors"""
    request_id: str
    timestamp: str
    path: str
    method: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    user_id: Optional[str] = None

@dataclass
class StandardError:
    """Standardized error response structure"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[str] = None
    context: Optional[ErrorContext] = None
    suggestions: Optional[list] = None
    documentation_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        result = {
            "error_id": self.error_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.context.timestamp if self.context else datetime.now().isoformat()
        }
        
        if self.details:
            result["details"] = self.details
        
        if self.context:
            result["context"] = {
                "request_id": self.context.request_id,
                "path": self.context.path,
                "method": self.context.method
            }
        
        if self.suggestions:
            result["suggestions"] = self.suggestions
        
        if self.documentation_url:
            result["documentation_url"] = self.documentation_url
        
        return result

class ErrorHandler:
    """Centralized error handling and response generation"""
    
    def __init__(self):
        self.error_mappings = {
            # HTTP status codes to error categories
            400: ErrorCategory.VALIDATION,
            401: ErrorCategory.AUTHENTICATION,
            403: ErrorCategory.AUTHORIZATION,
            404: ErrorCategory.NOT_FOUND,
            429: ErrorCategory.RATE_LIMIT,
            500: ErrorCategory.INTERNAL,
            502: ErrorCategory.EXTERNAL_SERVICE,
            503: ErrorCategory.EXTERNAL_SERVICE,
        }
        
        self.severity_mappings = {
            # HTTP status codes to severity levels
            400: ErrorSeverity.LOW,
            401: ErrorSeverity.MEDIUM,
            403: ErrorSeverity.MEDIUM,
            404: ErrorSeverity.LOW,
            429: ErrorSeverity.MEDIUM,
            500: ErrorSeverity.HIGH,
            502: ErrorSeverity.HIGH,
            503: ErrorSeverity.CRITICAL,
        }
    
    def generate_error_id(self) -> str:
        """Generate unique error ID for tracking"""
        return f"err_{uuid.uuid4().hex[:8]}"
    
    def extract_context(self, request: Request) -> ErrorContext:
        """Extract context information from request"""
        return ErrorContext(
            request_id=getattr(request.state, 'request_id', str(uuid.uuid4())),
            timestamp=datetime.now().isoformat(),
            path=str(request.url.path),
            method=request.method,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None
        )
    
    def create_standard_error(
        self,
        status_code: int,
        message: str,
        details: Optional[str] = None,
        context: Optional[ErrorContext] = None,
        suggestions: Optional[list] = None,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None
    ) -> StandardError:
        """Create standardized error object"""
        
        error_category = category or self.error_mappings.get(status_code, ErrorCategory.INTERNAL)
        error_severity = severity or self.severity_mappings.get(status_code, ErrorSeverity.MEDIUM)
        
        return StandardError(
            error_id=self.generate_error_id(),
            category=error_category,
            severity=error_severity,
            message=message,
            details=details,
            context=context,
            suggestions=suggestions or self._get_default_suggestions(status_code),
            documentation_url=self._get_documentation_url(error_category)
        )
    
    def _get_default_suggestions(self, status_code: int) -> list:
        """Get default suggestions based on status code"""
        suggestions_map = {
            400: [
                "Check your request parameters and format",
                "Ensure all required fields are provided",
                "Validate input data types and ranges"
            ],
            401: [
                "Verify your API key is correct and active",
                "Check if your API key has the required permissions",
                "Ensure the API key is properly formatted"
            ],
            403: [
                "Check if you have permission to access this resource",
                "Verify your account has the required subscription level"
            ],
            404: [
                "Check the endpoint URL for typos",
                "Refer to the API documentation for available endpoints",
                "Ensure the resource ID exists"
            ],
            429: [
                "Reduce your request rate",
                "Implement exponential backoff",
                "Consider upgrading your rate limit plan"
            ],
            500: [
                "Try again in a few moments",
                "Check the system status page",
                "Contact support if the issue persists"
            ]
        }
        return suggestions_map.get(status_code, ["Contact support for assistance"])
    
    def _get_documentation_url(self, category: ErrorCategory) -> Optional[str]:
        """Get documentation URL based on error category"""
        base_url = "/docs"  # Could be external documentation URL
        
        doc_map = {
            ErrorCategory.VALIDATION: f"{base_url}#validation",
            ErrorCategory.AUTHENTICATION: f"{base_url}#authentication",
            ErrorCategory.RATE_LIMIT: f"{base_url}#rate-limits",
            ErrorCategory.SECURITY: f"{base_url}#security"
        }
        return doc_map.get(category)
    
    def log_error(self, error: StandardError, exception: Optional[Exception] = None):
        """Log error with structured format"""
        log_data = {
            "error_id": error.error_id,
            "category": error.category.value,
            "severity": error.severity.value,
            "error_message": error.message,  # Renamed to avoid conflict with logging 'message'
            "details": error.details
        }
        
        if error.context:
            log_data.update({
                "request_id": error.context.request_id,
                "path": error.context.path,
                "method": error.context.method,
                "ip_address": error.context.ip_address
            })
        
        if exception:
            log_data["exception_type"] = type(exception).__name__
            log_data["traceback"] = traceback.format_exc()
        
        # Log at appropriate level based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical("Critical error occurred", extra=log_data)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error("High severity error", extra=log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning("Medium severity error", extra=log_data)
        else:
            logger.info("Low severity error", extra=log_data)
    
    def handle_validation_error(self, request: Request, exc: ValidationError) -> JSONResponse:
        """Handle Pydantic validation errors"""
        context = self.extract_context(request)
        
        # Extract validation error details
        error_details = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            error_details.append(f"{field}: {error['msg']}")
        
        details = "; ".join(error_details)
        
        error = self.create_standard_error(
            status_code=422,
            message="Request validation failed",
            details=details,
            context=context,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW
        )
        
        self.log_error(error, exc)
        return JSONResponse(status_code=422, content=error.to_dict())
    
    def handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions"""
        context = self.extract_context(request)
        
        error = self.create_standard_error(
            status_code=exc.status_code,
            message=str(exc.detail),
            context=context
        )
        
        self.log_error(error, exc)
        return JSONResponse(status_code=exc.status_code, content=error.to_dict())
    
    def handle_generic_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions"""
        context = self.extract_context(request)
        
        error = self.create_standard_error(
            status_code=500,
            message="An unexpected error occurred",
            details=f"Internal error: {type(exc).__name__}",
            context=context,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.HIGH
        )
        
        self.log_error(error, exc)
        return JSONResponse(status_code=500, content=error.to_dict())

# Global error handler instance
error_handler = ErrorHandler()
