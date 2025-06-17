# 🎤 Voice Bot - AI-Powered Voice Assistant

A modern voice-enabled chatbot built with FastAPI and FastHTML, featuring real-time speech-to-text, AI conversation, and text-to-speech capabilities.

## ✨ Features

- **🎙️ Speech-to-Text**: Convert voice input to text using Groq Whisper STT
- **🤖 AI Conversation**: Intelligent responses powered by Groq's LLaMA models
- **🔊 Text-to-Speech**: Natural voice synthesis with Microsoft Edge TTS
- **⚡ Real-time Processing**: Fast response times with optimized inference
- **🌐 Web Interface**: Clean, responsive FastHTML frontend
- **🔄 Conversation Memory**: Maintains context across interactions
- **📱 Mobile Friendly**: Works on desktop and mobile devices
- **🎛️ Multiple Voices**: Male and female voice options

## 🛠️ Technology Stack

- **Frontend**: FastHTML (Modern web framework)
- **Backend**: FastAPI (REST API)
- **AI Services**:
  - **STT**: Groq Whisper (`whisper-large-v3-turbo`)
  - **Chat**: Groq LLaMA (`llama3-8b-8192`)
  - **TTS**: Microsoft Edge TTS (Multiple voices)
- **Audio Processing**: Built-in audio utilities

## 📋 Prerequisites

- Python 3.8+
- Groq API key from [https://groq.com](https://groq.com)
- Modern web browser with microphone access

## 🔧 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd voice-bot
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env and add your Groq API key:
# GROQ_API_KEY=your_groq_api_key_here
```

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd ../fasthtml_frontend
pip install -r requirements.txt
```

## 🚀 Running the Application

### Start the Backend (Terminal 1)

```bash
cd backend
python main.py
```

The API will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

### Start the Frontend (Terminal 2)

```bash
cd fasthtml_frontend
python main.py
```

The web app will be available at: http://localhost:8504

## 📖 API Documentation

### Chat Endpoints

- `POST /api/chat/text` - Process text-based questions
- `GET /api/chat/sample-questions` - Get sample interview questions
- `GET /api/chat/model-info` - Get chat model information
- `GET /api/chat/health` - Chat service health check

### Voice Endpoints

- `POST /api/voice/transcribe` - Convert speech to text
- `POST /api/voice/synthesize` - Convert text to speech
- `POST /api/voice/conversation` - Complete voice workflow
- `GET /api/voice/voices` - Get available TTS voices
- `GET /api/voice/models-info` - Get voice model information
- `GET /api/voice/health` - Voice service health check

### General Endpoints

- `GET /` - API information
- `GET /health` - Overall health check
- `GET /config` - API configuration

## 🎯 Usage Examples

### Sample Interview Questions

The bot is designed to answer questions like:

- "What should we know about your life story in a few sentences?"
- "What's your #1 superpower?"
- "What are the top 3 areas you'd like to grow in?"
- "What misconception do your coworkers have about you?"
- "How do you push your boundaries and limits?"

### Voice Interaction

1. Click the microphone button or upload an audio file
2. Ask your question naturally
3. The bot will transcribe, generate a response, and speak it back

### Text Interaction

1. Type your question in the text area
2. Click "Send Message"
3. Get an immediate text response

## 🔊 Available Voices

### Voice Categories

- **Professional**: Fritz-PlayAI, Quinn-PlayAI
- **Friendly**: Celeste-PlayAI, Deedee-PlayAI
- **Authoritative**: Atlas-PlayAI, Thunder-PlayAI
- **Conversational**: Chip-PlayAI (default), Gail-PlayAI

## ⚙️ Configuration

### Environment Variables

```bash
# Required
GROQ_API_KEY=your_groq_api_key

# Optional
HOST=0.0.0.0
PORT=8000
DEBUG=false
BACKEND_URL=http://localhost:8000
```

### Model Configuration

- **Chat Model**: llama3-8b-8192 (default) or mixtral-8x7b-32768
- **STT Model**: whisper-large-v3-turbo (fastest, 216x real-time)
- **TTS Model**: playai-tts with Chip-PlayAI voice (default)

## 🚀 Deployment

### Streamlit Cloud + Railway/Render

1. **Frontend**: Deploy to Streamlit Cloud
2. **Backend**: Deploy to Railway or Render
3. Update `BACKEND_URL` in frontend environment

### Heroku (All-in-one)

```bash
# Add Procfile for both services
echo "web: cd backend && python main.py" > Procfile
```

### Environment Variables for Production

```bash
GROQ_API_KEY=your_production_groq_key
HOST=0.0.0.0
PORT=$PORT  # Heroku sets this automatically
DEBUG=false
```

## 🧪 Testing

### Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Test chat
curl -X POST http://localhost:8000/api/chat/text \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your superpower?"}'

# Get available voices
curl http://localhost:8000/api/voice/voices
```

### Test Frontend

1. Open http://localhost:8501
2. Try sample questions
3. Test voice upload functionality
4. Verify audio playback

## 📊 Performance

### Speed Benchmarks

- **STT**: 216x real-time (whisper-large-v3-turbo)
- **Chat**: Ultra-fast inference with Groq
- **TTS**: Near real-time synthesis
- **Total Pipeline**: <3 seconds for typical interactions

### Cost Optimization

- STT: $0.04 per hour (turbo model)
- TTS: $50 per 1M characters
- Chat: Groq's competitive pricing

## 🔒 Security & Privacy

- API keys stored in environment variables
- No permanent storage of voice recordings
- Temporary audio files cleaned up automatically
- CORS configured for production
- HTTPS required for microphone access in production

## 🐛 Troubleshooting

### Common Issues

1. **"GROQ_API_KEY not configured"**

   - Ensure `.env` file exists with valid API key
   - Check environment variable is loaded

2. **"Backend not available"**

   - Verify backend is running on correct port
   - Check `BACKEND_URL` in frontend configuration

3. **Audio upload issues**

   - Ensure file format is supported (wav, mp3, ogg, webm, m4a, flac)
   - Check file size is under 25MB

4. **Voice not working**
   - Verify microphone permissions in browser
   - Use HTTPS in production for microphone access

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
python backend/main.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Groq](https://groq.com) for ultra-fast AI inference
- [Streamlit](https://streamlit.io) for the web framework
- [FastAPI](https://fastapi.tiangolo.com) for the backend framework

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Open an issue on GitHub

---

**Built with ❤️ using Groq APIs, Streamlit, and FastAPI**
