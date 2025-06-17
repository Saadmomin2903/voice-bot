"""
Integration tests for API endpoints
"""

import pytest
import json
from io import BytesIO
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

@pytest.mark.integration
class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_healthy(self, test_client, mock_api_key_manager):
        """Test health check when system is healthy"""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert data["services"]["api"] == "running"
    
    def test_health_check_unhealthy(self, test_client):
        """Test health check when system is unhealthy"""
        with patch('utils.api_key_manager.api_key_manager') as mock_manager:
            mock_manager.check_system_security.return_value = {
                "security_level": "low",
                "required_keys": {"total": 1, "valid": 0, "missing": 1, "invalid": 0},
                "optional_keys": {"total": 0, "valid": 0, "configured": 0},
                "recommendations": ["Configure missing API keys"]
            }
            
            response = test_client.get("/health")
            
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"

@pytest.mark.integration
class TestChatEndpoints:
    """Test chat API endpoints"""
    
    def test_chat_text_success(self, test_client, mock_groq_client):
        """Test successful text chat"""
        payload = {
            "message": "Hello, how are you?",
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = test_client.post("/api/chat/text", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert isinstance(data["response"], str)
    
    def test_chat_text_with_history(self, test_client, mock_groq_client, sample_conversation_history):
        """Test text chat with conversation history"""
        payload = {
            "message": "Continue our conversation",
            "conversation_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            "temperature": 0.7
        }
        
        response = test_client.post("/api/chat/text", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    def test_chat_text_invalid_input(self, test_client):
        """Test chat with invalid input"""
        # Empty message
        payload = {"message": ""}
        response = test_client.post("/api/chat/text", json=payload)
        assert response.status_code == 422  # Validation error
        
        # Message too long
        payload = {"message": "A" * 10000}
        response = test_client.post("/api/chat/text", json=payload)
        assert response.status_code == 400  # Validation error
    
    def test_chat_text_xss_attempt(self, test_client, mock_groq_client):
        """Test chat with XSS attempt"""
        payload = {
            "message": "<script>alert('xss')</script>Hello",
            "temperature": 0.7
        }
        
        response = test_client.post("/api/chat/text", json=payload)
        
        # Should either succeed with sanitized input or fail with validation error
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            # Message should be sanitized
            data = response.json()
            assert "<script>" not in str(data)
    
    def test_sample_questions(self, test_client):
        """Test sample questions endpoint"""
        response = test_client.get("/api/chat/sample-questions")
        
        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert isinstance(data["questions"], list)
        assert len(data["questions"]) > 0

@pytest.mark.integration
class TestVoiceEndpoints:
    """Test voice API endpoints"""
    
    def test_voice_conversation_with_text(self, test_client, mock_groq_client, mock_tts_provider):
        """Test voice conversation with text input"""
        payload = {
            "text": "Hello, how are you?",
            "voice": "en-US-JennyNeural",
            "speed": 1.0,
            "language": "en"
        }
        
        response = test_client.post("/api/voice/conversation", data=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "ai_response" in data
        assert "audio_data" in data
    
    def test_voice_conversation_with_audio(self, test_client, mock_groq_client, 
                                         mock_tts_provider, mock_stt_provider, 
                                         mock_audio_processor, sample_audio_data):
        """Test voice conversation with audio input"""
        files = {
            "audio_file": ("test.wav", BytesIO(sample_audio_data), "audio/wav")
        }
        data = {
            "voice": "en-US-JennyNeural",
            "speed": 1.0,
            "language": "en"
        }
        
        response = test_client.post("/api/voice/conversation", files=files, data=data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert "transcribed_text" in response_data
        assert "ai_response" in response_data
        assert "audio_data" in response_data
    
    def test_voice_conversation_invalid_audio_format(self, test_client):
        """Test voice conversation with invalid audio format"""
        files = {
            "audio_file": ("test.exe", BytesIO(b"fake data"), "application/octet-stream")
        }
        data = {"language": "en"}
        
        response = test_client.post("/api/voice/conversation", files=files, data=data)
        
        assert response.status_code == 400
    
    def test_voice_conversation_no_input(self, test_client):
        """Test voice conversation with no input"""
        response = test_client.post("/api/voice/conversation", data={})
        
        assert response.status_code == 400
        data = response.json()
        assert "Either audio_file or text must be provided" in data["detail"]
    
    def test_voice_conversation_invalid_parameters(self, test_client):
        """Test voice conversation with invalid parameters"""
        # Invalid speed
        payload = {
            "text": "Hello",
            "speed": 5.0  # Out of range
        }
        
        response = test_client.post("/api/voice/conversation", data=payload)
        assert response.status_code == 400
        
        # Invalid language
        payload = {
            "text": "Hello",
            "language": "invalid_lang"
        }
        
        response = test_client.post("/api/voice/conversation", data=payload)
        assert response.status_code == 400
    
    def test_tts_synthesize(self, test_client, mock_tts_provider):
        """Test TTS synthesis endpoint"""
        payload = {
            "text": "Hello world",
            "voice": "en-US-JennyNeural",
            "speed": 1.0
        }
        
        response = test_client.post("/api/voice/synthesize", json=payload)
        
        assert response.status_code == 200
        # Should return audio data
        assert response.headers["content-type"].startswith("audio/")
    
    def test_get_voices(self, test_client):
        """Test get available voices endpoint"""
        response = test_client.get("/api/voice/voices")
        
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        assert isinstance(data["voices"], list)

@pytest.mark.integration
class TestSecurityEndpoints:
    """Test security-related endpoints"""
    
    def test_api_key_security_status(self, test_client, mock_api_key_manager):
        """Test API key security status endpoint"""
        response = test_client.get("/security/api-keys")
        
        assert response.status_code == 200
        data = response.json()
        assert "security_level" in data
        assert "required_keys" in data
        assert "recommendations" in data
    
    def test_config_endpoint(self, test_client):
        """Test configuration endpoint"""
        response = test_client.get("/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "groq_models" in data
        assert "supported_audio_formats" in data
        assert "default_settings" in data

@pytest.mark.integration
class TestErrorHandling:
    """Test error handling across endpoints"""
    
    def test_404_error(self, test_client):
        """Test 404 error handling"""
        response = test_client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, test_client):
        """Test method not allowed error"""
        response = test_client.delete("/health")
        assert response.status_code == 405
    
    def test_invalid_json(self, test_client):
        """Test invalid JSON handling"""
        response = test_client.post(
            "/api/chat/text",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

@pytest.mark.integration
class TestInputSanitization:
    """Test input sanitization across endpoints"""
    
    def test_sql_injection_attempt(self, test_client, mock_groq_client):
        """Test SQL injection attempt"""
        payload = {
            "message": "'; DROP TABLE users; --",
            "temperature": 0.7
        }
        
        response = test_client.post("/api/chat/text", json=payload)
        
        # Should handle safely
        assert response.status_code in [200, 400]
    
    def test_script_injection_attempt(self, test_client, mock_groq_client):
        """Test script injection attempt"""
        payload = {
            "message": "<script>document.cookie</script>",
            "temperature": 0.7
        }
        
        response = test_client.post("/api/chat/text", json=payload)
        
        # Should sanitize or reject
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "<script>" not in str(data)
    
    def test_path_traversal_attempt(self, test_client, sample_audio_data):
        """Test path traversal attempt in filename"""
        files = {
            "audio_file": ("../../../etc/passwd", BytesIO(sample_audio_data), "audio/wav")
        }
        data = {"text": "backup", "language": "en"}
        
        response = test_client.post("/api/voice/conversation", files=files, data=data)
        
        # Should reject malicious filename
        assert response.status_code == 400
