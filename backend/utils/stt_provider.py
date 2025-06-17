"""
Groq Speech-to-Text Provider
Simplified STT provider using only Groq Whisper
"""

from typing import Optional, Dict, Any
from models.groq_stt import groq_stt

class STTProvider:
    """Unified STT provider with multiple backends"""
    
    def __init__(self):
        # Available STT providers (simplified to Groq only)
        self.providers = {
            "groq": groq_stt
        }

        # Use Groq as the only provider
        self.primary_provider = "groq"
        self.current_provider = self.primary_provider

        print(f"🎤 STT Provider initialized: {self.current_provider}")

        # Provider priority for fallback (only Groq available)
        self.provider_priority = ["groq"]
    
    def _determine_primary_provider(self) -> str:
        """Determine which STT provider to use as primary (Groq only)"""
        return "groq"
    
    async def transcribe_audio_file(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio file using current provider with fallback
        
        Args:
            audio_file_path: Path to audio file
            language: Language code
            
        Returns:
            Transcribed text
        """
        # Try current provider first
        try:
            provider = self.providers[self.current_provider]
            
            # Convert language format if needed
            formatted_language = self._format_language_for_provider(language, self.current_provider)
            
            result = await provider.transcribe_audio_file(audio_file_path, formatted_language)
            print(f"✅ STT successful with {self.current_provider}: '{result[:50]}...'")
            return result
            
        except Exception as e:
            print(f"❌ STT failed with {self.current_provider}: {e}")
            
            # Try fallback providers
            return await self._try_fallback_providers(audio_file_path, language)
    
    async def transcribe_audio_data(
        self,
        audio_data: bytes,
        format: str = "wav",
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio data using current provider with fallback
        
        Args:
            audio_data: Audio data as bytes
            format: Audio format
            language: Language code
            
        Returns:
            Transcribed text
        """
        # Try current provider first
        try:
            provider = self.providers[self.current_provider]
            
            # Convert language format if needed
            formatted_language = self._format_language_for_provider(language, self.current_provider)
            
            result = await provider.transcribe_audio_data(audio_data, format, formatted_language)
            print(f"✅ STT successful with {self.current_provider}: '{result[:50]}...'")
            return result
            
        except Exception as e:
            print(f"❌ STT failed with {self.current_provider}: {e}")
            
            # Try fallback providers
            return await self._try_fallback_providers_data(audio_data, format, language)
    
    async def _try_fallback_providers(self, audio_file_path: str, language: Optional[str]) -> str:
        """Try fallback providers for audio file"""
        for provider_name in self.provider_priority:
            if provider_name != self.current_provider:
                try:
                    print(f"🔄 Trying fallback STT provider: {provider_name}")
                    provider = self.providers[provider_name]
                    
                    # Convert language format if needed
                    formatted_language = self._format_language_for_provider(language, provider_name)
                    
                    result = await provider.transcribe_audio_file(audio_file_path, formatted_language)
                    print(f"✅ Fallback STT successful with {provider_name}")
                    return result
                    
                except Exception as e:
                    print(f"❌ Fallback STT provider {provider_name} also failed: {e}")
                    continue
        
        # If all providers fail, return a helpful error message
        raise Exception("All STT providers failed. Please check your API keys and try again.")
    
    async def _try_fallback_providers_data(self, audio_data: bytes, format: str, language: Optional[str]) -> str:
        """Try fallback providers for audio data"""
        for provider_name in self.provider_priority:
            if provider_name != self.current_provider:
                try:
                    print(f"🔄 Trying fallback STT provider: {provider_name}")
                    provider = self.providers[provider_name]
                    
                    # Convert language format if needed
                    formatted_language = self._format_language_for_provider(language, provider_name)
                    
                    result = await provider.transcribe_audio_data(audio_data, format, formatted_language)
                    print(f"✅ Fallback STT successful with {provider_name}")
                    return result
                    
                except Exception as e:
                    print(f"❌ Fallback STT provider {provider_name} also failed: {e}")
                    continue
        
        # If all providers fail, return a helpful error message
        raise Exception("All STT providers failed. Please check your API keys and try again.")
    
    def _format_language_for_provider(self, language: Optional[str], provider_name: str) -> Optional[str]:
        """Format language code for Groq provider"""
        if not language:
            return None

        # Groq expects simple language codes (e.g., "en")
        if "-" in language:
            return language.split("-")[0]  # Extract language part
        return language
    
    def validate_audio_file(self, file_path: str) -> bool:
        """Validate audio file using current provider"""
        try:
            provider = self.providers[self.current_provider]
            return provider.validate_audio_file(file_path)
        except Exception:
            return False
    
    def get_supported_formats(self) -> list:
        """Get supported formats from current provider"""
        try:
            provider = self.providers[self.current_provider]
            return provider.supported_formats
        except Exception:
            return ["wav", "mp3", "m4a"]
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about current STT provider"""
        try:
            provider = self.providers[self.current_provider]
            info = provider.get_model_info()
            info["current_provider"] = self.current_provider
            info["available_providers"] = list(self.providers.keys())
            info["configured_providers"] = [
                name for name, provider in self.providers.items() 
                if provider.is_configured
            ]
            return info
        except Exception as e:
            return {
                "current_provider": self.current_provider,
                "error": str(e),
                "available_providers": list(self.providers.keys())
            }
    
    def switch_provider(self, provider_name: str) -> bool:
        """Switch to a different STT provider"""
        if provider_name in self.providers:
            self.current_provider = provider_name
            print(f"🔄 Switched STT provider to: {provider_name}")
            return True
        return False
    
    def get_current_provider(self):
        """Get current provider instance"""
        return self.providers.get(self.current_provider)

# Global STT provider instance
stt_provider = STTProvider()
