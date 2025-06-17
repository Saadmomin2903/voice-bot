"""
Groq STT (Speech-to-Text) integration using Whisper models
"""
import os
import tempfile
import asyncio
from typing import Optional, Union
from utils.groq_client import groq_client
from dotenv import load_dotenv

load_dotenv()

class GroqSTTModel:
    """Groq Whisper STT wrapper for speech-to-text conversion"""
    
    def __init__(self):
        self.client = groq_client.client
        self.model = groq_client.get_default_whisper_model()  # whisper-large-v3-turbo
        
        # STT configuration
        self.supported_formats = ["wav", "mp3", "m4a", "flac", "ogg", "webm"]
        self.max_file_size = 25 * 1024 * 1024  # 25MB limit
        
        # Check if Groq is configured
        self.api_key = groq_client.api_key
        self.is_configured = (
            self.api_key and
            self.api_key != "your_groq_api_key_here" and
            len(self.api_key.strip()) > 0
        )
        
        if not self.is_configured:
            print("⚠️ Groq STT not configured. STT will use mock responses.")
            print("💡 To enable Groq STT:")
            print("   1. Get Groq API key from https://console.groq.com/")
            print("   2. Set GROQ_API_KEY in .env file")
        else:
            print(f"✅ Groq Whisper STT configured with model: {self.model}")
    
    def _mock_transcription(self, identifier: str) -> str:
        """Generate mock transcription for testing"""
        mock_responses = [
            "Hello, this is a test transcription.",
            "The quick brown fox jumps over the lazy dog.",
            "Testing speech to text functionality.",
            "This is a mock response for audio transcription.",
            "Voice recognition is working in test mode."
        ]
        # Use hash of identifier to get consistent mock response
        index = hash(identifier) % len(mock_responses)
        return mock_responses[index]
    
    def validate_audio_file(self, file_path: str) -> bool:
        """
        Validate audio file format and size
        
        Args:
            file_path: Path to audio file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                print(f"❌ File too large: {file_size} bytes (max: {self.max_file_size})")
                return False
            
            # Check file extension
            file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
            if file_ext not in self.supported_formats:
                print(f"❌ Unsupported format: {file_ext} (supported: {self.supported_formats})")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ File validation error: {e}")
            return False

    async def transcribe_audio_file(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio file to text using Groq Whisper
        
        Args:
            audio_file_path: Path to audio file
            language: Optional language code (ISO-639-1 format like 'en', 'es', 'fr')
            
        Returns:
            Transcribed text
        """
        # Check if Groq is configured
        if not self.is_configured:
            print(f"🔄 Using mock transcription for: {audio_file_path}")
            return self._mock_transcription(audio_file_path)
        
        try:
            # Validate audio file
            if not self.validate_audio_file(audio_file_path):
                raise Exception(f"Invalid audio file: {audio_file_path}")
            
            print(f"Groq Whisper: Transcribing audio file: {audio_file_path}")
            
            # Open and transcribe the audio file
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model=self.model,
                    language=language,  # Optional: specify language
                    response_format="text"
                )
            
            # Handle different response formats
            if hasattr(transcript, 'text'):
                transcribed_text = transcript.text.strip()
            else:
                # If response is just a string
                transcribed_text = str(transcript).strip()
            
            print(f"Groq Whisper: Transcription successful: '{transcribed_text}'")
            return transcribed_text
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Groq STT transcription failed: {error_msg}")
            
            # Return mock response on error for development
            if "mock" in error_msg.lower() or not self.is_configured:
                return self._mock_transcription(audio_file_path)
            else:
                raise Exception(f"Groq STT transcription error: {error_msg}")

    async def transcribe_audio_data(
        self,
        audio_data: bytes,
        format: str = "wav",
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio data to text using Groq Whisper
        
        Args:
            audio_data: Audio data as bytes
            format: Audio format (wav, mp3, etc.)
            language: Optional language code
            
        Returns:
            Transcribed text
        """
        # Check if Groq is configured
        if not self.is_configured:
            print(f"🔄 Using mock transcription for audio data ({len(audio_data)} bytes)")
            return self._mock_transcription("audio_data")
        
        try:
            # Validate audio data size
            if len(audio_data) > self.max_file_size:
                raise Exception(f"Audio data too large: {len(audio_data)} bytes (max: {self.max_file_size})")
            
            # Create temporary file for audio data
            with tempfile.NamedTemporaryFile(suffix=f'.{format}', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Transcribe using the temporary file
                result = await self.transcribe_audio_file(temp_file_path, language)
                return result
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Groq STT audio data transcription failed: {error_msg}")
            
            # Return mock response on error for development
            if "mock" in error_msg.lower() or not self.is_configured:
                return self._mock_transcription("audio_data")
            else:
                raise Exception(f"Groq STT audio data error: {error_msg}")

    def get_model_info(self) -> dict:
        """Get information about the Groq Whisper model"""
        return {
            "provider": "Groq",
            "model": self.model,
            "service": "Whisper STT",
            "supported_formats": self.supported_formats,
            "max_file_size_mb": self.max_file_size // (1024 * 1024),
            "features": [
                "High-speed transcription (216x real-time)",
                "Multi-language support",
                "High accuracy",
                "Cost-effective"
            ],
            "languages": [
                "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
                "ar", "hi", "tr", "pl", "nl", "sv", "da", "no", "fi"
            ]
        }

    def get_supported_languages(self) -> list:
        """Get list of supported language codes"""
        return [
            "en",  # English
            "es",  # Spanish
            "fr",  # French
            "de",  # German
            "it",  # Italian
            "pt",  # Portuguese
            "ru",  # Russian
            "ja",  # Japanese
            "ko",  # Korean
            "zh",  # Chinese
            "ar",  # Arabic
            "hi",  # Hindi
            "tr",  # Turkish
            "pl",  # Polish
            "nl",  # Dutch
            "sv",  # Swedish
            "da",  # Danish
            "no",  # Norwegian
            "fi"   # Finnish
        ]

    async def transcribe_audio_async(self, audio_data: bytes, language: str = "en") -> str:
        """
        Async wrapper for transcribe_audio_data for WebSocket support
        """
        return await self.transcribe_audio_data(audio_data, "wav", language)

# Global Groq STT model instance
groq_stt = GroqSTTModel()
