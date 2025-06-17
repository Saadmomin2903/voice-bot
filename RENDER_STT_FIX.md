# Fix for Groq STT Issue on Render

## Problem
The STT (Speech-to-Text) functionality is failing on Render with the error:
```
❌ Groq STT transcription failed: 'Groq' object has no attribute 'audio'
```

## Root Cause
This error occurs because the Groq Python library version in your `requirements.txt` (0.4.1) is outdated and doesn't have the `audio` attribute that contains the transcription functionality.

## Solution

### Step 1: Update Requirements
The `requirements.txt` has already been updated to use `groq>=0.28.0`. Make sure this change is deployed to Render.

### Step 2: Verify Environment Variable
1. Go to your Render dashboard
2. Navigate to your service
3. Go to Environment tab
4. Verify that `GROQ_API_KEY` is set and starts with `gsk_`

### Step 3: Redeploy
1. Push the updated `requirements.txt` to your GitHub repository
2. Render should automatically redeploy
3. Or manually trigger a redeploy from the Render dashboard

### Step 4: Test the Fix
1. Run the debug script to verify everything is working:
   ```bash
   python debug_groq.py
   ```

2. Or test the backend directly:
   ```bash
   cd backend
   python test_groq_stt.py
   ```

## Debugging Steps

If the issue persists, follow these debugging steps:

### 1. Check Logs
Look for these messages in your Render logs:
- `✅ Groq client initialized successfully` - Good
- `❌ Groq client not available` - Bad, check API key
- `✅ Groq Whisper STT configured` - Good
- `⚠️ Groq STT not configured` - Bad, check API key

### 2. Verify API Key Format
Your GROQ_API_KEY should:
- Start with `gsk_`
- Be at least 52 characters long
- Not contain placeholder text like "your_groq_api_key_here"

### 3. Check Library Version
The logs should show the Groq library version. It should be 0.28.0 or higher.

### 4. Test API Connection
The debug script will test a simple chat completion to verify the API key works.

## Fallback Behavior

The code has been updated to provide better error handling:

1. **Configuration Issues**: If the API key is missing or invalid, STT will return mock responses with helpful error messages
2. **Library Issues**: If the Groq library is incompatible, it will return mock responses instead of crashing
3. **API Errors**: If the API call fails, it will gracefully fall back to mock responses

## Expected Behavior After Fix

1. **Successful STT**: You should see logs like:
   ```
   ✅ Groq Whisper STT configured with model: whisper-large-v3-turbo
   Groq Whisper: Transcribing audio file: /tmp/tmpXXXXXX.wav
   Groq Whisper: Transcription successful: 'Hello world'
   ```

2. **Mock Responses**: If there are still issues, you'll see:
   ```
   🔄 Using mock transcription for: /tmp/tmpXXXXXX.wav
   ```

## Files Changed

1. `backend/requirements.txt` - Updated Groq library version
2. `backend/models/groq_stt.py` - Added better error handling and debugging
3. `backend/utils/groq_client.py` - Added more detailed logging
4. `debug_groq.py` - New diagnostic script
5. `backend/test_groq_stt.py` - New test script

## Quick Test Commands

Run these on your local machine to test before deploying:

```bash
# Test environment and API key
python debug_groq.py

# Test backend modules
cd backend
python test_groq_stt.py

# Test the actual API endpoint (if running locally)
curl -X POST "http://localhost:8000/api/voice/transcribe" \
  -F "audio_file=@test_audio.wav" \
  -F "language=en-US"
```

## Contact

If you continue to have issues after following these steps, check:
1. Render deployment logs for any errors during pip install
2. Environment variables are correctly set
3. The GitHub repository has the latest changes
4. Try a manual redeploy from Render dashboard

The STT functionality should work correctly after these fixes are deployed.
