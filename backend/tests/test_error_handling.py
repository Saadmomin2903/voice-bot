"""
Unit tests for standardized error handling system
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi import Request, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from utils.error_handler import (
    ErrorHandler, StandardError, ErrorCategory, ErrorSeverity, ErrorContext
)
from utils.validation import SecurityError
from utils.api_key_manager import APIKeySecurityError

@pytest.mark.unit
class TestErrorHandler:
    """Test error handler functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.error_handler = ErrorHandler()
    
    def test_generate_error_id(self):
        """Test error ID generation"""
        error_id = self.error_handler.generate_error_id()
        assert error_id.startswith("err_")
        assert len(error_id) == 12  # "err_" + 8 hex chars
        
        # Should generate unique IDs
        error_id2 = self.error_handler.generate_error_id()
        assert error_id != error_id2
    
    def test_extract_context(self):
        """Test context extraction from request"""
        # Mock request
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.method = "POST"
        mock_request.headers = {"user-agent": "test-agent"}
        mock_request.client.host = "127.0.0.1"
        mock_request.state.request_id = "test-request-id"
        
        context = self.error_handler.extract_context(mock_request)
        
        assert context.request_id == "test-request-id"
        assert context.path == "/api/test"
        assert context.method == "POST"
        assert context.user_agent == "test-agent"
        assert context.ip_address == "127.0.0.1"
        assert context.timestamp is not None
    
    def test_create_standard_error(self):
        """Test standard error creation"""
        error = self.error_handler.create_standard_error(
            status_code=400,
            message="Test error message",
            details="Test error details"
        )
        
        assert isinstance(error, StandardError)
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.LOW
        assert error.message == "Test error message"
        assert error.details == "Test error details"
        assert error.error_id.startswith("err_")
    
    def test_create_standard_error_with_custom_category(self):
        """Test standard error creation with custom category"""
        error = self.error_handler.create_standard_error(
            status_code=401,
            message="Authentication failed",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH
        )
        
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.severity == ErrorSeverity.HIGH
    
    def test_get_default_suggestions(self):
        """Test default suggestions generation"""
        suggestions_400 = self.error_handler._get_default_suggestions(400)
        assert "Check your request parameters" in suggestions_400[0]
        
        suggestions_401 = self.error_handler._get_default_suggestions(401)
        assert "API key" in suggestions_401[0]
        
        suggestions_404 = self.error_handler._get_default_suggestions(404)
        assert "endpoint URL" in suggestions_404[0]
        
        suggestions_unknown = self.error_handler._get_default_suggestions(999)
        assert "Contact support" in suggestions_unknown[0]
    
    def test_handle_validation_error(self):
        """Test Pydantic validation error handling"""
        # Mock request
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.method = "POST"
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"
        mock_request.state.request_id = "test-request-id"
        
        # Mock validation error
        mock_error = Mock(spec=ValidationError)
        mock_error.errors.return_value = [
            {"loc": ("field1",), "msg": "field is required"},
            {"loc": ("field2", "nested"), "msg": "invalid value"}
        ]
        
        response = self.error_handler.handle_validation_error(mock_request, mock_error)
        
        assert response.status_code == 422
        content = json.loads(response.body)
        assert content["category"] == "validation"
        assert content["severity"] == "low"
        assert "field1: field is required" in content["details"]
    
    def test_handle_http_exception(self):
        """Test HTTP exception handling"""
        # Mock request
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"
        mock_request.state.request_id = "test-request-id"
        
        # Create HTTP exception
        exc = HTTPException(status_code=404, detail="Resource not found")
        
        response = self.error_handler.handle_http_exception(mock_request, exc)
        
        assert response.status_code == 404
        content = json.loads(response.body)
        assert content["category"] == "not_found"
        assert content["message"] == "Resource not found"
    
    def test_handle_generic_exception(self):
        """Test generic exception handling"""
        # Mock request
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.method = "POST"
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"
        mock_request.state.request_id = "test-request-id"
        
        # Create generic exception
        exc = ValueError("Something went wrong")
        
        response = self.error_handler.handle_generic_exception(mock_request, exc)
        
        assert response.status_code == 500
        content = json.loads(response.body)
        assert content["category"] == "internal"
        assert content["severity"] == "high"
        assert content["message"] == "An unexpected error occurred"

@pytest.mark.unit
class TestStandardError:
    """Test StandardError dataclass"""
    
    def test_standard_error_creation(self):
        """Test StandardError creation"""
        context = ErrorContext(
            request_id="test-id",
            timestamp="2023-01-01T00:00:00Z",
            path="/api/test",
            method="POST"
        )
        
        error = StandardError(
            error_id="err_12345678",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            message="Test error",
            details="Test details",
            context=context,
            suggestions=["Test suggestion"]
        )
        
        assert error.error_id == "err_12345678"
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.message == "Test error"
        assert error.details == "Test details"
        assert error.context == context
        assert error.suggestions == ["Test suggestion"]
    
    def test_standard_error_to_dict(self):
        """Test StandardError to_dict conversion"""
        context = ErrorContext(
            request_id="test-id",
            timestamp="2023-01-01T00:00:00Z",
            path="/api/test",
            method="POST"
        )
        
        error = StandardError(
            error_id="err_12345678",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            message="Test error",
            details="Test details",
            context=context,
            suggestions=["Test suggestion"],
            documentation_url="/docs#validation"
        )
        
        result = error.to_dict()
        
        assert result["error_id"] == "err_12345678"
        assert result["category"] == "validation"
        assert result["severity"] == "medium"
        assert result["message"] == "Test error"
        assert result["details"] == "Test details"
        assert result["suggestions"] == ["Test suggestion"]
        assert result["documentation_url"] == "/docs#validation"
        assert result["context"]["request_id"] == "test-id"
        assert result["context"]["path"] == "/api/test"
        assert result["context"]["method"] == "POST"
    
    def test_standard_error_to_dict_minimal(self):
        """Test StandardError to_dict with minimal data"""
        error = StandardError(
            error_id="err_12345678",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.HIGH,
            message="Test error"
        )
        
        result = error.to_dict()
        
        assert result["error_id"] == "err_12345678"
        assert result["category"] == "internal"
        assert result["severity"] == "high"
        assert result["message"] == "Test error"
        assert "details" not in result
        assert "context" not in result
        assert "suggestions" not in result
        assert "documentation_url" not in result
        assert "timestamp" in result

@pytest.mark.unit
class TestErrorCategories:
    """Test error category and severity enums"""
    
    def test_error_category_values(self):
        """Test ErrorCategory enum values"""
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.AUTHORIZATION.value == "authorization"
        assert ErrorCategory.NOT_FOUND.value == "not_found"
        assert ErrorCategory.RATE_LIMIT.value == "rate_limit"
        assert ErrorCategory.EXTERNAL_SERVICE.value == "external_service"
        assert ErrorCategory.INTERNAL.value == "internal"
        assert ErrorCategory.SECURITY.value == "security"
        assert ErrorCategory.BUSINESS_LOGIC.value == "business_logic"
    
    def test_error_severity_values(self):
        """Test ErrorSeverity enum values"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"
