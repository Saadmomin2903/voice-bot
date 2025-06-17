"""
TTS Provider Manager - Switch between different TTS services
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class TTSProviderManager:
    """Manages multiple TTS providers and switches between them"""
    
    def __init__(self):
        self.current_provider = os.getenv("TTS_PROVIDER", "edge").lower()
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available TTS providers (Edge TTS only)"""
        try:
            # Initialize Edge TTS
            from models.edge_tts import edge_tts_model
            self.providers["edge"] = edge_tts_model
            print("✅ Edge TTS provider initialized")
        except Exception as e:
            print(f"⚠️ Edge TTS provider failed to initialize: {e}")
    
    def get_current_provider(self):
        """Get the current active TTS provider"""
        if self.current_provider in self.providers:
            return self.providers[self.current_provider]
        
        # Fallback to first available provider
        if self.providers:
            fallback_provider = list(self.providers.keys())[0]
            print(f"⚠️ Provider '{self.current_provider}' not available, using '{fallback_provider}'")
            return self.providers[fallback_provider]
        
        raise Exception("No TTS providers available")
    
    def switch_provider(self, provider_name: str):
        """Switch to a different TTS provider"""
        if provider_name.lower() in self.providers:
            self.current_provider = provider_name.lower()
            print(f"✅ Switched to {provider_name} TTS provider")
            return True
        else:
            available = list(self.providers.keys())
            raise Exception(f"Provider '{provider_name}' not available. Available: {available}")
    
    def get_available_providers(self) -> list:
        """Get list of available TTS providers"""
        return list(self.providers.keys())
    
    async def synthesize_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        **kwargs
    ) -> bytes:
        """
        Synthesize speech using the current provider
        
        Args:
            text: Text to convert to speech
            voice: Voice to use
            speed: Speech speed
            **kwargs: Additional provider-specific arguments
            
        Returns:
            Audio data as bytes
        """
        provider = self.get_current_provider()
        
        try:
            return await provider.synthesize_speech(
                text=text,
                voice=voice,
                speed=speed,
                **kwargs
            )
        except Exception as e:
            # Try fallback provider if current one fails
            if len(self.providers) > 1:
                print(f"⚠️ {self.current_provider} TTS failed, trying fallback...")
                return await self._try_fallback_provider(text, voice, speed, **kwargs)
            else:
                raise e
    
    async def _try_fallback_provider(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        **kwargs
    ) -> bytes:
        """Try fallback provider if current one fails"""
        for provider_name, provider in self.providers.items():
            if provider_name != self.current_provider:
                try:
                    print(f"🔄 Trying fallback provider: {provider_name}")
                    
                    # Map voice names between providers if needed
                    mapped_voice = self._map_voice_between_providers(voice, provider_name)
                    
                    return await provider.synthesize_speech(
                        text=text,
                        voice=mapped_voice,
                        speed=speed,
                        **kwargs
                    )
                except Exception as e:
                    print(f"❌ Fallback provider {provider_name} also failed: {e}")
                    continue
        
        raise Exception("All TTS providers failed")
    
    def _map_voice_between_providers(self, voice: str, target_provider: str = None) -> str:
        """Map voice names (simplified for Edge TTS only)"""
        if not voice:
            return "en-US-GuyNeural"  # Default male voice

        # Since we only have Edge TTS, just return the voice or default
        return voice if voice else "en-US-GuyNeural"
    
    def get_available_voices(self, category: str = "all") -> list:
        """Get available voices from current provider"""
        provider = self.get_current_provider()
        if hasattr(provider, 'get_available_voices'):
            return provider.get_available_voices(category)
        return []
    
    def get_provider_info(self) -> dict:
        """Get information about current provider"""
        provider = self.get_current_provider()
        info = {
            "current_provider": self.current_provider,
            "available_providers": self.get_available_providers()
        }
        
        if hasattr(provider, 'get_model_info'):
            info.update(provider.get_model_info())
        
        return info
    
    def validate_text_length(self, text: str) -> bool:
        """Validate text length for current provider"""
        provider = self.get_current_provider()
        if hasattr(provider, 'validate_text_length'):
            return provider.validate_text_length(text)
        return len(text) <= 5000  # Default limit

    async def synthesize_async(self, text: str, voice: Optional[str] = None, speed: float = 1.0) -> str:
        """
        Async wrapper for synthesize_speech that returns base64 encoded audio
        """
        try:
            import base64
            from utils.performance_optimizer import async_optimizer, memory_manager

            # Use performance-optimized async execution
            audio_bytes = await async_optimizer.run_in_thread(
                self.synthesize_speech, text, voice, speed
            )

            # Cache audio for potential reuse
            cache_key = f"tts_{hash(text)}_{voice}_{speed}"
            memory_manager.cache_audio(cache_key, audio_bytes, {
                'text': text[:100],  # Store first 100 chars for debugging
                'voice': voice,
                'speed': speed
            })

            return base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            raise Exception(f"TTS synthesis error: {str(e)}")

    async def get_available_voices_async(self) -> dict:
        """
        Async wrapper for get_available_voices
        """
        try:
            provider = self.get_current_provider()
            voices_data = {
                "all_voices": self.get_available_voices(),
                "provider": self.current_provider,
                "default_voice": getattr(provider, 'default_voice', 'default')
            }

            if hasattr(provider, 'get_voices_by_category'):
                voices_data["voices_by_category"] = provider.get_voices_by_category()

            return voices_data
        except Exception as e:
            return {
                "all_voices": [],
                "provider": "unknown",
                "default_voice": "default",
                "error": str(e)
            }

# Create alias for backward compatibility
TTSProvider = TTSProviderManager

# Global TTS provider manager
tts_provider = TTSProviderManager()
