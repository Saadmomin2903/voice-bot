"""
Microsoft Edge TTS API integration - Completely FREE
"""
import asyncio
import tempfile
import os
from typing import Optional
import edge_tts

class EdgeTTSModel:
    """Microsoft Edge TTS wrapper - Free, unlimited text-to-speech"""
    
    def __init__(self):
        # TTS configuration
        self.max_input_length = 10000  # Edge TTS can handle long texts
        self.output_format = "wav"
        
        # Available voices by category
        self.voices = {
            "professional": ["en-US-GuyNeural", "en-US-AnaNeural", "en-US-ChristopherNeural"],
            "friendly": ["en-US-AriaNeural", "en-US-CoraNeural", "en-US-AmberNeural"],
            "conversational": ["en-US-JennyNeural", "en-US-BrandonNeural"],
            "authoritative": ["en-US-DavisNeural", "en-US-ElizabethNeural"]
        }
        
        # Default voice (changed to male)
        self.default_voice = "en-US-RogerNeural"  # Professional male voice
        
        # All available English voices
        self.all_voices = [
            "en-US-AriaNeural",      # Female, Friendly
            "en-US-GuyNeural",       # Male, Professional
            "en-US-JennyNeural",     # Female, Conversational
            "en-US-DavisNeural",     # Male, Authoritative
            "en-US-AmberNeural",     # Female, Warm
            "en-US-AnaNeural",       # Female, Professional
            "en-US-BrandonNeural",   # Male, Casual
            "en-US-ChristopherNeural", # Male, Professional
            "en-US-CoraNeural",      # Female, Friendly
            "en-US-ElizabethNeural", # Female, Professional
            "en-US-EricNeural",      # Male, Casual
            "en-US-MichelleNeural",  # Female, Professional
            "en-US-RogerNeural",     # Male, Professional
            "en-US-SteffanNeural"    # Male, Casual
        ]
    
    async def synthesize_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        save_to_file: Optional[str] = None
    ) -> bytes:
        """
        Convert text to speech using Microsoft Edge TTS
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (defaults to en-US-JennyNeural)
            speed: Speech speed (0.5-2.0)
            save_to_file: Optional path to save audio file
            
        Returns:
            Audio data as bytes (WAV format)
        """
        try:
            # Validate and clean input text
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            text = text.strip()
            
            # Validate input length
            if len(text) > self.max_input_length:
                raise ValueError(f"Text length ({len(text)}) exceeds maximum ({self.max_input_length} characters)")
            
            # Use default voice if none specified
            if voice is None:
                voice = self.default_voice
            
            # Map Groq voices to Edge voices if needed
            voice = self._map_voice_name(voice)
            
            # Validate voice
            if voice not in self.all_voices:
                print(f"Warning: Voice '{voice}' not found, using default '{self.default_voice}'")
                voice = self.default_voice
            
            # Convert speed to Edge TTS rate format
            rate = self._convert_speed_to_rate(speed)
            
            print(f"Edge TTS Request: text_len={len(text)}, voice={voice}, rate={rate}")
            
            # Create Edge TTS communicate object
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            
            # Generate audio data
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            # Validate audio data
            if not audio_data or len(audio_data) == 0:
                raise Exception("Received empty audio data from Edge TTS")
            
            # Save to file if requested
            if save_to_file:
                with open(save_to_file, "wb") as f:
                    f.write(audio_data)
            
            return audio_data
            
        except Exception as e:
            # Handle specific error types
            error_msg = str(e)
            
            if "network" in error_msg.lower() or "connection" in error_msg.lower():
                raise Exception(f"Edge TTS network error: {error_msg}. Check internet connection.")
            elif "voice" in error_msg.lower():
                raise Exception(f"Edge TTS voice error: {error_msg}. Voice '{voice}' may not be available.")
            else:
                raise Exception(f"Edge TTS synthesis error: {error_msg}")
    
    def _map_voice_name(self, voice: str) -> str:
        """Map voice names from other providers to Edge TTS format"""
        voice_mapping = {
            # Groq voice names to Edge equivalents
            "Chip-PlayAI": "en-US-BrandonNeural",
            "Fritz-PlayAI": "en-US-GuyNeural",
            "Celeste-PlayAI": "en-US-AriaNeural",
            "Quinn-PlayAI": "en-US-AnaNeural",
            "Atlas-PlayAI": "en-US-DavisNeural",
            "Thunder-PlayAI": "en-US-DavisNeural",
            "Gail-PlayAI": "en-US-CoraNeural",
            "Deedee-PlayAI": "en-US-AmberNeural",
            
            # Google voice names to Edge equivalents
            "en-US-Standard-A": "en-US-AnaNeural",
            "en-US-Standard-B": "en-US-BrandonNeural",
            "en-US-Standard-C": "en-US-AriaNeural",
            "en-US-Standard-D": "en-US-GuyNeural",
            "en-US-Standard-E": "en-US-EricNeural",
            "en-US-Standard-F": "en-US-AmberNeural",
            
            # Simple names
            "male": "en-US-GuyNeural",
            "female": "en-US-JennyNeural",
            "professional": "en-US-GuyNeural",
            "friendly": "en-US-AriaNeural",
            "conversational": "en-US-JennyNeural",

            # Custom name mapping
            "paul": "en-US-GuyNeural",
            "Paul": "en-US-GuyNeural"
        }
        
        return voice_mapping.get(voice, voice)
    
    def _convert_speed_to_rate(self, speed: float) -> str:
        """Convert speed float to Edge TTS rate string"""
        # Edge TTS uses rate format like "+20%" or "-10%"
        if speed == 1.0:
            return "+0%"
        elif speed > 1.0:
            # Speed up
            percentage = int((speed - 1.0) * 100)
            return f"+{percentage}%"
        else:
            # Slow down
            percentage = int((1.0 - speed) * 100)
            return f"-{percentage}%"
    
    def get_available_voices(self, category: str = "all") -> list:
        """Get available TTS voices by category"""
        if category == "all":
            return self.all_voices.copy()
        return self.voices.get(category, [])
    
    def get_voice_recommendations(self) -> dict:
        """Get voice recommendations by use case"""
        return {
            "interview_responses": ["en-US-GuyNeural", "en-US-AnaNeural"],
            "casual_conversation": ["en-US-JennyNeural", "en-US-BrandonNeural"],
            "professional_presentation": ["en-US-GuyNeural", "en-US-ChristopherNeural"],
            "friendly_chat": ["en-US-AriaNeural", "en-US-CoraNeural"]
        }
    
    def validate_text_length(self, text: str) -> bool:
        """Validate if text length is within limits"""
        return len(text) <= self.max_input_length
    
    def get_model_info(self) -> dict:
        """Get information about the current TTS model"""
        return {
            "provider": "Microsoft Edge TTS",
            "default_voice": self.default_voice,
            "max_input_length": self.max_input_length,
            "output_format": self.output_format,
            "available_voices": self.all_voices,
            "voice_categories": list(self.voices.keys()),
            "cost": "FREE - No limits",
            "registration_required": "None",
            "quality": "Neural TTS (Excellent)"
        }

# Global Edge TTS model instance
edge_tts_model = EdgeTTSModel()
