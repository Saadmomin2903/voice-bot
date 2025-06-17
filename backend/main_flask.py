"""
Flask-based Voice Bot Backend with Full Features
Includes Chat, TTS, STT functionality
"""
import os
import json
import base64
import tempfile
import asyncio
from datetime import datetime
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the models and utilities
try:
    from models.groq_chat import groq_chat
    GROQ_CHAT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Groq chat not available: {e}")
    GROQ_CHAT_AVAILABLE = False

try:
    from utils.stt_provider import STTProvider
    stt_provider = STTProvider()
    STT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: STT not available: {e}")
    STT_AVAILABLE = False

try:
    from utils.tts_provider import tts_provider
    TTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: TTS not available: {e}")
    TTS_AVAILABLE = False

try:
    from utils.audio_processor import audio_processor
    AUDIO_PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Audio processor not available: {e}")
    AUDIO_PROCESSOR_AVAILABLE = False

# Create Flask app
app = Flask(__name__)

# Enable CORS
CORS(app, origins="*")

# Helper function to run async functions in Flask
def run_async(coro):
    """Run async function in Flask context"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@app.route("/")
def root():
    """Basic root endpoint"""
    return jsonify({
        "message": "Voice Bot Flask API", 
        "status": "running",
        "framework": "flask"
    })

@app.route("/health")
def health():
    """Basic health check"""
    return jsonify({
        "status": "healthy",
        "message": "Flask API is running",
        "framework": "flask",
        "endpoints_available": [
            "/",
            "/health",
            "/config"
        ]
    })

@app.route("/config")
def config():
    """Full configuration endpoint"""
    return jsonify({
        "framework": "flask",
        "version": "1.0.0",
        "status": "full_functionality",
        "features": {
            "chat": GROQ_CHAT_AVAILABLE,
            "tts": TTS_AVAILABLE,
            "stt": STT_AVAILABLE,
            "voice_conversation": STT_AVAILABLE and GROQ_CHAT_AVAILABLE and TTS_AVAILABLE,
            "audio_processing": AUDIO_PROCESSOR_AVAILABLE
        },
        "groq_models": {
            "chat": ["llama3-8b-8192", "mixtral-8x7b-32768"] if GROQ_CHAT_AVAILABLE else [],
            "whisper": ["whisper-large-v3-turbo", "whisper-large-v3"] if STT_AVAILABLE else [],
            "tts": ["Edge TTS voices"] if TTS_AVAILABLE else []
        },
        "supported_audio_formats": ["flac", "mp3", "mp4", "mpeg", "mpga", "m4a", "ogg", "wav", "webm"],
        "max_audio_file_size_mb": 25,
        "max_tts_text_length": 10000,
        "default_settings": {
            "chat_temperature": 0.7,
            "chat_max_tokens": 500,
            "tts_speed": 1.0,
            "stt_language": "en"
        }
    })

@app.route("/api/chat/text", methods=["POST"])
def chat_text():
    """Full chat endpoint with Groq integration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        message = data.get("message", "")
        if not message:
            return jsonify({"error": "Message is required"}), 400

        conversation_history = data.get("conversation_history", [])
        temperature = data.get("temperature", 0.7)
        max_tokens = data.get("max_tokens", 500)

        if not GROQ_CHAT_AVAILABLE:
            return jsonify({
                "error": "Chat service not available",
                "message": "Groq chat integration not configured"
            }), 503

        # Generate response using Groq
        try:
            ai_response = run_async(groq_chat.generate_response(
                message=message,
                conversation_history=conversation_history,
                temperature=temperature,
                max_tokens=max_tokens
            ))

            response = {
                "response": ai_response,
                "conversation_id": f"conv_{int(datetime.now().timestamp())}",
                "timestamp": datetime.now().isoformat()
            }

            return jsonify(response)

        except Exception as e:
            return jsonify({
                "error": "Chat generation failed",
                "details": str(e)
            }), 500

    except Exception as e:
        return jsonify({"error": f"Request processing failed: {str(e)}"}), 500

@app.route("/api/chat/sample-questions")
def sample_questions():
    """Sample questions endpoint"""
    questions = [
        "What should we know about your life story in a few sentences?",
        "What's your #1 superpower?",
        "What are the top 3 areas you'd like to grow in?",
        "Tell me about a time you overcame a significant challenge.",
        "What motivates you to get up every morning?"
    ]
    return jsonify({"questions": questions})

