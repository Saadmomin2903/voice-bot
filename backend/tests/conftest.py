"""
Pytest configuration and shared fixtures
"""

import os
import sys
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import httpx

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set test environment variables before importing modules
os.environ["TESTING"] = "true"
os.environ["GROQ_API_KEY"] = "gsk_test_key_" + "a" * 48  # Valid test key format
os.environ["AZURE_SPEECH_KEY"] = "test_azure_key_12345678901234567890"
os.environ["AZURE_SPEECH_REGION"] = "eastus"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_groq_client():
    """Mock Groq client for testing"""
    with patch('utils.groq_client.Groq') as mock_groq:
        mock_client = Mock()
        mock_groq.return_value = mock_client
        
        # Mock chat completion
        mock_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Test response from AI"))]
        )
        
        # Mock transcription
        mock_client.audio.transcriptions.create.return_value = Mock(
            text="Test transcription result"
        )
        
        yield mock_client

@pytest.fixture
def mock_api_key_manager():
    """Mock API key manager for testing"""
    with patch('utils.api_key_manager.api_key_manager') as mock_manager:
        mock_manager.validate_api_key_format.return_value = True
        mock_manager.get_secure_key.return_value = "gsk_test_key_" + "a" * 48
        mock_manager.mask_api_key.return_value = "gsk_...test"
        mock_manager.check_system_security.return_value = {
            "security_level": "high",
            "required_keys": {
                "total": 1,
                "valid": 1,
                "missing": 0,
                "invalid": 0,
                "details": {
                    "GROQ_API_KEY": {
                        "status": "valid",
                        "masked_key": "gsk_...test",
                        "provider": "groq"
                    }
                }
            },
            "optional_keys": {
                "total": 2,
                "valid": 0,
                "configured": 0,
                "details": {}
            },
            "recommendations": ["All systems secure"]
        }
        yield mock_manager

@pytest.fixture
def test_client():
    """Create test client for FastAPI app"""
    from main import app
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Create async test client for FastAPI app"""
    from main import app
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def sample_audio_data():
    """Sample audio data for testing"""
    # Create minimal WAV file header + some data
    wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
    audio_data = b'\x00\x00' * 1000  # Some sample audio data
    return wav_header + audio_data

@pytest.fixture
def sample_conversation_history():
    """Sample conversation history for testing"""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there! How can I help you?"},
        {"role": "user", "content": "What's the weather like?"}
    ]

@pytest.fixture
def mock_audio_processor():
    """Mock audio processor for testing"""
    with patch('utils.audio_processor.audio_processor') as mock_processor:
        mock_processor.save_uploaded_audio.return_value = "/tmp/test_audio.wav"
        mock_processor.create_audio_response.return_value = {
            "audio_data": b"fake_audio_data",
            "filename": "test_response.wav"
        }
        mock_processor.cleanup_temp_file.return_value = None
        yield mock_processor

@pytest.fixture
def mock_tts_provider():
    """Mock TTS provider for testing"""
    with patch('utils.tts_provider.tts_provider') as mock_tts:
        mock_tts.synthesize_speech.return_value = b"fake_tts_audio_data"
        mock_tts.get_provider_info.return_value = {
            "name": "test_tts",
            "default_voice": "test_voice"
        }
        yield mock_tts

@pytest.fixture
def mock_stt_provider():
    """Mock STT provider for testing"""
    with patch('utils.stt_provider.stt_provider') as mock_stt:
        mock_stt.transcribe_audio_file.return_value = "Test transcription"
        mock_stt.providers = {
            "groq": Mock(
                validate_audio_file=Mock(return_value=True),
                supported_formats=["wav", "mp3", "flac"]
            )
        }
        mock_stt.current_provider = "groq"
        yield mock_stt

@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def temp_audio_file(tmp_path, sample_audio_data):
    """Create temporary audio file for testing"""
    audio_file = tmp_path / "test_audio.wav"
    audio_file.write_bytes(sample_audio_data)
    return str(audio_file)

# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

# Async test configuration
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
