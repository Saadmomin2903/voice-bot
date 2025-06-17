"""
Unit tests for input validation utilities
"""

import pytest
from utils.validation import (
    sanitize_text, validate_filename, validate_audio_format,
    validate_language_code, validate_voice_name, validate_numeric_range,
    validate_conversation_history, SecurityError, handle_validation_error
)
from fastapi import HTTPException

@pytest.mark.unit
class TestTextSanitization:
    """Test text sanitization functionality"""
    
    def test_sanitize_normal_text(self):
        """Test sanitization of normal text"""
        text = "Hello world! This is a normal message."
        result = sanitize_text(text)
        assert result == "Hello world! This is a normal message."
    
    def test_sanitize_html_content(self):
        """Test sanitization of HTML content"""
        text = "<script>alert('xss')</script>Hello"
        result = sanitize_text(text)
        assert "<script>" not in result
        # Note: HTML escaping preserves content but makes it safe
        assert "&lt;script&gt;" in result or "script" not in result
        assert "Hello" in result
    
    def test_sanitize_special_characters(self):
        """Test sanitization of special characters"""
        text = "Text with 'quotes' and \"double quotes\" & ampersands"
        result = sanitize_text(text)
        assert "&quot;" in result or "&#x27;" in result
        assert "&amp;" in result
    
    def test_sanitize_null_bytes(self):
        """Test removal of null bytes and control characters"""
        text = "Text\x00with\x08null\x0bbytes"
        result = sanitize_text(text)
        assert "\x00" not in result
        assert "\x08" not in result
        assert "\x0b" not in result
        # The word "null" remains in the text after sanitization
        assert "Textwithnullbytes" in result
    
    def test_sanitize_text_too_long(self):
        """Test handling of text that's too long"""
        text = "A" * 10001
        with pytest.raises(SecurityError) as exc_info:
            sanitize_text(text, max_length=10000)
        assert "too long" in str(exc_info.value)
    
    def test_sanitize_non_string_input(self):
        """Test handling of non-string input"""
        with pytest.raises(SecurityError) as exc_info:
            sanitize_text(123)
        assert "must be a string" in str(exc_info.value)

@pytest.mark.unit
class TestFilenameValidation:
    """Test filename validation functionality"""
    
    def test_validate_normal_filename(self):
        """Test validation of normal filename"""
        filename = "audio_file.wav"
        result = validate_filename(filename)
        assert result == "audio_file.wav"
    
    def test_validate_filename_with_spaces(self):
        """Test validation of filename with spaces"""
        filename = "my audio file.mp3"
        result = validate_filename(filename)
        assert result == "my audio file.mp3"
    
    def test_validate_filename_path_traversal(self):
        """Test rejection of path traversal attempts"""
        filenames = ["../../../etc/passwd", "..\\windows\\system32", "file/../other"]
        for filename in filenames:
            with pytest.raises(SecurityError) as exc_info:
                validate_filename(filename)
            assert "path traversal" in str(exc_info.value)
    
    def test_validate_filename_invalid_characters(self):
        """Test rejection of invalid characters"""
        filename = "file<script>.wav"
        with pytest.raises(SecurityError) as exc_info:
            validate_filename(filename)
        assert "Invalid filename format" in str(exc_info.value)
    
    def test_validate_filename_too_long(self):
        """Test rejection of too long filename"""
        filename = "a" * 300 + ".wav"
        with pytest.raises(SecurityError) as exc_info:
            validate_filename(filename)
        assert "too long" in str(exc_info.value)
    
    def test_validate_filename_non_string(self):
        """Test rejection of non-string filename"""
        with pytest.raises(SecurityError) as exc_info:
            validate_filename(123)
        assert "must be a string" in str(exc_info.value)

@pytest.mark.unit
class TestAudioFormatValidation:
    """Test audio format validation functionality"""
    
    def test_validate_supported_formats(self):
        """Test validation of supported audio formats"""
        supported_formats = ["test.wav", "audio.mp3", "file.flac", "sound.ogg"]
        for filename in supported_formats:
            result = validate_audio_format(filename)
            assert result in ["wav", "mp3", "flac", "ogg"]
    
    def test_validate_unsupported_format(self):
        """Test rejection of unsupported formats"""
        unsupported_formats = ["file.exe", "script.php", "document.pdf"]
        for filename in unsupported_formats:
            with pytest.raises(SecurityError) as exc_info:
                validate_audio_format(filename)
            assert "Unsupported audio format" in str(exc_info.value)
    
    def test_validate_no_extension(self):
        """Test handling of filename without extension"""
        with pytest.raises(SecurityError) as exc_info:
            validate_audio_format("filename_without_extension")
        assert "Unsupported audio format" in str(exc_info.value)
    
    def test_validate_empty_filename(self):
        """Test handling of empty filename"""
        with pytest.raises(SecurityError) as exc_info:
            validate_audio_format("")
        assert "required" in str(exc_info.value)

