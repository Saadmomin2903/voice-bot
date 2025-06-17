"""
FastHTML Voice Bot Frontend
Real-time TTS streaming with optimized HTTP communication
"""

from fasthtml.common import *
import logging
from datetime import datetime
from typing import Optional
from fastapi import HTTPException
import html

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app, rt = fast_app(
    hdrs=(
        # Google Fonts
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=True),
        Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"),
        # Include HTMX for real-time updates
        Script(src="https://unpkg.com/htmx.org@1.9.10"),
        # Include our custom JavaScript
        Script(src="/static/audio-queue.js"),
        Script(src="/static/websocket-client.js"),
        # Custom CSS
        Link(rel="stylesheet", href="/static/styles.css"),
        # Meta tags
        Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        Meta(name="theme-color", content="#0f0f23"),
    )
)

# Configuration
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

USE_HTTPS = os.getenv("USE_HTTPS", "false").lower() == "true"
PROTOCOL = "https" if USE_HTTPS else "http"

# Backend URL configuration for different environments
BACKEND_HOST = os.getenv("BACKEND_HOST", "localhost")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
FASTAPI_HTTP_URL = os.getenv("FASTAPI_HTTP_URL", f"{PROTOCOL}://{BACKEND_HOST}:{BACKEND_PORT}")



@rt("/")
def get():
    """Main voice bot interface"""
    return Titled("AI Voice Assistant",
        Div(
            # Header
            Header(
                H1("AI Voice Assistant", cls="header-title"),
                P("Real-time voice conversations with AI", cls="header-subtitle"),
                cls="app-header"
            ),
            
            # Main container
            Div(
                # Chat interface
                Div(
                    Div(id="chat-messages", cls="chat-messages"),
                    Div(id="typing-indicator", cls="typing-indicator", style="display: none;"),
                    cls="chat-container"
                ),
                
                # Input area
                Div(
                    # Text input
                    Div(
                        Input(
                            type="text",
                            id="message-input",
                            name="message",
                            placeholder="Type your message or use voice...",
                            cls="message-input"
                        ),
                        Button(
                            Span("📤", cls="button-icon"),
                            Span("Send", cls="button-text"),
                            id="send-btn",
                            cls="send-button",
                            hx_post="/send-message",
                            hx_include="#message-input",
                            hx_target="#chat-messages",
                            hx_swap="beforeend"
                        ),
                        cls="text-input-group"
                    ),
                    
                    # Voice controls
                    Div(
                        Button(
                            Span("🎤", cls="button-icon"),
                            Span("Start Recording", cls="button-text"),
                            id="record-btn",
                            cls="voice-button",
                            onclick="toggleRecording()"
                        ),
                        Button(
                            Span("⏹️", cls="button-icon"),
                            Span("Stop Recording", cls="button-text"),
                            id="stop-btn",
                            cls="voice-button stop-button",
                            style="display: none;",
                            onclick="stopRecording()"
                        ),
                        cls="voice-controls"
                    ),
                    
                    cls="input-area"
                ),
                
                # Voice settings
                Div(
                    Details(
                        Summary("🔧 Voice Settings"),
                        Div(
                            Label("Voice:", For="voice-select"),
                            Select(
                                Option("Guy (Professional Male)", value="en-US-GuyNeural", selected=True),
                                Option("Brandon (Conversational Male)", value="en-US-BrandonNeural"),
                                Option("Christopher (Professional Male)", value="en-US-ChristopherNeural"),
                                Option("Davis (Authoritative Male)", value="en-US-DavisNeural"),
                                Option("Eric (Standard Male)", value="en-US-EricNeural"),
                                Option("Jenny (Female)", value="en-US-JennyNeural"),
                                Option("Aria (Female)", value="en-US-AriaNeural"),
                                Option("Ana (Female)", value="en-US-AnaNeural"),
                                id="voice-select",
                                cls="voice-select"
                            ),
                            cls="setting-group"
                        ),
                        Div(
                            Label("Auto TTS:", For="auto-tts"),
                            Input(
                                type="checkbox",
                                id="auto-tts",
                                checked=True,
                                cls="checkbox"
                            ),
                            cls="setting-group"
                        ),
                        Div(
                            Label("Streaming TTS:", For="streaming-tts"),
                            Input(
                                type="checkbox",
                                id="streaming-tts",
                                checked=True,
                                cls="checkbox"
                            ),
                            cls="setting-group"
                        ),
                        cls="voice-settings-content"
                    ),
                    cls="voice-settings"
                ),
                
                # Audio queue status (for debugging)
                Div(
                    id="audio-status",
                    cls="audio-status",
                    style="display: none;"
                ),
                
                cls="main-container"
            ),
            
            # Audio elements container (hidden)
            Div(id="audio-container", style="display: none;"),
            

            
            cls="app-container"
        )
    )

