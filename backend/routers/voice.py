"""
Voice API endpoints for speech-to-text and text-to-speech
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from utils.stt_provider import STTProvider
from models.groq_chat import groq_chat
from utils.audio_processor import audio_processor
from utils.tts_provider import tts_provider
from utils.validation import (
    sanitize_text, validate_filename, validate_audio_format, validate_language_code,
    validate_voice_name, validate_numeric_range, SecurityError, MAX_TEXT_LENGTH
)
import logging
import html

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Initialize STT provider
stt_provider = STTProvider()

class TranscriptionResponse(BaseModel):
    transcribed_text: str = Field(..., description="Transcribed text from audio")
    model_used: str = Field(..., description="STT model used for transcription")
    language: str = Field(..., description="Language detected/used")

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH, description="Text to synthesize")
    voice: Optional[str] = Field(None, description="TTS voice to use")
    speed: Optional[float] = Field(1.0, ge=0.5, le=2.0, description="Speech speed (0.5-2.0)")

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        try:
            return sanitize_text(v, MAX_TEXT_LENGTH)
        except SecurityError as e:
            raise ValueError(str(e))

    @field_validator('voice')
    @classmethod
    def validate_voice(cls, v):
        if v is None:
            return v
        try:
            return validate_voice_name(v)
        except SecurityError as e:
            raise ValueError(str(e))

class TTSResponse(BaseModel):
    audio_data: str  # Base64 encoded audio
    filename: str
    format: str
    size_bytes: int
    voice_used: str

class VoiceConversationRequest(BaseModel):
    text: Optional[str] = None  # For text input
    voice: Optional[str] = None
    speed: Optional[float] = 1.0
    conversation_history: Optional[list] = None

class VoiceConversationResponse(BaseModel):
    transcribed_text: Optional[str] = None
    ai_response: str
    audio_data: str  # Base64 encoded audio response
    filename: str
    voice_used: str

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: str = Form("en-US")
):
    """
    Convert speech to text using Groq Whisper STT

    Args:
        audio_file: Audio file to transcribe
        language: Language code (default: 'en-US')

    Returns:
        Transcribed text and metadata
    """
    temp_file_path = None
    try:
        # Check file extension from filename
        if audio_file.filename:
            file_extension = audio_file.filename.lower().split('.')[-1]
            current_provider = stt_provider.providers[stt_provider.current_provider]
            if file_extension not in current_provider.supported_formats:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported audio format: {file_extension}. Supported formats: {current_provider.supported_formats}"
                )

        # Save uploaded file to temporary location
        audio_data = await audio_file.read()

        # Check file size
        current_provider = stt_provider.providers[stt_provider.current_provider]
        if len(audio_data) > current_provider.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {len(audio_data)} bytes. Maximum: {current_provider.max_file_size} bytes"
            )

        temp_file_path = audio_processor.save_uploaded_audio(audio_data, audio_file.filename or "audio.wav")

        # Additional validation after saving
        if not current_provider.validate_audio_file(temp_file_path):
            raise HTTPException(status_code=400, detail="Invalid audio file format or corrupted file")

        # Transcribe audio
        transcribed_text = await stt_provider.transcribe_audio_file(
            audio_file_path=temp_file_path,
            language=language
        )

        return TranscriptionResponse(
            transcribed_text=transcribed_text,
            model_used=f"{stt_provider.current_provider.title()} STT",
            language=language
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_file_path:
            audio_processor.cleanup_temp_file(temp_file_path)

@router.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """
    Convert text to speech using Edge TTS

    Args:
        request: TTS request with text and voice options

    Returns:
        Audio data and metadata
    """
    try:
        # Validate text length
        if not tts_provider.validate_text_length(request.text):
            provider_info = tts_provider.get_provider_info()
            max_length = provider_info.get('max_input_length', 5000)
            raise HTTPException(
                status_code=400,
                detail=f"Text too long. Maximum length: {max_length} characters"
            )

        # Decode HTML entities for TTS (request.text is already sanitized by Pydantic)
        tts_text = html.unescape(request.text)

        # Generate speech using current TTS provider
        audio_data = await tts_provider.synthesize_speech(
            text=tts_text,  # Use decoded text for TTS
            voice=request.voice,
            speed=request.speed
        )
        
        # Create response format
        audio_response = audio_processor.create_audio_response(audio_data, "response.wav")
        
        return TTSResponse(
            audio_data=audio_response["audio_data"],
            filename=audio_response["filename"],
            format=audio_response["format"],
            size_bytes=audio_response["size_bytes"],
            voice_used=request.voice or tts_provider.get_provider_info().get('default_voice', 'default')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis error: {str(e)}")

@router.post("/conversation", response_model=VoiceConversationResponse)
async def voice_conversation(
    audio_file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    voice: Optional[str] = Form(None),
    speed: Optional[float] = Form(1.0),
    language: str = Form("en")
):
    """
    Complete voice conversation workflow: STT → Chat → TTS

    Args:
        audio_file: Optional audio file for speech input
        text: Optional text input (if no audio file)
        voice: TTS voice to use
        speed: TTS speech speed
        language: STT language

    Returns:
        Complete conversation response with audio
    """
    temp_file_path = None
    try:
        # Input validation
        logger.info("Processing voice conversation request")

        # Validate parameters
        try:
            if language:
                language = validate_language_code(language)
            if voice:
                voice = validate_voice_name(voice)
            if speed:
                speed = validate_numeric_range(speed, 0.5, 2.0, "speed")
        except SecurityError as e:
            logger.warning(f"Parameter validation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

        transcribed_text = None

        # Handle input (either audio or text)
        if audio_file:
            # Validate audio file
            try:
                if audio_file.filename:
                    validate_filename(audio_file.filename)
                    validate_audio_format(audio_file.filename)

                # Check file size
                audio_data = await audio_file.read()
                if len(audio_data) > 25 * 1024 * 1024:  # 25MB limit
                    raise SecurityError("Audio file too large (max 25MB)")

                logger.info(f"Processing audio file: {audio_file.filename}, size: {len(audio_data)} bytes")

            except SecurityError as e:
                logger.warning(f"Audio file validation failed: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            # Process audio input
            current_provider = stt_provider.providers[stt_provider.current_provider]
            if not current_provider.validate_audio_file(audio_file.filename):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported audio format. Supported: {current_provider.supported_formats}"
                )

            # Save and transcribe audio
            temp_file_path = audio_processor.save_uploaded_audio(audio_data, audio_file.filename)

            transcribed_text = await stt_provider.transcribe_audio_file(
                audio_file_path=temp_file_path,
                language=language
            )
            user_input = transcribed_text

        elif text:
            # Validate and sanitize text input
            try:
                user_input = sanitize_text(text, MAX_TEXT_LENGTH)
                logger.info(f"Processing text input: length={len(user_input)}")
            except SecurityError as e:
                logger.warning(f"Text validation failed: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        else:
            raise HTTPException(status_code=400, detail="Either audio_file or text must be provided")
        
        # Generate AI response
        logger.info("Generating AI response")
        ai_response = await groq_chat.generate_response(
            message=user_input,
            temperature=0.7,
            max_tokens=500
        )

        # Sanitize AI response
        try:
            ai_response = sanitize_text(ai_response, MAX_TEXT_LENGTH)
        except SecurityError as e:
            logger.warning(f"AI response sanitization failed: {e}")
            ai_response = "Response contained invalid content and was filtered."

        # Decode HTML entities for TTS (but keep encoded version for response)
        tts_text = html.unescape(ai_response)

        # Convert response to speech using current TTS provider
        logger.info(f"Synthesizing speech: voice={voice}, speed={speed}")
        audio_data = await tts_provider.synthesize_speech(
            text=tts_text,  # Use decoded text for TTS
            voice=voice,
            speed=speed
        )

        # Create audio response
        audio_response = audio_processor.create_audio_response(audio_data, "conversation_response.wav")

        logger.info("Voice conversation completed successfully")
        return VoiceConversationResponse(
            transcribed_text=transcribed_text,
            ai_response=ai_response,
            audio_data=audio_response["audio_data"],
            filename=audio_response["filename"],
            voice_used=voice or tts_provider.get_provider_info().get('default_voice', 'default')
        )

    except HTTPException:
        raise
    except SecurityError as e:
        logger.warning(f"Security validation failed in voice conversation: {e}")
        raise HTTPException(status_code=400, detail=f"Security validation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in voice conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Voice conversation error: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_file_path:
            audio_processor.cleanup_temp_file(temp_file_path)

@router.get("/voices")
async def get_available_voices():
    """
    Get available TTS voices and recommendations
    
    Returns:
        Available voices organized by category
    """
    try:
        provider_info = tts_provider.get_provider_info()
        current_provider = tts_provider.get_current_provider()

        # Get voices and recommendations from current provider
        all_voices = tts_provider.get_available_voices("all")

        # Get voice recommendations if available
        recommendations = {}
        if hasattr(current_provider, 'get_voice_recommendations'):
            recommendations = current_provider.get_voice_recommendations()

        # Get voice categories if available
        voices_by_category = {}
        if hasattr(current_provider, 'voices'):
            voices_by_category = current_provider.voices

        return {
            "provider": provider_info.get("current_provider", "unknown"),
            "voices_by_category": voices_by_category,
            "all_voices": all_voices,
            "recommendations": recommendations,
            "default_voice": provider_info.get('default_voice', 'default')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting voices: {str(e)}")

@router.get("/models-info")
async def get_models_info():
    """
    Get information about available voice models
    
    Returns:
        Model information for STT and TTS
    """
    try:
        current_provider = stt_provider.providers[stt_provider.current_provider]
        return {
            "stt_model": current_provider.get_model_info(),
            "tts_model": tts_provider.get_provider_info(),
            "supported_audio_formats": current_provider.supported_formats,
            "max_file_size_mb": current_provider.max_file_size / (1024 * 1024)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting model info: {str(e)}")

@router.get("/health")
async def voice_health_check():
    """
    Health check for voice services
    
    Returns:
        Health status of STT and TTS services
    """
    try:
        # Test STT with a small audio file (would need actual implementation)
        stt_status = "available"  # Simplified for now
        
        # Test TTS with a short text
        try:
            test_audio = await tts_provider.synthesize_speech("Test", speed=1.0)
            tts_status = "available" if test_audio else "unavailable"
        except Exception:
            tts_status = "unavailable"
        
        return {
            "status": "healthy",
            "services": {
                "speech_to_text": stt_status,
                "text_to_speech": tts_status
            },
            "models": {
                "stt": "Groq Whisper STT",
                "tts": tts_provider.get_provider_info().get("current_provider", "unknown")
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "services": {
                "speech_to_text": "error",
                "text_to_speech": "error"
            }
        }