@app.route("/api/voice/voices")
def get_voices():
    """Get available TTS voices"""
    return jsonify({
        "voices": [
            {"name": "en-US-AriaNeural", "language": "en-US", "gender": "Female"},
            {"name": "en-US-DavisNeural", "language": "en-US", "gender": "Male"},
            {"name": "en-US-JennyNeural", "language": "en-US", "gender": "Female"}
        ],
        "status": "limited_functionality",
        "message": "Flask backend - voice features not fully implemented"
    })

@app.route("/api/voice/synthesize", methods=["POST"])
def synthesize_speech():
    """Full TTS endpoint with Edge TTS integration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        text = data.get("text", "")
        if not text:
            return jsonify({"error": "Text is required"}), 400

        voice = data.get("voice", "en-US-AriaNeural")
        speed = data.get("speed", 1.0)

        if not TTS_AVAILABLE:
            return jsonify({
                "error": "TTS service not available",
                "message": "TTS provider not configured"
            }), 503

        # Generate speech using TTS provider
        try:
            audio_data = run_async(tts_provider.synthesize_speech(
                text=text,
                voice=voice,
                speed=speed
            ))

            if not audio_data:
                return jsonify({"error": "TTS generation failed"}), 500

            # Create audio response
            if AUDIO_PROCESSOR_AVAILABLE:
                audio_response = audio_processor.create_audio_response(
                    audio_data,
                    f"tts_output_{int(datetime.now().timestamp())}.wav"
                )

                return jsonify({
                    "audio_data": audio_response["audio_data"],
                    "filename": audio_response["filename"],
                    "voice_used": voice,
                    "text": text,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # Fallback: return base64 encoded audio
                import base64
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                return jsonify({
                    "audio_data": audio_b64,
                    "filename": f"tts_output_{int(datetime.now().timestamp())}.wav",
                    "voice_used": voice,
                    "text": text,
                    "timestamp": datetime.now().isoformat()
                })

        except Exception as e:
            return jsonify({
                "error": "TTS generation failed",
                "details": str(e)
            }), 500

    except Exception as e:
        return jsonify({"error": f"Request processing failed: {str(e)}"}), 500

@app.route("/api/voice/transcribe", methods=["POST"])
def transcribe_audio():
    """Full STT endpoint with Groq Whisper integration"""
    try:
        # Check if file is in request
        if 'audio_file' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files['audio_file']
        if audio_file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        language = request.form.get('language', 'en-US')

        if not STT_AVAILABLE:
            return jsonify({
                "error": "STT service not available",
                "message": "STT provider not configured"
            }), 503

        # Save uploaded file temporarily
        import tempfile
        import os

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                audio_file.save(temp_file.name)
                temp_file_path = temp_file.name

            # Transcribe audio
            transcribed_text = run_async(stt_provider.transcribe_audio_file(
                audio_file_path=temp_file_path,
                language=language
            ))

            # Clean up temp file
            os.unlink(temp_file_path)

            if not transcribed_text:
                return jsonify({"error": "Transcription failed"}), 500

            return jsonify({
                "transcribed_text": transcribed_text,
                "model_used": f"{stt_provider.current_provider.title()} STT",
                "language": language,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            # Clean up temp file if it exists
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise e

    except Exception as e:
        return jsonify({
            "error": "Transcription failed",
            "details": str(e)
        }), 500

@app.route("/api/voice/conversation", methods=["POST"])
def voice_conversation():
    """Complete voice conversation workflow: STT → Chat → TTS"""
    try:
        # Check if we have required services
        if not (STT_AVAILABLE and GROQ_CHAT_AVAILABLE and TTS_AVAILABLE):
            missing_services = []
            if not STT_AVAILABLE:
                missing_services.append("STT")
            if not GROQ_CHAT_AVAILABLE:
                missing_services.append("Chat")
            if not TTS_AVAILABLE:
                missing_services.append("TTS")

            return jsonify({
                "error": "Voice conversation not available",
                "missing_services": missing_services
            }), 503

        # Get parameters
        voice = request.form.get('voice', 'en-US-AriaNeural')
        speed = float(request.form.get('speed', 1.0))
        language = request.form.get('language', 'en')
        text_input = request.form.get('text')  # Optional text input

        transcribed_text = None

        # Step 1: Handle input (either audio file or text)
        if text_input:
            # Use provided text
            transcribed_text = text_input
        elif 'audio_file' in request.files:
            # Transcribe audio file
            audio_file = request.files['audio_file']
            if audio_file.filename != '':
                import tempfile
                import os

                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    audio_file.save(temp_file.name)
                    temp_file_path = temp_file.name

                try:
                    transcribed_text = run_async(stt_provider.transcribe_audio_file(
                        audio_file_path=temp_file_path,
                        language=language
                    ))
                finally:
                    os.unlink(temp_file_path)

        if not transcribed_text:
            return jsonify({"error": "No input provided (audio file or text required)"}), 400

        # Step 2: Generate AI response
        ai_response = run_async(groq_chat.generate_response(
            message=transcribed_text,
            temperature=0.7,
            max_tokens=500
        ))

        if not ai_response:
            return jsonify({"error": "Failed to generate AI response"}), 500

        # Step 3: Convert response to speech
        audio_data = run_async(tts_provider.synthesize_speech(
            text=ai_response,
            voice=voice,
            speed=speed
        ))

        if not audio_data:
            return jsonify({"error": "Failed to generate speech"}), 500

        # Step 4: Create response
        if AUDIO_PROCESSOR_AVAILABLE:
            audio_response = audio_processor.create_audio_response(
                audio_data,
                f"conversation_response_{int(datetime.now().timestamp())}.wav"
            )

            return jsonify({
                "transcribed_text": transcribed_text,
                "ai_response": ai_response,
                "audio_data": audio_response["audio_data"],
                "filename": audio_response["filename"],
                "voice_used": voice,
                "timestamp": datetime.now().isoformat()
            })
        else:
            # Fallback: return base64 encoded audio
            import base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            return jsonify({
                "transcribed_text": transcribed_text,
                "ai_response": ai_response,
                "audio_data": audio_b64,
                "filename": f"conversation_response_{int(datetime.now().timestamp())}.wav",
                "voice_used": voice,
                "timestamp": datetime.now().isoformat()
            })

    except Exception as e:
        return jsonify({
            "error": "Voice conversation failed",
            "details": str(e)
        }), 500

@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """Streaming chat endpoint"""
    try:
        data = request.get_json()
        message = data.get("message", "")

        if not GROQ_CHAT_AVAILABLE:
            return jsonify({"error": "Chat service not available"}), 503

        # For Flask, we'll return the full response at once
        # (streaming would require more complex setup)
        ai_response = run_async(groq_chat.generate_response(
            message=message,
            conversation_history=data.get("conversation_history", []),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 500)
        ))

        # Return in streaming format expected by frontend
        import json
        return Response(
            f"data: {json.dumps({'chunk': ai_response})}\n\ndata: {json.dumps({'done': True})}\n\n",
            mimetype='text/plain'
        )

    except Exception as e:
        import json
        return Response(
            f"data: {json.dumps({'error': str(e)})}\n\n",
            mimetype='text/plain'
        )

@app.route("/api/voice/models-info")
def get_models_info():
    """Get information about available voice models"""
    try:
        info = {
            "stt_model": {
                "provider": stt_provider.current_provider if STT_AVAILABLE else "not_available",
                "model": "Groq Whisper" if STT_AVAILABLE else "not_available"
            },
            "tts_model": {
                "provider": "Edge TTS" if TTS_AVAILABLE else "not_available",
                "voices_available": True if TTS_AVAILABLE else False
            },
            "chat_model": {
                "provider": "Groq" if GROQ_CHAT_AVAILABLE else "not_available",
                "model": "llama3-8b-8192" if GROQ_CHAT_AVAILABLE else "not_available"
            }
        }
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat/model-info")
def get_chat_model_info():
    """Get chat model information"""
    if not GROQ_CHAT_AVAILABLE:
        return jsonify({"error": "Chat service not available"}), 503

    return jsonify({
        "model": "llama3-8b-8192",
        "provider": "Groq",
        "capabilities": [
            "Conversational responses",
            "Interview-style questions",
            "Personality consistency",
            "Context awareness"
        ],
        "default_temperature": 0.7,
        "default_max_tokens": 500
    })

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"Starting Flask API on http://{host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=False
    )
