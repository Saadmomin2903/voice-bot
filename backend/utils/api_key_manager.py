"""
Secure API Key Management System
Provides validation, secure storage, and proper handling of API keys
"""

import os
import re
import hashlib
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class APIKeyStatus(Enum):
    """API Key validation status"""
    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    EXPIRED = "expired"
    RATE_LIMITED = "rate_limited"

@dataclass
class APIKeyInfo:
    """Information about an API key"""
    name: str
    status: APIKeyStatus
    masked_key: str
    provider: str
    last_validated: Optional[str] = None
    error_message: Optional[str] = None

class APIKeySecurityError(Exception):
    """Custom exception for API key security issues"""
    pass

class APIKeyManager:
    """Secure API key management with validation and monitoring"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # API key patterns for validation (only for services we actually use)
        self.key_patterns = {
            "groq": r"^gsk_[a-zA-Z0-9]{48,}$",  # Groq API key pattern
            "azure": r"^[a-f0-9A-F]{32}$",  # Azure Speech Services key pattern
        }

        # Minimum key lengths for security
        self.min_key_lengths = {
            "groq": 52,
            "azure": 32,
        }

        # Required API keys for the application
        self.required_keys = {
            "GROQ_API_KEY": "groq"
        }

        # Optional API keys (for additional features)
        self.optional_keys = {
            "AZURE_SPEECH_KEY": "azure"
        }
        
        # Cache for validated keys (to avoid repeated validation)
        self._validation_cache = {}
        
        logger.info("API Key Manager initialized")
    
    def validate_api_key_format(self, key: str, provider: str) -> bool:
        """
        Validate API key format based on provider patterns
        
        Args:
            key: API key to validate
            provider: Provider name (groq, openai, azure)
            
        Returns:
            True if format is valid, False otherwise
        """
        if not key or not isinstance(key, str):
            return False
        
        # Check minimum length
        min_length = self.min_key_lengths.get(provider, 32)
        if len(key) < min_length:
            logger.warning(f"API key too short for {provider}: {len(key)} chars (min: {min_length})")
            return False
        
        # Check pattern if available
        pattern = self.key_patterns.get(provider)
        if pattern and not re.match(pattern, key):
            logger.warning(f"API key format invalid for {provider}")
            return False
        
        # Check for common invalid values
        invalid_values = [
            "your_api_key_here",
            "your_groq_api_key_here",
            "your_openai_api_key_here",
            "your_azure_speech_key_here",
            "test",
            "demo",
            "example",
            "",
            "null",
            "undefined"
        ]
        
        if key.lower() in invalid_values:
            logger.warning(f"API key contains placeholder value for {provider}")
            return False
        
        return True
    
    def mask_api_key(self, key: str) -> str:
        """
        Safely mask API key for logging/display
        
        Args:
            key: API key to mask
            
        Returns:
            Masked key string
        """
        if not key or len(key) < 8:
            return "***INVALID***"
        
        # Show first 4 and last 4 characters
        return f"{key[:4]}...{key[-4:]}"
    
    def get_api_key_hash(self, key: str) -> str:
        """
        Generate secure hash of API key for caching/comparison
        
        Args:
            key: API key to hash
            
        Returns:
            SHA256 hash of the key
        """
        return hashlib.sha256(key.encode()).hexdigest()
    
    def validate_required_keys(self) -> Dict[str, APIKeyInfo]:
        """
        Validate all required API keys
        
        Returns:
            Dictionary of key validation results
        """
        results = {}
        
        for env_var, provider in self.required_keys.items():
            key = os.getenv(env_var)
            
            if not key:
                results[env_var] = APIKeyInfo(
                    name=env_var,
                    status=APIKeyStatus.MISSING,
                    masked_key="***MISSING***",
                    provider=provider,
                    error_message=f"Environment variable {env_var} not set"
                )
                logger.error(f"Required API key missing: {env_var}")
                continue
            
            # Validate format
            if self.validate_api_key_format(key, provider):
                results[env_var] = APIKeyInfo(
                    name=env_var,
                    status=APIKeyStatus.VALID,
                    masked_key=self.mask_api_key(key),
                    provider=provider
                )
                logger.info(f"API key validated: {env_var} ({self.mask_api_key(key)})")
            else:
                results[env_var] = APIKeyInfo(
                    name=env_var,
                    status=APIKeyStatus.INVALID,
                    masked_key=self.mask_api_key(key),
                    provider=provider,
                    error_message=f"Invalid format for {provider} API key"
                )
                logger.error(f"Invalid API key format: {env_var}")
        
        return results
    
    def validate_optional_keys(self) -> Dict[str, APIKeyInfo]:
        """
        Validate optional API keys
        
        Returns:
            Dictionary of optional key validation results
        """
        results = {}
        
        for env_var, provider in self.optional_keys.items():
            key = os.getenv(env_var)
            
            if not key:
                results[env_var] = APIKeyInfo(
                    name=env_var,
                    status=APIKeyStatus.MISSING,
                    masked_key="***NOT_SET***",
                    provider=provider,
                    error_message=f"Optional key {env_var} not configured"
                )
                continue
            
            # Validate format
            if self.validate_api_key_format(key, provider):
                results[env_var] = APIKeyInfo(
                    name=env_var,
                    status=APIKeyStatus.VALID,
                    masked_key=self.mask_api_key(key),
                    provider=provider
                )
                logger.info(f"Optional API key validated: {env_var} ({self.mask_api_key(key)})")
            else:
                results[env_var] = APIKeyInfo(
                    name=env_var,
                    status=APIKeyStatus.INVALID,
                    masked_key=self.mask_api_key(key),
                    provider=provider,
                    error_message=f"Invalid format for {provider} API key"
                )
                logger.warning(f"Invalid optional API key format: {env_var}")
        
        return results
    
    def get_secure_key(self, env_var: str) -> Optional[str]:
        """
        Securely retrieve and validate API key
        
        Args:
            env_var: Environment variable name
            
        Returns:
            API key if valid, None otherwise
            
        Raises:
            APIKeySecurityError: If key is invalid or missing
        """
        key = os.getenv(env_var)
        
        if not key:
            if env_var in self.required_keys:
                raise APIKeySecurityError(f"Required API key {env_var} is missing")
            return None
        
        # Get provider for validation
        provider = self.required_keys.get(env_var) or self.optional_keys.get(env_var)
        if not provider:
            raise APIKeySecurityError(f"Unknown API key type: {env_var}")

        # Validate format
        if not self.validate_api_key_format(key, provider):
            raise APIKeySecurityError(f"Invalid API key format for {env_var}")

        return key
    
    def check_system_security(self) -> Dict[str, Any]:
        """
        Comprehensive security check for API key management
        
        Returns:
            Security status report
        """
        required_results = self.validate_required_keys()
        optional_results = self.validate_optional_keys()
        
        # Count statuses
        total_required = len(self.required_keys)
        valid_required = sum(1 for r in required_results.values() if r.status == APIKeyStatus.VALID)
        
        total_optional = len(self.optional_keys)
        valid_optional = sum(1 for r in optional_results.values() if r.status == APIKeyStatus.VALID)
        
        # Determine overall security status
        security_level = "high" if valid_required == total_required else "low"
        if valid_required > 0 and valid_required < total_required:
            security_level = "medium"
        
        return {
            "security_level": security_level,
            "required_keys": {
                "total": total_required,
                "valid": valid_required,
                "missing": sum(1 for r in required_results.values() if r.status == APIKeyStatus.MISSING),
                "invalid": sum(1 for r in required_results.values() if r.status == APIKeyStatus.INVALID),
                "details": {k: {"status": v.status.value, "masked_key": v.masked_key, "provider": v.provider} 
                          for k, v in required_results.items()}
            },
            "optional_keys": {
                "total": total_optional,
                "valid": valid_optional,
                "configured": sum(1 for r in optional_results.values() if r.status != APIKeyStatus.MISSING),
                "details": {k: {"status": v.status.value, "masked_key": v.masked_key, "provider": v.provider} 
                          for k, v in optional_results.items()}
            },
            "recommendations": self._get_security_recommendations(required_results, optional_results)
        }
    
    def _get_security_recommendations(self, required_results: Dict[str, APIKeyInfo], 
                                    optional_results: Dict[str, APIKeyInfo]) -> List[str]:
        """Generate security recommendations based on validation results"""
        recommendations = []
        
        # Check for missing required keys
        missing_required = [k for k, v in required_results.items() if v.status == APIKeyStatus.MISSING]
        if missing_required:
            recommendations.append(f"Configure missing required API keys: {', '.join(missing_required)}")
        
        # Check for invalid required keys
        invalid_required = [k for k, v in required_results.items() if v.status == APIKeyStatus.INVALID]
        if invalid_required:
            recommendations.append(f"Fix invalid required API keys: {', '.join(invalid_required)}")
        
        # Check for invalid optional keys
        invalid_optional = [k for k, v in optional_results.items() if v.status == APIKeyStatus.INVALID]
        if invalid_optional:
            recommendations.append(f"Fix invalid optional API keys: {', '.join(invalid_optional)}")
        
        # General security recommendations
        recommendations.extend([
            "Store API keys in environment variables, never in code",
            "Use different API keys for development and production",
            "Regularly rotate API keys for security",
            "Monitor API key usage for unusual activity",
            "Restrict API key permissions to minimum required scope"
        ])
        
        return recommendations

# Global API key manager instance
api_key_manager = APIKeyManager()
