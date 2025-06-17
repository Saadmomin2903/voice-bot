"""
Input validation and sanitization utilities for Voice Bot API
Provides comprehensive validation for all user inputs to prevent security vulnerabilities
"""

import re
import html
import bleach
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, validator, Field
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

# Security configuration
MAX_TEXT_LENGTH = 10000
MAX_MESSAGE_LENGTH = 5000
MAX_FILENAME_LENGTH = 255
MAX_CONVERSATION_HISTORY = 50
ALLOWED_AUDIO_FORMATS = ["wav", "mp3", "m4a", "flac", "ogg", "webm", "mp4", "mpeg", "mpga"]
ALLOWED_LANGUAGES = ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "ar", "hi", "tr", "pl", "nl", "sv", "da", "no", "fi"]
ALLOWED_VOICES = [
    "en-US-JennyNeural", "en-US-GuyNeural", "en-US-AriaNeural", "en-US-DavisNeural",
    "en-US-AmberNeural", "en-US-AnaNeural", "en-US-BrandonNeural", "en-US-ChristopherNeural",
    "en-US-CoraNeural", "en-US-ElizabethNeural"
]

# Regex patterns for validation
SAFE_TEXT_PATTERN = re.compile(r'^[a-zA-Z0-9\s\.,\?!\-\'\"\(\)\[\]\{\}:;@#$%&*+=<>/\\|`~_\n\r\t]*$')
FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9\-_\.\s]+$')
LANGUAGE_PATTERN = re.compile(r'^[a-z]{2}(-[A-Z]{2})?$')

class SecurityError(Exception):
    """Custom exception for security-related validation errors"""
    pass

def sanitize_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    """
    Sanitize text input to prevent XSS and injection attacks
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
        
    Raises:
        SecurityError: If text contains malicious content
    """
    if not isinstance(text, str):
        raise SecurityError("Input must be a string")
    
    # Check length
    if len(text) > max_length:
        raise SecurityError(f"Text too long: {len(text)} characters (max: {max_length})")
    
    # Remove null bytes and control characters (except common whitespace)
    text = text.replace('\x00', '').replace('\x08', '').replace('\x0b', '').replace('\x0c', '')
    
    # HTML escape to prevent XSS
    text = html.escape(text, quote=True)
    
    # Additional sanitization with bleach (removes HTML tags)
    text = bleach.clean(text, tags=[], attributes={}, strip=True)
    
    # Validate against safe pattern (optional - can be relaxed based on needs)
    if not SAFE_TEXT_PATTERN.match(text):
        logger.warning(f"Text contains potentially unsafe characters: {text[:100]}...")
        # Don't raise error here as it might be too restrictive for natural language
    
    return text.strip()

def validate_filename(filename: str) -> str:
    """
    Validate and sanitize filename

    Args:
        filename: Input filename

    Returns:
        Sanitized filename

    Raises:
        SecurityError: If filename is invalid
    """
    if not isinstance(filename, str):
        raise SecurityError("Filename must be a string")

    if len(filename) > MAX_FILENAME_LENGTH:
        raise SecurityError(f"Filename too long: {len(filename)} characters (max: {MAX_FILENAME_LENGTH})")

    # Check for path traversal attempts before removing them
    if '..' in filename or '/' in filename or '\\' in filename:
        raise SecurityError(f"Invalid filename contains path traversal: {filename}")

    # Validate pattern
    if not FILENAME_PATTERN.match(filename):
        raise SecurityError(f"Invalid filename format: {filename}")

    return filename.strip()

def validate_audio_format(filename: str) -> str:
    """
    Validate audio file format
    
    Args:
        filename: Audio filename
        
    Returns:
        File extension
        
    Raises:
        SecurityError: If format is not supported
    """
    if not filename:
        raise SecurityError("Filename is required")
    
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if extension not in ALLOWED_AUDIO_FORMATS:
        raise SecurityError(f"Unsupported audio format: {extension}. Allowed: {ALLOWED_AUDIO_FORMATS}")
    
    return extension

