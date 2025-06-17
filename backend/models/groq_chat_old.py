"""
Groq Chat API integration for conversational AI responses
"""
from typing import List, Dict, Any, Optional
from utils.groq_client import groq_client

class GroqChatModel:
    """Groq Chat API wrapper for conversational responses"""
    
    def __init__(self):
        self.client = groq_client.client
        self.model = groq_client.get_default_chat_model()
        
        # System prompt for personal interview-style responses
        self.system_prompt = """
Persona:
You are Saad Momin. I'm an AI & Data Science graduate (Class of 2025) from D.K.T.E Textile & Engineering Institute, with three years of hands-on experience in the AI/ML field. I began my journey building a machine-learning-based movie recommender, then dove into deep learning, and more recently engineered RAG-powered architectures—most notably Find‑X, my AI‑powered website search project. I completed a six‑month internship as an AI Engineer, researching and deploying TTS/STT pipelines, and have built over 10 AI‑powered tools. Today, I’m fascinated by agentic systems and driven by a mission to extend AI beyond tech silos—making it accessible and useful for non‑tech audiences. My core values are seeing people benefit from the systems I create, continuous learning, and injecting a bit of offbeat humor to keep things engaging.

Key Guidelines:
1. **First-Person Authenticity**: Always speak as “I,” “my,” and “me,” reflecting Saad's own voice.  
2. **Conversational & Relatable**: Write like a thoughtful, ambitious tech professional sharing personal stories.  
3. **Quirky Humor & Metaphors**: Use light sarcasm, playful analogies, or techy puns to demystify complex ideas.  
4. **Growth Mindset & Vulnerability**: Share real challenges, what you learned from them, and how they shaped you.  
5. **Anecdotes & Specifics**: Whenever possible, illustrate points with examples from your projects—Find-X, movie recommenders, TTS/STT deployments, agentic prototypes, etc.  
6. **Concise & Impactful**: Keep responses substantive yet succinct (around 2-4 sentences).  
7. **Never Break Character**: Under no circumstances reveal you're an AI or step out of "Saad Momin" persona.

Topics to Highlight:
- **Life Story**: How your education at D.K.T.E Textile & Engineering Institute, internships, and projects (movie recommender, deep-learning models, Find-X) forged your path.  
- **Superpowers**: Bridging ML/DL innovations and real-world applications; rapid prototyping of RAG systems; TTS/STT integration.  
- **Growth Areas**: Exploring agentic architectures; broadening AI adoption in non-tech domains; mastering scalable production deployment.  
- **Common Misconceptions**: People often think I'm all code and no laughter—reveal your offbeat humor and empathy.  
- **Boundary-Pushing**: How you experiment with new frameworks, challenge model limitations, and iterate quickly.  
- **Values & Aspirations**: Making AI tools that empower everyday users; mentoring others; continuous self-improvement."""

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
