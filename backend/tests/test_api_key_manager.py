"""
Unit tests for API key management
"""

import os
import pytest
from unittest.mock import patch
from utils.api_key_manager import (
    APIKeyManager, APIKeyStatus, APIKeyInfo, APIKeySecurityError
)

@pytest.mark.unit
class TestAPIKeyManager:
    """Test API key manager functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.manager = APIKeyManager()
    
    def test_validate_groq_key_format(self):
        """Test Groq API key format validation"""
        # Valid Groq key
        valid_key = "gsk_" + "a" * 48
        assert self.manager.validate_api_key_format(valid_key, "groq") is True
        
        # Invalid format
        invalid_keys = [
            "invalid_key",
            "gsk_short",
            "sk_" + "a" * 48,  # OpenAI format
            "",
            None
        ]
        for key in invalid_keys:
            assert self.manager.validate_api_key_format(key, "groq") is False
    
    def test_validate_groq_key_edge_cases(self):
        """Test Groq API key validation edge cases"""
        # Test minimum length
        min_valid_key = "gsk_" + "a" * 48  # Exactly minimum length
        assert self.manager.validate_api_key_format(min_valid_key, "groq") is True

        # Test longer key
        longer_key = "gsk_" + "a" * 60
        assert self.manager.validate_api_key_format(longer_key, "groq") is True

        # Test with mixed case and numbers
        mixed_key = "gsk_" + "A1b2C3d4" * 6  # 48 chars of mixed case/numbers
        assert self.manager.validate_api_key_format(mixed_key, "groq") is True
    
    def test_validate_azure_key_format(self):
        """Test Azure Speech Services API key format validation"""
        # Valid Azure keys (32 hex characters)
        valid_keys = [
            "a" * 32,  # All lowercase
            "A" * 32,  # All uppercase
            "1234567890abcdef1234567890ABCDEF",  # Mixed case with numbers
        ]
        for key in valid_keys:
            assert self.manager.validate_api_key_format(key, "azure") is True

        # Invalid format
        invalid_keys = [
            "a" * 31,  # Too short
            "a" * 33,  # Too long
            "gsk_" + "a" * 48,  # Wrong format
            "gggggggggggggggggggggggggggggggg",  # Invalid hex chars
        ]
        for key in invalid_keys:
            assert self.manager.validate_api_key_format(key, "azure") is False
    
    def test_validate_placeholder_values(self):
        """Test rejection of placeholder values"""
        placeholder_values = [
            "your_api_key_here",
            "your_groq_api_key_here",
            "test",
            "demo",
            "example"
        ]
        
        for placeholder in placeholder_values:
            assert self.manager.validate_api_key_format(placeholder, "groq") is False
    
    def test_mask_api_key(self):
        """Test API key masking"""
        # Normal key
        key = "gsk_1234567890abcdef1234567890abcdef1234567890abcdef"
        masked = self.manager.mask_api_key(key)
        assert masked.startswith("gsk_")
        assert masked.endswith("cdef")
        assert "..." in masked
        assert len(masked) < len(key)
        
        # Short key
        short_key = "short"
        masked_short = self.manager.mask_api_key(short_key)
        assert masked_short == "***INVALID***"
        
        # Empty key
        empty_masked = self.manager.mask_api_key("")
        assert empty_masked == "***INVALID***"
    
    def test_get_api_key_hash(self):
        """Test API key hashing"""
        key = "test_key_123"
        hash1 = self.manager.get_api_key_hash(key)
        hash2 = self.manager.get_api_key_hash(key)
        
        # Same key should produce same hash
        assert hash1 == hash2
        
        # Different keys should produce different hashes
        different_key = "different_key_456"
        hash3 = self.manager.get_api_key_hash(different_key)
        assert hash1 != hash3
        
        # Hash should be hex string
        assert all(c in "0123456789abcdef" for c in hash1)
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "gsk_" + "a" * 48})
    def test_validate_required_keys_valid(self):
        """Test validation of valid required keys"""
        results = self.manager.validate_required_keys()
        
        assert "GROQ_API_KEY" in results
        key_info = results["GROQ_API_KEY"]
        assert key_info.status == APIKeyStatus.VALID
        assert key_info.provider == "groq"
        assert "gsk_" in key_info.masked_key
    
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_required_keys_missing(self):
        """Test validation when required keys are missing"""
        results = self.manager.validate_required_keys()
        
        assert "GROQ_API_KEY" in results
        key_info = results["GROQ_API_KEY"]
        assert key_info.status == APIKeyStatus.MISSING
        assert key_info.masked_key == "***MISSING***"
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "invalid_key"})
    def test_validate_required_keys_invalid(self):
        """Test validation when required keys are invalid"""
        results = self.manager.validate_required_keys()
        
        assert "GROQ_API_KEY" in results
        key_info = results["GROQ_API_KEY"]
        assert key_info.status == APIKeyStatus.INVALID
        assert "Invalid format" in key_info.error_message
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "gsk_" + "a" * 48})
    def test_get_secure_key_valid(self):
        """Test secure key retrieval with valid key"""
        key = self.manager.get_secure_key("GROQ_API_KEY")
        assert key == "gsk_" + "a" * 48
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_secure_key_missing_required(self):
        """Test secure key retrieval with missing required key"""
        with pytest.raises(APIKeySecurityError) as exc_info:
            self.manager.get_secure_key("GROQ_API_KEY")
        assert "missing" in str(exc_info.value)
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "invalid_key"})
    def test_get_secure_key_invalid(self):
        """Test secure key retrieval with invalid key"""
        with pytest.raises(APIKeySecurityError) as exc_info:
            self.manager.get_secure_key("GROQ_API_KEY")
        assert "Invalid API key format" in str(exc_info.value)
    
    @patch.dict(os.environ, {"UNKNOWN_KEY": "some_value"})
    def test_get_secure_key_unknown(self):
        """Test secure key retrieval for unknown key"""
        with pytest.raises(APIKeySecurityError) as exc_info:
            self.manager.get_secure_key("UNKNOWN_KEY")
        assert "Unknown API key type" in str(exc_info.value)
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "gsk_" + "a" * 48})
    def test_check_system_security_high(self):
        """Test system security check with high security"""
        status = self.manager.check_system_security()
        
        assert status["security_level"] == "high"
        assert status["required_keys"]["valid"] == 1
        assert status["required_keys"]["total"] == 1
        assert len(status["recommendations"]) > 0
    
    @patch.dict(os.environ, {}, clear=True)
    def test_check_system_security_low(self):
        """Test system security check with low security"""
        status = self.manager.check_system_security()
        
        assert status["security_level"] == "low"
        assert status["required_keys"]["valid"] == 0
        assert status["required_keys"]["missing"] == 1
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "gsk_" + "a" * 48})
    def test_security_recommendations(self):
        """Test security recommendations generation"""
        status = self.manager.check_system_security()
        recommendations = status["recommendations"]
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Check for common security recommendations
        rec_text = " ".join(recommendations).lower()
        assert any(keyword in rec_text for keyword in [
            "environment", "rotate", "production", "scope", "monitor"
        ])

@pytest.mark.unit
class TestAPIKeyInfo:
    """Test APIKeyInfo dataclass"""
    
    def test_api_key_info_creation(self):
        """Test APIKeyInfo creation"""
        info = APIKeyInfo(
            name="TEST_KEY",
            status=APIKeyStatus.VALID,
            masked_key="test...key",
            provider="test"
        )
        
        assert info.name == "TEST_KEY"
        assert info.status == APIKeyStatus.VALID
        assert info.masked_key == "test...key"
        assert info.provider == "test"
        assert info.last_validated is None
        assert info.error_message is None
    
    def test_api_key_info_with_error(self):
        """Test APIKeyInfo with error message"""
        info = APIKeyInfo(
            name="TEST_KEY",
            status=APIKeyStatus.INVALID,
            masked_key="***INVALID***",
            provider="test",
            error_message="Test error"
        )
        
        assert info.status == APIKeyStatus.INVALID
        assert info.error_message == "Test error"

@pytest.mark.unit
class TestAPIKeyStatus:
    """Test APIKeyStatus enum"""
    
    def test_api_key_status_values(self):
        """Test APIKeyStatus enum values"""
        assert APIKeyStatus.VALID.value == "valid"
        assert APIKeyStatus.INVALID.value == "invalid"
        assert APIKeyStatus.MISSING.value == "missing"
        assert APIKeyStatus.EXPIRED.value == "expired"
        assert APIKeyStatus.RATE_LIMITED.value == "rate_limited"
