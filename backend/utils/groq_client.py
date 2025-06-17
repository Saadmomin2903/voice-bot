"""
Unified Groq API client for STT, TTS, and Chat functionality
"""
import os
import logging
from typing import Optional, Dict, Any
from groq import Groq
from dotenv import load_dotenv
from utils.api_key_manager import api_key_manager, APIKeySecurityError

load_dotenv()
logger = logging.getLogger(__name__)

class GroqClient:
    """Unified client for all Groq API services with secure key management"""

    def __init__(self, api_key: Optional[str] = None):
        # Use secure API key manager for validation
        try:
            logger.info("Initializing Groq client...")

            if api_key:
                # Validate provided key
                logger.info("Using provided API key")
                if not api_key_manager.validate_api_key_format(api_key, "groq"):
                    raise APIKeySecurityError("Invalid Groq API key format provided")
                self.api_key = api_key
                logger.info(f"Using provided Groq API key: {api_key_manager.mask_api_key(api_key)}")
            else:
                # Get key from environment with validation
                logger.info("Getting API key from environment...")
                self.api_key = api_key_manager.get_secure_key("GROQ_API_KEY")
                logger.info(f"Using Groq API key from environment: {api_key_manager.mask_api_key(self.api_key)}")

            # Initialize Groq client
            logger.info("Creating Groq client instance...")
            self.client = Groq(api_key=self.api_key)
            self.is_configured = True
            logger.info("✅ Groq client initialized successfully")

        except APIKeySecurityError as e:
            logger.error(f"❌ Groq API key security error: {e}")
            self.api_key = None
            self.client = None
            self.is_configured = False
            # Don't raise here to allow graceful degradation
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq client: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.api_key = None
            self.client = None
            self.is_configured = False
        
        # Model configurations
        self.chat_models = {
            "llama3": "llama3-8b-8192",
            "mixtral": "mixtral-8x7b-32768"
        }
        
        self.whisper_models = {
            "turbo": "whisper-large-v3-turbo",  # Fastest (216x real-time)
            "standard": "whisper-large-v3",     # Most accurate
            "distil": "distil-whisper-large-v3-en"  # English-only, cost-effective
        }
        
        self.tts_models = {
            "english": "playai-tts",
            "arabic": "playai-tts-arabic"
        }
        
        # Recommended TTS voices
        self.tts_voices = {
            "professional": ["Fritz-PlayAI", "Quinn-PlayAI"],
            "friendly": ["Celeste-PlayAI", "Deedee-PlayAI"],
            "authoritative": ["Atlas-PlayAI", "Thunder-PlayAI"],
            "conversational": ["Chip-PlayAI", "Gail-PlayAI"]
        }
    
    def get_default_chat_model(self) -> str:
        """Get default chat model"""
        return self.chat_models["llama3"]
    
    def get_default_whisper_model(self) -> str:
        """Get default Whisper model (fastest)"""
        return self.whisper_models["turbo"]
    
    def get_default_tts_model(self) -> str:
        """Get default TTS model"""
        return self.tts_models["english"]
    
    def get_default_voice(self) -> str:
        """Get default TTS voice"""
        return self.tts_voices["conversational"][0]  # Chip-PlayAI
    
    def get_available_voices(self, category: str = "all") -> list:
        """Get available TTS voices by category"""
        if category == "all":
            all_voices = []
            for voices in self.tts_voices.values():
                all_voices.extend(voices)
            return all_voices
        return self.tts_voices.get(category, [])

    def validate_configuration(self) -> dict:
        """
        Validate current Groq client configuration

        Returns:
            Configuration status and details
        """
        if not self.is_configured:
            return {
                "configured": False,
                "error": "Groq client not properly initialized",
                "api_key_status": "invalid_or_missing"
            }

        return {
            "configured": True,
            "api_key_status": "valid",
            "masked_key": api_key_manager.mask_api_key(self.api_key) if self.api_key else "***ERROR***",
            "models": {
                "chat": self.get_default_chat_model(),
                "whisper": self.get_default_whisper_model(),
                "tts": self.get_default_tts_model()
            }
        }

# Global client instance with error handling
try:
    groq_client = GroqClient()
    if groq_client.is_configured:
        logger.info("✅ Groq client initialized successfully")
    else:
        logger.warning("⚠️ Groq client initialized but not configured properly")
except Exception as e:
    logger.error(f"❌ Failed to initialize Groq client: {e}")
    # Create a dummy client for graceful degradation
    groq_client = None
