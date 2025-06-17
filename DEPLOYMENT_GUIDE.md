# 🚀 Voice Bot Deployment Guide

## Quick Start (Render - Recommended)

### Prerequisites
- GitHub account
- Groq API key from [groq.com](https://groq.com)
- Render account (free signup)

### Step 1: Prepare Repository

1. **Commit deployment files** (already created):
   ```bash
   git add render.yaml start_combined.py Dockerfile .env.production
   git commit -m "Add deployment configuration"
   git push origin main
   ```

### Step 2: Deploy to Render

1. **Connect Repository**:
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your voice bot repository

2. **Configure Service**:
   - **Name**: `voice-bot` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     cd backend && pip install -r requirements.txt && cd ../fasthtml_frontend && pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     python start_combined.py
     ```

3. **Set Environment Variables**:
   - `GROQ_API_KEY`: Your Groq API key
   - `USE_HTTPS`: `true`
   - `USE_SSL`: `true`
   - `ENVIRONMENT`: `production`
   - `FRONTEND_URL`: `https://your-app-name.onrender.com`

4. **Deploy**:
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)

### Step 3: Configure Domain & SSL

1. **Custom Domain** (Optional):
   - Go to Settings → Custom Domains
   - Add your domain
   - Update DNS records as instructed

2. **SSL Certificate**:
   - Automatic with Render
   - No additional configuration needed

### Step 4: Test Deployment

1. **Health Check**:
   ```bash
   curl https://your-app-name.onrender.com/health
   ```

2. **API Test**:
   ```bash
   curl -X POST https://your-app-name.onrender.com/api/chat/text \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello, test message"}'
   ```

3. **Frontend Test**:
   - Open `https://your-app-name.onrender.com`
   - Test microphone access (requires HTTPS)
   - Try voice recording and playback

## Alternative Deployments

### Railway Deployment

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Deploy**:
   ```bash
   railway new
   railway add
   railway up
   ```

3. **Set Environment Variables**:
   ```bash
   railway variables set GROQ_API_KEY=your_key
   railway variables set USE_HTTPS=true
   ```

### Fly.io Deployment

1. **Install Fly CLI**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

2. **Initialize App**:
   ```bash
   fly launch
   ```

3. **Set Secrets**:
   ```bash
   fly secrets set GROQ_API_KEY=your_key
   fly secrets set USE_HTTPS=true
   ```

4. **Deploy**:
   ```bash
   fly deploy
   ```

### Docker Deployment (Self-Hosted)

1. **Build Image**:
   ```bash
   docker build -t voice-bot .
   ```

2. **Run Container**:
   ```bash
   docker run -d \
     -p 10000:10000 \
     -e GROQ_API_KEY=your_key \
     -e USE_HTTPS=true \
     --name voice-bot \
     voice-bot
   ```

3. **With SSL Certificates**:
   ```bash
   docker run -d \
     -p 443:10000 \
     -v /path/to/ssl:/app/ssl_certs \
     -e GROQ_API_KEY=your_key \
     -e USE_HTTPS=true \
     --name voice-bot \
     voice-bot
   ```

## Production Optimizations

### Performance Tuning

1. **Update start_combined.py**:
   ```python
   # Add worker configuration
   WORKERS = int(os.getenv("WORKERS", "2"))
   
   # Add to uvicorn commands:
   "--workers", str(WORKERS)
   ```

2. **Memory Optimization**:
   ```python
   # In backend/main.py, add:
   import gc
   import psutil
   
   # Periodic cleanup
   @app.middleware("http")
   async def cleanup_middleware(request, call_next):
       response = await call_next(request)
       if psutil.virtual_memory().percent > 80:
           gc.collect()
       return response
   ```

### Security Hardening

1. **Rate Limiting**:
   ```python
   # Already implemented in backend
   # Ensure RATE_LIMIT_ENABLED=true in production
   ```

2. **CORS Configuration**:
   ```python
   # Update ALLOWED_ORIGINS in backend/main.py
   ALLOWED_ORIGINS = [
       "https://your-domain.com",
       "https://your-app-name.onrender.com"
   ]
   ```

### Monitoring & Logging

1. **Health Monitoring**:
   - Use Render's built-in monitoring
   - Set up alerts for downtime

2. **Log Aggregation**:
   ```python
   # Add to backend/main.py
   import logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

## Troubleshooting

### Common Issues

1. **"Service Unavailable"**:
   - Check environment variables
   - Verify GROQ_API_KEY is set
   - Check logs: `render logs` or platform equivalent

2. **WebSocket Connection Failed**:
   - Ensure platform supports WebSockets
   - Check CORS configuration
   - Verify HTTPS is enabled

3. **Microphone Access Denied**:
   - Ensure HTTPS is enabled
   - Check browser permissions
   - Verify SSL certificate is valid

4. **High Memory Usage**:
   - Enable memory management
   - Reduce audio cache size
   - Monitor with `/performance` endpoint

### Debug Commands

```bash
# Check service status
curl https://your-app.onrender.com/health

# Check API key configuration
curl https://your-app.onrender.com/security/api-keys

# Check performance metrics
curl https://your-app.onrender.com/performance

# Test voice endpoints
curl https://your-app.onrender.com/api/voice/voices
```

## Cost Optimization

### Free Tier Limits
- **Render**: 750 hours/month free
- **Railway**: $5 credit/month
- **Fly.io**: 3 free VMs
- **Google Cloud Run**: 2M requests/month

### Scaling Strategy
1. Start with free tier for testing
2. Upgrade to paid tier ($7/month) for production
3. Monitor usage and scale as needed
4. Consider CDN for static assets

## Next Steps

1. **Custom Domain**: Set up your own domain
2. **Analytics**: Add usage tracking
3. **Backup**: Set up database backups (if using)
4. **CI/CD**: Automate deployments
5. **Monitoring**: Set up uptime monitoring

---

**🎉 Your voice bot is now deployed and ready for production use!**
