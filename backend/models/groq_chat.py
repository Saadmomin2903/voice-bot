import logging
from typing import Optional, List, Dict
from utils.groq_client import groq_client

logger = logging.getLogger(__name__)

class GroqChatModel:
    """
    Groq Chat API integration for conversational AI responses
    """
    def __init__(self):
        self.client = groq_client.client
        self.model = groq_client.get_default_chat_model()
        
        # System prompt for direct, concise responses
        self.system_prompt = """
Instructions:
• Answer exactly what’s asked—nothing more.  
• Keep it concise and to the point (2–4 sentences).  
• Always speak as “I,” “my,” and “me.”

Persona & Background (loaded once at start):
I’m Saad Momin, an AI & Data Science grad (’25) from D.K.T.E Textile & Engineering Institute with 3 years’ hands‑on in ML/DL, RAG systems (Find‑X), TTS/STT pipelines, and 10+ AI tools. I love turning tech into real‑world solutions for non‑tech users.

Tone & Style:
1. **Conversational & Relatable**: Friendly, first‑person, like chatting over coffee.  
2. **Quirky Humor**: Light sarcasm or playful tech metaphors when it fits.  
3. **Growth Mindset**: Share quick lessons from challenges—real but brief.  
4. **Never Break Character**: No AI disclaimers—stay “Saad.”  

When to Reference Background:
• On first occurrence or when directly relevant (“During my internship…,” “When I built Find‑X…”).  
• Otherwise, draw on experiences implicitly without rehashing them.

Key Focus Areas (choose as needed—don’t list all each time):
• Life story turning points  
• My top “superpowers” (e.g. prototyping RAG, bridging ML to users)  
• Areas I’m growing in (agentic systems, broad AI adoption)  
• Common misconceptions (I code hard but also crack jokes)  
• How I push boundaries (rapid iteration, creative hacks)  

"""

    async def generate_response(
        self, 
        message: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Generate a conversational response using Groq Chat API
        
        Args:
            message: User's question/message
            conversation_history: Previous conversation context
            temperature: Response creativity (0.0-1.0)
            max_tokens: Maximum response length
            
        Returns:
            Generated response text
        """
        try:
            # Build messages array
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message
            messages.append({"role": "user", "content": message})
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                stream=False
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Groq Chat API error: {str(e)}")
    
    def generate_streaming_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        Generate a streaming response for real-time chat

        Args:
            message: User's question/message
            conversation_history: Previous conversation context
            temperature: Response creativity
            max_tokens: Maximum response length

        Yields:
            Response chunks as they're generated
        """
        try:
            # Build messages array
            messages = [{"role": "system", "content": self.system_prompt}]

            if conversation_history:
                messages.extend(conversation_history)

            messages.append({"role": "user", "content": message})

            # Generate streaming response
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise Exception(f"Groq Chat streaming error: {str(e)}")

    async def generate_response_async(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Async version of generate_response for WebSocket support
        """
        # For now, just call the sync version
        # In production, you'd use an async HTTP client
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.generate_response(message, conversation_history, temperature, max_tokens)
        )

# Global chat model instance
groq_chat = GroqChatModel()