def validate_language_code(language: str) -> str:
    """
    Validate language code

    Args:
        language: Language code (e.g., 'en', 'es', 'en-US')

    Returns:
        Validated language code

    Raises:
        SecurityError: If language code is invalid
    """
    if not isinstance(language, str):
        raise SecurityError("Language must be a string")

    language = language.strip()

    # Extract base language code (handle both 'en' and 'en-US' formats)
    base_lang = language.split('-')[0].lower()

    if base_lang not in ALLOWED_LANGUAGES:
        raise SecurityError(f"Unsupported language: {language}. Allowed: {ALLOWED_LANGUAGES}")

    # Allow both 'en' and 'en-US' style codes
    if not re.match(r'^[a-z]{2}(-[A-Z]{2})?$', language):
        # If it doesn't match the full pattern, check if it's just the base language
        if not re.match(r'^[a-z]{2}$', language.lower()):
            raise SecurityError(f"Invalid language code format: {language}")
        language = language.lower()

    return language

def validate_voice_name(voice: Optional[str]) -> Optional[str]:
    """
    Validate TTS voice name
    
    Args:
        voice: Voice name
        
    Returns:
        Validated voice name or None
        
    Raises:
        SecurityError: If voice name is invalid
    """
    if voice is None:
        return None
    
    if not isinstance(voice, str):
        raise SecurityError("Voice must be a string")
    
    voice = voice.strip()
    
    if voice not in ALLOWED_VOICES:
        logger.warning(f"Unknown voice requested: {voice}. Using default.")
        return None  # Use default voice
    
    return voice

def validate_numeric_range(value: Union[int, float], min_val: float, max_val: float, name: str) -> Union[int, float]:
    """
    Validate numeric value within range
    
    Args:
        value: Numeric value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Parameter name for error messages
        
    Returns:
        Validated value
        
    Raises:
        SecurityError: If value is out of range
    """
    if not isinstance(value, (int, float)):
        raise SecurityError(f"{name} must be a number")
    
    if value < min_val or value > max_val:
        raise SecurityError(f"{name} must be between {min_val} and {max_val}, got {value}")
    
    return value

def validate_conversation_history(history: Optional[List[Dict[str, str]]]) -> Optional[List[Dict[str, str]]]:
    """
    Validate conversation history
    
    Args:
        history: List of conversation messages
        
    Returns:
        Validated conversation history
        
    Raises:
        SecurityError: If history is invalid
    """
    if history is None:
        return None
    
    if not isinstance(history, list):
        raise SecurityError("Conversation history must be a list")
    
    if len(history) > MAX_CONVERSATION_HISTORY:
        raise SecurityError(f"Too many messages in history: {len(history)} (max: {MAX_CONVERSATION_HISTORY})")
    
    validated_history = []
    for i, message in enumerate(history):
        if not isinstance(message, dict):
            raise SecurityError(f"Message {i} must be a dictionary")
        
        if 'role' not in message or 'content' not in message:
            raise SecurityError(f"Message {i} must have 'role' and 'content' fields")
        
        role = message['role']
        if role not in ['user', 'assistant', 'system']:
            raise SecurityError(f"Invalid role in message {i}: {role}")
        
        content = sanitize_text(message['content'], MAX_MESSAGE_LENGTH)
        
        validated_history.append({
            'role': role,
            'content': content
        })
    
    return validated_history

# Custom exception handler for validation errors
def handle_validation_error(error: Exception) -> HTTPException:
    """
    Convert validation errors to HTTP exceptions
    
    Args:
        error: Validation error
        
    Returns:
        HTTPException with appropriate status code
    """
    if isinstance(error, SecurityError):
        logger.warning(f"Security validation failed: {error}")
        return HTTPException(status_code=400, detail=f"Validation error: {str(error)}")
    else:
        logger.error(f"Unexpected validation error: {error}")
        return HTTPException(status_code=500, detail="Internal validation error")