@pytest.mark.unit
class TestLanguageCodeValidation:
    """Test language code validation functionality"""
    
    def test_validate_supported_languages(self):
        """Test validation of supported language codes"""
        supported_langs = ["en", "es", "fr", "de", "en-US", "es-ES"]
        for lang in supported_langs:
            result = validate_language_code(lang)
            assert result.lower().startswith(lang.split('-')[0].lower())
    
    def test_validate_unsupported_language(self):
        """Test rejection of unsupported languages"""
        with pytest.raises(SecurityError) as exc_info:
            validate_language_code("xx")
        assert "Unsupported language" in str(exc_info.value)
    
    def test_validate_invalid_format(self):
        """Test rejection of invalid language code format"""
        invalid_codes = ["english", "123", "en-us-extra"]
        for code in invalid_codes:
            with pytest.raises(SecurityError) as exc_info:
                validate_language_code(code)
            assert "Invalid language code format" in str(exc_info.value) or "Unsupported language" in str(exc_info.value)
    
    def test_validate_non_string_language(self):
        """Test rejection of non-string language code"""
        with pytest.raises(SecurityError) as exc_info:
            validate_language_code(123)
        assert "must be a string" in str(exc_info.value)

@pytest.mark.unit
class TestNumericRangeValidation:
    """Test numeric range validation functionality"""
    
    def test_validate_valid_ranges(self):
        """Test validation of values within valid ranges"""
        assert validate_numeric_range(0.7, 0.0, 2.0, "temperature") == 0.7
        assert validate_numeric_range(1.0, 0.5, 2.0, "speed") == 1.0
        assert validate_numeric_range(500, 1, 4000, "tokens") == 500
    
    def test_validate_out_of_range(self):
        """Test rejection of values outside valid ranges"""
        with pytest.raises(SecurityError) as exc_info:
            validate_numeric_range(2.5, 0.0, 2.0, "temperature")
        assert "must be between" in str(exc_info.value)
        
        with pytest.raises(SecurityError) as exc_info:
            validate_numeric_range(-0.1, 0.0, 2.0, "temperature")
        assert "must be between" in str(exc_info.value)
    
    def test_validate_non_numeric(self):
        """Test rejection of non-numeric values"""
        with pytest.raises(SecurityError) as exc_info:
            validate_numeric_range("invalid", 0.0, 2.0, "temperature")
        assert "must be a number" in str(exc_info.value)

@pytest.mark.unit
class TestConversationHistoryValidation:
    """Test conversation history validation functionality"""
    
    def test_validate_valid_history(self):
        """Test validation of valid conversation history"""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        result = validate_conversation_history(history)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
    
    def test_validate_empty_history(self):
        """Test handling of empty/None history"""
        assert validate_conversation_history(None) is None
        assert validate_conversation_history([]) == []
    
    def test_validate_invalid_role(self):
        """Test rejection of invalid roles"""
        history = [{"role": "invalid", "content": "Hello"}]
        with pytest.raises(SecurityError) as exc_info:
            validate_conversation_history(history)
        assert "Invalid role" in str(exc_info.value)
    
    def test_validate_missing_fields(self):
        """Test rejection of messages with missing fields"""
        history = [{"role": "user"}]  # Missing content
        with pytest.raises(SecurityError) as exc_info:
            validate_conversation_history(history)
        assert "must have 'role' and 'content' fields" in str(exc_info.value)
    
    def test_validate_too_many_messages(self):
        """Test rejection of too many messages"""
        history = [{"role": "user", "content": f"Message {i}"} for i in range(60)]
        with pytest.raises(SecurityError) as exc_info:
            validate_conversation_history(history)
        assert "Too many messages" in str(exc_info.value)
    
    def test_validate_non_list_history(self):
        """Test rejection of non-list history"""
        with pytest.raises(SecurityError) as exc_info:
            validate_conversation_history("invalid")
        assert "must be a list" in str(exc_info.value)

@pytest.mark.unit
class TestErrorHandling:
    """Test error handling functionality"""
    
    def test_handle_security_error(self):
        """Test handling of SecurityError"""
        error = SecurityError("Test security error")
        result = handle_validation_error(error)
        assert isinstance(result, HTTPException)
        assert result.status_code == 400
        assert "Validation error" in result.detail
    
    def test_handle_unexpected_error(self):
        """Test handling of unexpected errors"""
        error = ValueError("Unexpected error")
        result = handle_validation_error(error)
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
        assert "Internal validation error" in result.detail
