"""
API Client for FastHTML to FastAPI Backend Communication
Handles HTTP requests to FastAPI endpoints
"""

import httpx
import asyncio
import json
import logging
import os
import ssl
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class FastAPIClient:
    """Client for communicating with FastAPI backend"""

    def __init__(self, base_url: str = None):
        # Auto-detect HTTPS or use environment variable
        if base_url is None:
            use_https = os.getenv("USE_HTTPS", "false").lower() == "true"
            protocol = "https" if use_https else "http"
            base_url = f"{protocol}://localhost:8000"

        self.base_url = base_url.rstrip('/')

        # Configure SSL verification properly
        if self.base_url.startswith("https"):
            # Check if we're in development mode with self-signed certificates
            allow_self_signed = os.getenv("ALLOW_SELF_SIGNED_CERTS", "false").lower() == "true"

            if allow_self_signed:
                # Create SSL context that allows self-signed certificates for development
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                logger.warning("⚠️ SSL verification disabled for development. Do not use in production!")

                self.client = httpx.AsyncClient(
                    timeout=30.0,
                    verify=ssl_context
                )
            else:
                # Production-ready SSL verification
                self.client = httpx.AsyncClient(
                    timeout=30.0,
                    verify=True,  # Enable SSL certificate verification
                    trust_env=True  # Use system certificate store
                )
                logger.info("✅ SSL certificate verification enabled")
        else:
            self.client = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check backend health"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def send_chat_message(
        self, 
        message: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """Send chat message to backend"""
        try:
            payload = {
                "message": message,
                "conversation_history": conversation_history or [],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/chat/text",
                json=payload
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
            
        except Exception as e:
            logger.error(f"Chat message failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_streaming_chat_message(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """Send streaming chat message to backend"""
        try:
            payload = {
                "message": message,
                "conversation_history": conversation_history or [],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat/stream",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        try:
                            chunk_data = json.loads(data)
                            if chunk_data.get("done"):
                                break
                            elif "chunk" in chunk_data:
                                yield chunk_data["chunk"]
                            elif "error" in chunk_data:
                                raise Exception(chunk_data["error"])
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Streaming chat failed: {e}")
            yield f"Error: {str(e)}"
    
    async def synthesize_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> Dict[str, Any]:
        """Synthesize speech using backend TTS"""
        try:
            payload = {
                "text": text,
                "voice": voice,
                "speed": speed
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/voice/synthesize",
                json=payload
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
            
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Transcribe audio using backend STT"""
        try:
            files = {
                "audio_file": ("audio.wav", audio_data, "audio/wav")
            }
            data = {
                "language": language
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/voice/transcribe",
                files=files,
                data=data
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """Get available TTS voices from backend"""
        try:
            response = await self.client.get(f"{self.base_url}/api/voice/voices")
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
            
        except Exception as e:
            logger.error(f"Get voices failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def voice_conversation(
        self,
        audio_data: Optional[bytes] = None,
        text: Optional[str] = None,
        voice: Optional[str] = None,
        speed: float = 1.0,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Complete voice conversation workflow"""
        try:
            if audio_data:
                files = {
                    "audio_file": ("audio.wav", audio_data, "audio/wav")
                }
                data = {
                    "voice": voice or "",
                    "speed": speed,
                    "language": language
                }
                
                response = await self.client.post(
                    f"{self.base_url}/api/voice/conversation",
                    files=files,
                    data=data
                )
            elif text:
                data = {
                    "text": text,
                    "voice": voice or "",
                    "speed": speed,
                    "language": language
                }
                
                response = await self.client.post(
                    f"{self.base_url}/api/voice/conversation",
                    data=data
                )
            else:
                return {
                    "success": False,
                    "error": "Either audio_data or text must be provided"
                }
            
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
            
        except Exception as e:
            logger.error(f"Voice conversation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_sample_questions(self) -> Dict[str, Any]:
        """Get sample questions from backend"""
        try:
            response = await self.client.get(f"{self.base_url}/api/chat/sample-questions")
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
            
        except Exception as e:
            logger.error(f"Get sample questions failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {"sample_questions": []}
            }


# Global client instance
api_client = FastAPIClient()

# Utility functions for common operations
async def check_backend_connection() -> bool:
    """Check if backend is accessible"""
    try:
        result = await api_client.health_check()
        return result.get("status") == "healthy"
    except Exception:
        return False

async def get_backend_status() -> Dict[str, Any]:
    """Get detailed backend status"""
    try:
        health = await api_client.health_check()
        voices = await api_client.get_available_voices()
        
        return {
            "health": health,
            "voices_available": voices.get("success", False),
            "voice_count": len(voices.get("data", {}).get("voices", [])) if voices.get("success") else 0,
            "connected": health.get("status") == "healthy"
        }
    except Exception as e:
        return {
            "health": {"status": "error", "error": str(e)},
            "voices_available": False,
            "voice_count": 0,
            "connected": False
        }