def decode_html_entities(text: str) -> str:
    """Decode HTML entities to make text readable"""
    if not text:
        return ""
    return html.unescape(text)

def sanitize_message_input(message: str) -> str:
    """Enhanced sanitization to prevent XSS and injection attacks"""
    if not message:
        return ""

    import re

    # Remove null bytes and control characters first
    message = message.replace('\x00', '').replace('\x08', '').replace('\x0b', '').replace('\x0c', '')

    # Check for suspicious patterns before processing
    suspicious_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'data:text/html',
        r'vbscript:',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            logger.warning(f"Suspicious content detected in message: {pattern}")
            return ""  # Return empty string for suspicious content

    # Remove HTML tags and potentially dangerous content
    message = re.sub(r'<[^>]*>', '', message)

    # Replace HTML entities
    message = message.replace('<', '&lt;').replace('>', '&gt;')
    message = message.replace('"', '&quot;').replace("'", '&#x27;')
    message = message.replace('&', '&amp;')  # Handle ampersands

    # Limit length
    if len(message) > 2000:
        message = message[:2000]

    return message.strip()

@rt("/send-message")
def post(message: str):
    """Handle text message sending with input sanitization"""
    try:
        logger.info(f"Received message: '{message[:50]}...' (length: {len(message) if message else 0})")

        if not message or not message.strip():
            logger.warning("Empty message received")
            return Div("Please enter a message", cls="error-message")

        # Sanitize input
        sanitized_message = sanitize_message_input(message)
        if not sanitized_message:
            logger.warning("Message became empty after sanitization")
            return Div("Invalid message content", cls="error-message")

        # Add user message to chat
        user_message = Div(
            Div(
                Strong("You:"),
                Span(sanitized_message, cls="message-text"),
                cls="message-content"
            ),
            Div(datetime.now().strftime("%H:%M"), cls="message-time"),
            cls="message user-message"
        )

        # Trigger AI response via HTMX
        import urllib.parse
        encoded_message = urllib.parse.quote(sanitized_message)
        response_id = f"ai-response-{int(datetime.now().timestamp() * 1000)}"

        ai_response_placeholder = Div(
            Div(
                Strong("AI:"),
                Span("⏳ Thinking...", cls="message-text typing-indicator"),
                cls="message-content"
            ),
            Div(datetime.now().strftime("%H:%M"), cls="message-time"),
            cls="message ai-message",
            hx_get=f"/ai-response?message={encoded_message}&response_id={response_id}",
            hx_trigger="load",
            hx_swap="outerHTML"
        )

        # Clear input and return messages
        return Div(
            user_message,
            ai_response_placeholder,
            Script("document.getElementById('message-input').value = '';")
        )

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return Div(
            Div(
                Strong("Error:"),
                Span("Failed to process message. Please try again.", cls="message-text"),
                cls="message-content"
            ),
            Div(datetime.now().strftime("%H:%M"), cls="message-time"),
            cls="message error-message"
        )

@rt("/ai-response")
async def get(message: str = "", response_id: str = ""):
    """Handle AI response generation with direct API call and input validation"""
    try:
        logger.info(f"AI Response endpoint called with message: '{message[:50]}...', response_id: '{response_id}'")

        if not response_id:
            response_id = f"response-{int(datetime.now().timestamp() * 1000)}"

        if not message:
            logger.warning("No message provided to AI response endpoint")
            return Div("No message provided", cls="error-message")

        # Sanitize input
        sanitized_message = sanitize_message_input(message)
        if not sanitized_message:
            logger.warning("Message became empty after sanitization in AI response")
            return Div("Invalid message content", cls="error-message")

        # Import API client
        from utils.api_client import api_client

        # Get AI response directly from FastAPI backend
        result = await api_client.send_chat_message(sanitized_message)

        if result['success']:
            ai_response = result['data']['response']

            # Decode HTML entities to make text readable
            decoded_response = decode_html_entities(ai_response)

            # Generate TTS if needed (using male voice)
            tts_result = await api_client.synthesize_speech(decoded_response, voice="en-US-GuyNeural")
            audio_data = tts_result['data'].get('audio_data') if tts_result['success'] else None

            return Div(
                Div(
                    Strong("AI:"),
                    Span(decoded_response, cls="message-text"),
                    cls="message-content"
                ),
                Div(datetime.now().strftime("%H:%M"), cls="message-time"),
                Div(
                    # Audio player if TTS was successful
                    Audio(
                        Source(src=f"data:audio/wav;base64,{audio_data}", type="audio/wav"),
                        controls=True,
                        autoplay=True,
                        style="width: 100%; margin-top: 0.5rem;"
                    ) if audio_data else Div("🔇 TTS not available", cls="tts-error"),
                    cls="audio-controls"
                ),
                cls="message ai-message"
            )
        else:
            logger.error(f"AI response failed: {result.get('error', 'Unknown error')}")
            return Div(
                Div(
                    Strong("Error:"),
                    Span(f"Failed to get AI response: {result.get('error', 'Unknown error')}", cls="message-text"),
                    cls="message-content"
                ),
                Div(datetime.now().strftime("%H:%M"), cls="message-time"),
                cls="message error-message"
            )

    except Exception as e:
        logger.error(f"Exception in AI response: {str(e)}")
        return Div(
            Div(
                Strong("Error:"),
                Span("An unexpected error occurred. Please try again.", cls="message-text"),
                cls="message-content"
            ),
            Div(datetime.now().strftime("%H:%M"), cls="message-time"),
            cls="message error-message"
        )

