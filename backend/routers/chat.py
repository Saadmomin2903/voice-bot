"""
Chat API endpoints for text-based conversations
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator, Field
from typing import List, Dict, Optional
from models.groq_chat import groq_chat
from utils.validation import (
    sanitize_text, validate_conversation_history, validate_numeric_range,
    handle_validation_error, SecurityError, MAX_MESSAGE_LENGTH
)
from utils.logging_config import get_logger
from utils.error_handler import ErrorCategory, ErrorSeverity
# Temporarily disable performance optimizer imports for deployment debugging
# from utils.performance_optimizer import async_timed, memory_efficient, performance_monitor, memory_manager
import json

logger = get_logger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH, description="Message content")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ['user', 'assistant', 'system']:
            raise ValueError(f"Invalid role: {v}. Must be 'user', 'assistant', or 'system'")
        return v

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        try:
            return sanitize_text(v, MAX_MESSAGE_LENGTH)
        except SecurityError as e:
            raise ValueError(str(e))

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH, description="User message")
    conversation_history: Optional[List[ChatMessage]] = Field(None, description="Previous conversation messages")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Response creativity (0.0-2.0)")
    max_tokens: Optional[int] = Field(500, ge=1, le=4000, description="Maximum response length")

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        try:
            return sanitize_text(v, MAX_MESSAGE_LENGTH)
        except SecurityError as e:
            raise ValueError(str(e))

    @field_validator('conversation_history')
    @classmethod
    def validate_history(cls, v):
        if v is None:
            return v
        try:
            # Convert to dict format for validation
            history_dicts = [{"role": msg.role, "content": msg.content} for msg in v]
            validated = validate_conversation_history(history_dicts)
            # Convert back to ChatMessage objects
            return [ChatMessage(role=msg["role"], content=msg["content"]) for msg in validated] if validated else None
        except SecurityError as e:
            raise ValueError(str(e))

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI generated response")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    timestamp: Optional[str] = Field(None, description="Response timestamp")

@router.post("/text", response_model=ChatResponse)
# Temporarily disable performance decorators for deployment debugging
# @async_timed(performance_monitor)
# @memory_efficient(memory_manager)
async def chat_text(request: ChatRequest):
    """
    Process text-based chat message using Groq Chat API with performance optimization

    Args:
        request: Chat request with message and optional history

    Returns:
        Generated response from the AI
    """
    try:
        # Input validation is handled by Pydantic models
        logger.info(f"Processing chat request: message_length={len(request.message)}")

        # Convert conversation history to dict format
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]
            logger.info(f"Using conversation history with {len(history)} messages")

        # Generate response using Groq Chat
        response = await groq_chat.generate_response(
            message=request.message,
            conversation_history=history,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        # Sanitize the response as well
        try:
            sanitized_response = sanitize_text(response, MAX_MESSAGE_LENGTH)
        except SecurityError as e:
            logger.warning(f"Response sanitization failed: {e}")
            sanitized_response = "Response contained invalid content and was filtered."

        return ChatResponse(
            response=sanitized_response,
            conversation_id=None,  # Could implement conversation tracking
            timestamp=None  # Could add timestamp
        )

    except ValueError as e:
        # Pydantic validation errors - let middleware handle with standardized response
        logger.warning(f"Validation error in chat request: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except SecurityError as e:
        # Custom security validation errors - let middleware handle
        logger.warning(f"Security validation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Security validation failed: {str(e)}")
    except Exception as e:
        # Unexpected errors - let middleware handle with standardized response
        logger.error(f"Unexpected error in chat processing: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Process text-based chat message with streaming response

    Args:
        request: Chat request with message and optional history

    Returns:
        Streaming response with real-time text generation
    """
    try:
        # Convert conversation history to dict format
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        # Generate streaming response
        def generate_stream():
            try:
                for chunk in groq_chat.generate_streaming_response(
                    message=request.message,
                    conversation_history=history,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                ):
                    # Send each chunk as Server-Sent Events format
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"

                # Send end signal
                yield f"data: {json.dumps({'done': True})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming chat error: {str(e)}")

@router.get("/sample-questions")
async def get_sample_questions():
    """
    Get sample interview-style questions for the voice bot
    
    Returns:
        List of sample questions users can ask
    """
    sample_questions = [
        "What should we know about your life story in a few sentences?",
        "What's your #1 superpower?",
        "What are the top 3 areas you'd like to grow in?",
        "What misconception do your coworkers have about you?",
        "How do you push your boundaries and limits?",
        "Tell me about a time you overcame a significant challenge.",
        "What motivates you to get up every morning?",
        "How do you handle stress and pressure?",
        "What's the most important lesson you've learned in your career?",
        "Where do you see yourself in 5 years?",
        "What's your biggest professional achievement?",
        "How do you approach learning new skills?",
        "What's your leadership style?",
        "How do you handle failure or setbacks?",
        "What makes you unique as a professional?"
    ]
    
    return {
        "sample_questions": sample_questions,
        "description": "These are example questions the voice bot is designed to answer in a conversational, interview-style format."
    }

@router.get("/model-info")
async def get_model_info():
    """
    Get information about the current chat model configuration
    
    Returns:
        Model configuration and capabilities
    """
    try:
        return {
            "model": groq_chat.model,
            "provider": "Groq",
            "capabilities": [
                "Conversational responses",
                "Interview-style questions",
                "Personality consistency",
                "Context awareness"
            ],
            "system_prompt_summary": "Configured for authentic, conversational responses to personal and professional questions",
            "default_temperature": 0.7,
            "default_max_tokens": 500
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting model info: {str(e)}")

class HealthResponse(BaseModel):
    status: str
    message: str
    model_available: bool

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for chat functionality
    
    Returns:
        Health status of chat service
    """
    try:
        # Test a simple chat request to verify model availability
        test_response = await groq_chat.generate_response(
            message="Hello, this is a test.",
            temperature=0.1,
            max_tokens=10
        )
        
        return HealthResponse(
            status="healthy",
            message="Chat service is operational",
            model_available=True
        )
        
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            message=f"Chat service error: {str(e)}",
            model_available=False
        )
