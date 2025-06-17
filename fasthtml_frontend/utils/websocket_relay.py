"""
WebSocket Relay for FastHTML to FastAPI Backend Communication
Handles real-time streaming and TTS audio chunks
"""

import asyncio
import json
import websockets
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketRelay:
    """Relay WebSocket messages between FastHTML frontend and FastAPI backend"""
    
    def __init__(self, backend_url: str = "ws://localhost:8000"):
        self.backend_url = backend_url
        self.active_connections = {}
        self.response_buffers = {}
        
    async def relay_messages(self, frontend_ws, backend_ws):
        """Relay messages between frontend and backend WebSockets"""
        try:
            # Create tasks for both directions
            frontend_to_backend = asyncio.create_task(
                self._forward_frontend_to_backend(frontend_ws, backend_ws)
            )
            backend_to_frontend = asyncio.create_task(
                self._forward_backend_to_frontend(frontend_ws, backend_ws)
            )
            
            # Wait for either task to complete (or fail)
            done, pending = await asyncio.wait(
                [frontend_to_backend, backend_to_frontend],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
        except Exception as e:
            logger.error(f"WebSocket relay error: {e}")
            raise
    
    async def _forward_frontend_to_backend(self, frontend_ws, backend_ws):
        """Forward messages from frontend to backend"""
        try:
            async for message in frontend_ws.iter_json():
                # Process and potentially modify message before forwarding
                processed_message = await self._process_frontend_message(message)
                
                if processed_message:
                    await backend_ws.send(json.dumps(processed_message))
                    logger.debug(f"Forwarded to backend: {processed_message.get('type', 'unknown')}")
                    
        except Exception as e:
            logger.error(f"Frontend to backend relay error: {e}")
            raise
    
    async def _forward_backend_to_frontend(self, frontend_ws, backend_ws):
        """Forward messages from backend to frontend"""
        try:
            async for message in backend_ws:
                data = json.loads(message)
                
                # Process and potentially modify message before forwarding
                processed_messages = await self._process_backend_message(data)
                
                # Send all processed messages to frontend
                for msg in processed_messages:
                    await frontend_ws.send_json(msg)
                    logger.debug(f"Forwarded to frontend: {msg.get('type', 'unknown')}")
                    
        except Exception as e:
            logger.error(f"Backend to frontend relay error: {e}")
            raise
    
    async def _process_frontend_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process messages from frontend before sending to backend"""
        message_type = message.get('type')
        
        if message_type == 'text_message':
            # Add response tracking
            response_id = message.get('response_id')
            if response_id:
                self.response_buffers[response_id] = {
                    'text': '',
                    'audio_chunks': [],
                    'chunk_index': 0
                }
        
        return message
    
    async def _process_backend_message(self, message: Dict[str, Any]) -> list:
        """Process messages from backend before sending to frontend"""
        message_type = message.get('type')
        processed_messages = []
        
        if message_type == 'ai_response':
            # Handle complete AI response
            processed_messages.append(message)
            
        elif message_type == 'ai_response_chunk':
            # Handle streaming AI response chunk
            processed_messages.append(message)
            
            # Check if we should generate TTS for this chunk
            response_id = message.get('response_id')
            chunk_text = message.get('chunk', '')
            
            if response_id and response_id in self.response_buffers:
                buffer = self.response_buffers[response_id]
                buffer['text'] += chunk_text
                
                # Check for complete sentences for TTS
                complete_sentence = self._extract_complete_sentence(buffer['text'])
                if complete_sentence:
                    # Remove the sentence from buffer
                    buffer['text'] = buffer['text'][len(complete_sentence):].strip()
                    
                    # Create TTS audio chunk message (this would be generated by backend)
                    tts_message = {
                        'type': 'tts_audio_chunk',
                        'response_id': response_id,
                        'chunk_index': buffer['chunk_index'],
                        'text': complete_sentence,
                        'audio_data': None,  # Backend should provide this
                        'timestamp': datetime.now().isoformat()
                    }
                    buffer['chunk_index'] += 1
                    
                    # Note: In real implementation, backend should generate TTS
                    # This is just for demonstration of the message flow
        
        elif message_type == 'tts_audio_chunk':
            # Handle TTS audio chunk
            processed_messages.append(message)
            
        elif message_type == 'transcription_result':
            # Handle speech-to-text result
            processed_messages.append(message)
            
        elif message_type == 'error':
            # Handle error messages
            processed_messages.append(message)
            
        else:
            # Forward other messages as-is
            processed_messages.append(message)
        
        return processed_messages
    
    def _extract_complete_sentence(self, text: str) -> Optional[str]:
        """Extract complete sentence from text buffer"""
        sentence_endings = ['.', '!', '?', ';']
        last_sentence_end = -1
        
        for ending in sentence_endings:
            pos = text.rfind(ending)
            if pos > last_sentence_end:
                last_sentence_end = pos
        
        if last_sentence_end > 0:
            sentence = text[:last_sentence_end + 1].strip()
            # Only return if sentence is substantial
            if len(sentence) > 10:
                return sentence
        
        return None
    
    async def connect_to_backend(self, backend_endpoint: str = "/ws/voice-chat"):
        """Connect to FastAPI backend WebSocket"""
        backend_url = f"{self.backend_url}{backend_endpoint}"
        
        try:
            backend_ws = await websockets.connect(backend_url)
            logger.info(f"Connected to backend: {backend_url}")
            return backend_ws
            
        except Exception as e:
            logger.error(f"Failed to connect to backend {backend_url}: {e}")
            raise
    
    def cleanup_response_buffer(self, response_id: str):
        """Clean up response buffer after completion"""
        if response_id in self.response_buffers:
            del self.response_buffers[response_id]
            logger.debug(f"Cleaned up response buffer for {response_id}")


class StreamingTTSHandler:
    """Handle streaming TTS audio chunks for sequential playback"""
    
    def __init__(self):
        self.audio_queues = {}  # response_id -> audio chunks
        
    def add_audio_chunk(self, response_id: str, chunk_index: int, audio_data: str, text: str):
        """Add audio chunk to response queue"""
        if response_id not in self.audio_queues:
            self.audio_queues[response_id] = []
            
        self.audio_queues[response_id].append({
            'chunk_index': chunk_index,
            'audio_data': audio_data,
            'text': text,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.debug(f"Added audio chunk {chunk_index} for response {response_id}")
    
    def get_audio_queue(self, response_id: str) -> list:
        """Get all audio chunks for a response"""
        return self.audio_queues.get(response_id, [])
    
    def clear_audio_queue(self, response_id: str):
        """Clear audio queue for a response"""
        if response_id in self.audio_queues:
            del self.audio_queues[response_id]
            logger.debug(f"Cleared audio queue for response {response_id}")


# Global instances
websocket_relay = WebSocketRelay()
streaming_tts_handler = StreamingTTSHandler()