@rt("/static/{fname:path}")
def get(fname: str):
    """Serve static files"""
    try:
        from pathlib import Path
        from fastapi.responses import FileResponse

        # Get the current directory and construct the static file path
        current_dir = Path(__file__).parent
        static_file = current_dir / "static" / fname

        if static_file.exists() and static_file.is_file():
            logger.info(f"Serving static file: {fname}")
            return FileResponse(static_file)
        else:
            logger.warning(f"Static file not found: {fname}")
            raise HTTPException(status_code=404, detail=f"Static file not found: {fname}")
    except Exception as e:
        logger.error(f"Error serving static file {fname}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@rt("/health")
def get():
    """Health check endpoint"""
    return {"status": "healthy", "service": "FastHTML Voice Bot Frontend"}

@rt("/api/backend-status")
async def get():
    """Backend status endpoint - proxy to actual backend health check"""
    try:
        from utils.api_client import api_client
        health = await api_client.health_check()
        return {
            "connected": health.get("status") == "healthy",
            "status": health.get("status", "unknown"),
            "service": "Backend Health Check"
        }
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "error": str(e),
            "service": "Backend Health Check"
        }

@rt("/api/voice/transcribe")
async def post(request):
    """Proxy STT requests to backend"""
    try:
        from utils.api_client import api_client

        logger.info("STT proxy called")

        # Get form data from request
        form = await request.form()

        # Extract audio file and language
        audio_file = form.get('audio_file')
        language = form.get('language', 'en-US')

        logger.info(f"Form data: audio_file={audio_file is not None}, language={language}")

        if not audio_file:
            logger.error("No audio file provided to STT proxy")
            return {"error": "No audio file provided"}

        # Read audio data
        audio_data = await audio_file.read()
        logger.info(f"Audio data size: {len(audio_data)} bytes")

        # Call backend STT
        result = await api_client.transcribe_audio(audio_data, language)

        if result['success']:
            logger.info("STT proxy successful")
            return result['data']
        else:
            logger.error(f"STT proxy backend error: {result['error']}")
            return {"error": result['error']}

    except Exception as e:
        logger.error(f"STT proxy failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}



# Utility functions for enhanced HTTP-based communication
def extract_complete_sentence(text: str) -> Optional[str]:
    """Extract complete sentence from text buffer for TTS streaming"""
    sentence_endings = ['.', '!', '?', ';']
    last_sentence_end = -1

    for ending in sentence_endings:
        pos = text.rfind(ending)
        if pos > last_sentence_end:
            last_sentence_end = pos

    if last_sentence_end > 0:
        sentence = text[:last_sentence_end + 1].strip()
        if len(sentence) > 10:  # Only return substantial sentences
            return sentence
    return None





if __name__ == "__main__":
    import uvicorn

    # SSL configuration
    ssl_keyfile = None
    ssl_certfile = None
    if USE_HTTPS:
        ssl_keyfile = "../ssl_certs/key.pem"
        ssl_certfile = "../ssl_certs/cert.pem"
        protocol = "https"
    else:
        protocol = "http"

    print(f"Starting FastHTML Frontend on {protocol}://localhost:8504")
    print(f"Backend URL: {FASTAPI_HTTP_URL}")
    print(f"SSL enabled: {USE_HTTPS}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8504,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile
    )
