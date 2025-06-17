"""
WebSocket router for real-time voice communication
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Any
import json
import asyncio
import logging
import html
from datetime import datetime

# Import models and utilities
from models.groq_chat import GroqChatModel
from utils.stt_provider import STTProvider
from utils.tts_provider import TTSProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_data: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_data[websocket] = {
            'connected_at': datetime.now(),
            'conversation_history': [],
            'session_id': f"session_{len(self.active_connections)}_{datetime.now().timestamp()}"
        }
        logger.info(f"New WebSocket connection established. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_data:
            del self.connection_data[websocket]
        logger.info(f"WebSocket connection closed. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connections"""
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

# Global connection manager
manager = ConnectionManager()

# Initialize models
chat_model = GroqChatModel()
stt_provider = STTProvider()
tts_provider = TTSProvider()

@router.websocket("/ws/voice-chat")
async def websocket_voice_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time voice chat"""
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connection_established",
            "message": "WebSocket connection established for real-time voice chat",
            "session_id": manager.connection_data[websocket]['session_id'],
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            await handle_websocket_message(websocket, message_data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Server error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        manager.disconnect(websocket)

async def handle_websocket_message(websocket: WebSocket, message_data: Dict[str, Any]):
    """Handle different types of WebSocket messages"""
    message_type = message_data.get("type")
    
    try:
        if message_type == "text_message":
            await handle_text_message(websocket, message_data)
        
        elif message_type == "audio_data":
            await handle_audio_data(websocket, message_data)
        
        elif message_type == "start_recording":
            await handle_start_recording(websocket, message_data)
        
        elif message_type == "stop_recording":
            await handle_stop_recording(websocket, message_data)
        
        elif message_type == "get_voices":
            await handle_get_voices(websocket, message_data)
        
        elif message_type == "ping":
            await manager.send_personal_message({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }, websocket)
        
        else:
            await manager.send_personal_message({
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.now().isoformat()
            }, websocket)
    
    except Exception as e:
        logger.error(f"Error handling message type {message_type}: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Error processing {message_type}: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }, websocket)

async def handle_text_message(websocket: WebSocket, message_data: Dict[str, Any]):
    """Handle text message and generate AI response"""
    user_message = message_data.get("message", "")
    voice_settings = message_data.get("voice_settings", {})
    
    if not user_message.strip():
        await manager.send_personal_message({
            "type": "error",
            "message": "Empty message received",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        return
    
    # Get conversation history
    conversation_history = manager.connection_data[websocket]['conversation_history']
    
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_message,
        "timestamp": datetime.now().isoformat()
    })
    
    # Send acknowledgment
    await manager.send_personal_message({
        "type": "message_received",
        "message": user_message,
        "timestamp": datetime.now().isoformat()
    }, websocket)
    
    try:
        # Generate AI response
        ai_response = await chat_model.generate_response_async(
            message=user_message,
            conversation_history=conversation_history[-10:],  # Last 10 messages
            temperature=0.7,
            max_tokens=500
        )
        
        if ai_response:
            # Decode HTML entities to make text readable
            decoded_response = html.unescape(ai_response)

            # Add AI response to history
            conversation_history.append({
                "role": "assistant",
                "content": decoded_response,
                "timestamp": datetime.now().isoformat()
            })

            # Send AI response
            await manager.send_personal_message({
                "type": "ai_response",
                "message": decoded_response,
                "timestamp": datetime.now().isoformat()
            }, websocket)

            # Generate TTS if requested
            if voice_settings.get("auto_tts", False):
                await generate_and_send_tts(websocket, decoded_response, voice_settings)
        
        else:
            await manager.send_personal_message({
                "type": "error",
                "message": "Failed to generate AI response",
                "timestamp": datetime.now().isoformat()
            }, websocket)
    
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"AI response error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }, websocket)

async def handle_audio_data(websocket: WebSocket, message_data: Dict[str, Any]):
    """Handle audio data for transcription"""
    audio_data = message_data.get("audio_data")  # Base64 encoded
    language = message_data.get("language", "en-US")
    
    if not audio_data:
        await manager.send_personal_message({
            "type": "error",
            "message": "No audio data received",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        return
    
    try:
        # Send processing status
        await manager.send_personal_message({
            "type": "processing_audio",
            "message": "Transcribing audio...",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        # Transcribe audio
        import base64
        audio_bytes = base64.b64decode(audio_data)
        transcribed_text = await stt_provider.transcribe_audio_data(audio_bytes, "wav", language)
        
        if transcribed_text:
            await manager.send_personal_message({
                "type": "transcription_result",
                "transcribed_text": transcribed_text,
                "timestamp": datetime.now().isoformat()
            }, websocket)
            
            # Automatically process as text message
            await handle_text_message(websocket, {
                "message": transcribed_text,
                "voice_settings": message_data.get("voice_settings", {})
            })
        else:
            await manager.send_personal_message({
                "type": "error",
                "message": "Failed to transcribe audio",
                "timestamp": datetime.now().isoformat()
            }, websocket)
    
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Audio processing error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }, websocket)

async def handle_start_recording(websocket: WebSocket, message_data: Dict[str, Any]):
    """Handle start recording request"""
    await manager.send_personal_message({
        "type": "recording_started",
        "message": "Recording started - speak now",
        "timestamp": datetime.now().isoformat()
    }, websocket)

async def handle_stop_recording(websocket: WebSocket, message_data: Dict[str, Any]):
    """Handle stop recording request"""
    await manager.send_personal_message({
        "type": "recording_stopped",
        "message": "Recording stopped - processing audio",
        "timestamp": datetime.now().isoformat()
    }, websocket)

async def handle_get_voices(websocket: WebSocket, message_data: Dict[str, Any]):
    """Handle get available voices request"""
    try:
        voices_data = await tts_provider.get_available_voices_async()
        await manager.send_personal_message({
            "type": "voices_list",
            "voices_data": voices_data,
            "timestamp": datetime.now().isoformat()
        }, websocket)
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Error getting voices: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }, websocket)

async def generate_and_send_tts(websocket: WebSocket, text: str, voice_settings: Dict[str, Any]):
    """Generate TTS and send audio data"""
    try:
        voice = voice_settings.get("voice")
        speed = voice_settings.get("speed", 1.0)
        
        # Send TTS processing status
        await manager.send_personal_message({
            "type": "generating_tts",
            "message": "Generating speech...",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        # Generate TTS
        audio_data = await tts_provider.synthesize_async(text, voice, speed)
        
        if audio_data:
            await manager.send_personal_message({
                "type": "tts_audio",
                "audio_data": audio_data,  # Base64 encoded
                "text": text,
                "timestamp": datetime.now().isoformat()
            }, websocket)
        else:
            await manager.send_personal_message({
                "type": "tts_error",
                "message": "Failed to generate speech",
                "timestamp": datetime.now().isoformat()
            }, websocket)
    
    except Exception as e:
        logger.error(f"TTS generation error: {e}")
        await manager.send_personal_message({
            "type": "tts_error",
            "message": f"TTS error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }, websocket)

@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket server status"""
    return {
        "active_connections": len(manager.active_connections),
        "websocket_enabled": True,
        "supported_message_types": [
            "text_message",
            "audio_data", 
            "start_recording",
            "stop_recording",
            "get_voices",
            "ping"
        ]
    }
