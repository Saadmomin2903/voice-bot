/**
 * Audio Queue Manager for Sequential TTS Playback
 * Handles real-time audio streaming without conflicts
 */

class AudioQueueManager {
    constructor() {
        this.queue = [];
        this.isPlaying = false;
        this.currentAudio = null;
        this.currentResponseId = null;
        this.audioElements = new Map();
        
        // Debug mode
        this.debug = false;
        
        this.log('AudioQueueManager initialized');
    }
    
    log(message) {
        if (this.debug) {
            console.log(`[AudioQueue] ${message}`);
        }
    }
    
    /**
     * Add audio chunk to the queue for sequential playback
     */
    addChunk(audioData, text, responseId, chunkIndex = 0) {
        const chunk = {
            id: `${responseId}_${chunkIndex}`,
            audioData: audioData,
            text: text,
            responseId: responseId,
            chunkIndex: chunkIndex,
            played: false,
            timestamp: Date.now()
        };
        
        this.queue.push(chunk);
        this.log(`Added chunk ${chunk.id}: "${text.substring(0, 30)}..."`);
        
        // Start playing if not already playing
        if (!this.isPlaying) {
            this.playNext();
        }
        
        // Update UI
        this.updateAudioStatus();
        
        return chunk.id;
    }
    
    /**
     * Play the next audio chunk in the queue
     */
    async playNext() {
        if (this.queue.length === 0) {
            this.isPlaying = false;
            this.currentAudio = null;
            this.log('Queue empty, stopping playback');
            this.updateAudioStatus();
            return;
        }
        
        const chunk = this.queue.shift();
        this.isPlaying = true;
        this.currentAudio = chunk;
        
        this.log(`Playing chunk ${chunk.id}`);
        
        try {
            // Create audio element
            const audio = new Audio();
            audio.src = `data:audio/wav;base64,${chunk.audioData}`;
            audio.volume = 0.8;
            
            // Store audio element for potential cleanup
            this.audioElements.set(chunk.id, audio);
            
            // Update UI to show what's playing
            this.showCurrentlyPlaying(chunk);
            
            // Set up event handlers with proper cleanup
            audio.onended = () => {
                this.log(`Finished playing chunk ${chunk.id}`);
                chunk.played = true;

                // Clean up audio element
                this.cleanupAudioElement(chunk.id, audio);

                // Play next chunk
                setTimeout(() => {
                    this.playNext();
                }, 100); // Small delay between chunks
            };

            audio.onerror = (error) => {
                console.error(`Audio playback error for chunk ${chunk.id}:`, error);

                // Clean up audio element
                this.cleanupAudioElement(chunk.id, audio);

                // Continue with next chunk
                setTimeout(() => {
                    this.playNext();
                }, 100);
            };

            // Add timeout to prevent memory leaks from stuck audio
            setTimeout(() => {
                if (this.audioElements.has(chunk.id)) {
                    console.warn(`Audio chunk ${chunk.id} timed out, cleaning up`);
                    this.cleanupAudioElement(chunk.id, audio);
                    this.playNext();
                }
            }, 30000); // 30 second timeout
            
            // Start playback
            await audio.play();
            
        } catch (error) {
            console.error(`Failed to play audio chunk ${chunk.id}:`, error);
            
            // Continue with next chunk
            setTimeout(() => {
                this.playNext();
            }, 100);
        }
    }
    
    /**
     * Clean up a specific audio element
     */
    cleanupAudioElement(chunkId, audioElement) {
        try {
            // Pause and reset audio
            if (audioElement) {
                audioElement.pause();
                audioElement.currentTime = 0;
                audioElement.src = '';
                audioElement.load(); // Force cleanup
            }

            // Remove from tracking
            this.audioElements.delete(chunkId);

            this.log(`Cleaned up audio element for chunk ${chunkId}`);
        } catch (error) {
            console.error(`Error cleaning up audio element ${chunkId}:`, error);
        }
    }

    /**
     * Stop current playback and clear queue
     */
    stop() {
        this.log('Stopping audio playback');

        // Stop current audio
        if (this.currentAudio) {
            const audioElement = this.audioElements.get(this.currentAudio.id);
            if (audioElement) {
                this.cleanupAudioElement(this.currentAudio.id, audioElement);
            }
        }

        // Clean up all audio elements
        for (const [chunkId, audioElement] of this.audioElements.entries()) {
            this.cleanupAudioElement(chunkId, audioElement);
        }

        // Clear queue and reset state
        this.queue = [];
        this.isPlaying = false;
        this.currentAudio = null;
        this.audioElements.clear();

        this.updateAudioStatus();
    }
    
    /**
     * Get queue status for debugging
     */
    getStatus() {
        return {
            queueLength: this.queue.length,
            isPlaying: this.isPlaying,
            currentAudio: this.currentAudio ? this.currentAudio.id : null,
            totalElements: this.audioElements.size
        };
    }
    
    /**
     * Update audio status display
     */
    updateAudioStatus() {
        const statusElement = document.getElementById('audio-status');
        if (!statusElement) return;
        
        const status = this.getStatus();
        
        if (status.queueLength > 0 || status.isPlaying) {
            statusElement.style.display = 'block';
            statusElement.innerHTML = `
                <div class="audio-status-content">
                    <span class="status-indicator ${status.isPlaying ? 'playing' : 'queued'}">
                        ${status.isPlaying ? '🔊' : '⏸️'}
                    </span>
                    <span class="status-text">
                        ${status.isPlaying ? 'Playing' : 'Queued'}: ${status.queueLength} chunks
                    </span>
                    ${status.currentAudio ? `<span class="current-chunk">${status.currentAudio}</span>` : ''}
                </div>
            `;
        } else {
            statusElement.style.display = 'none';
        }
    }
    
    /**
     * Show currently playing audio chunk in the UI
     */
    showCurrentlyPlaying(chunk) {
        const responseElement = document.getElementById(`audio-controls-${chunk.responseId}`);
        if (responseElement) {
            responseElement.innerHTML = `
                <div class="currently-playing">
                    <span class="playing-icon">🔊</span>
                    <span class="playing-text">Playing: "${chunk.text.substring(0, 40)}${chunk.text.length > 40 ? '...' : ''}"</span>
                </div>
            `;
        }
    }
    
    /**
     * Enable debug mode
     */
    enableDebug() {
        this.debug = true;
        this.log('Debug mode enabled');
    }
    
    /**
     * Disable debug mode
     */
    disableDebug() {
        this.debug = false;
    }
}

// Global audio queue manager instance
window.audioQueueManager = new AudioQueueManager();

// Utility functions for voice recording
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

/**
 * Toggle voice recording
 */
async function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
}

/**
 * Check if microphone access is supported and available
 */
async function checkMicrophoneSupport() {
    // Check if we're in a secure context
    if (!window.isSecureContext && window.location.hostname !== 'localhost') {
        throw new Error('Microphone access requires HTTPS or localhost');
    }

    // Check if getUserMedia is supported
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Your browser does not support microphone access');
    }

    // Check permissions
    try {
        const permission = await navigator.permissions.query({ name: 'microphone' });
        if (permission.state === 'denied') {
            throw new Error('Microphone permission denied. Please enable microphone access in your browser settings.');
        }
    } catch (e) {
        // Permissions API might not be supported, continue anyway
        console.warn('Could not check microphone permissions:', e);
    }
}

/**
 * Start voice recording
 */
async function startRecording() {
    try {
        // Check microphone support first
        await checkMicrophoneSupport();

        console.log('Requesting microphone access...');
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });

        console.log('Microphone access granted');

        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });

            console.log('Audio recorded, length:', audioBlob.size);

            // Get voice settings
            const voiceSettings = {
                auto_tts: document.getElementById('auto-tts')?.checked || false,
                streaming_tts: document.getElementById('streaming-tts')?.checked || false,
                voice: document.getElementById('voice-select')?.value || 'en-US-GuyNeural'
            };

            console.log('Voice settings:', voiceSettings);

            // Send audio to backend for transcription
            await sendAudioForTranscription(audioBlob, voiceSettings);

            // Clean up
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        isRecording = true;

        // Update UI
        document.getElementById('record-btn').style.display = 'none';
        document.getElementById('stop-btn').style.display = 'inline-block';

        console.log('Recording started successfully');

    } catch (error) {
        console.error('Error starting recording:', error);

        let errorMessage = 'Error accessing microphone. ';

        if (error.name === 'NotAllowedError') {
            errorMessage += 'Please allow microphone access when prompted, or check your browser settings.';
        } else if (error.name === 'NotFoundError') {
            errorMessage += 'No microphone found. Please connect a microphone and try again.';
        } else if (error.name === 'NotSupportedError') {
            errorMessage += 'Your browser does not support audio recording.';
        } else if (error.name === 'SecurityError') {
            errorMessage += 'Microphone access blocked due to security restrictions. Try using HTTPS or localhost.';
        } else {
            errorMessage += error.message || 'Unknown error occurred.';
        }

        alert(errorMessage);
        addTranscriptionMessage(errorMessage, "error");
    }
}

/**
 * Stop voice recording
 */
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        
        // Update UI
        document.getElementById('record-btn').style.display = 'inline-block';
        document.getElementById('stop-btn').style.display = 'none';
    }
}

/**
 * Send audio to backend for transcription
 */
async function sendAudioForTranscription(audioBlob, voiceSettings) {
    try {
        // Show processing indicator
        addTranscriptionMessage("🎤 Processing voice...", "processing");

        // Create FormData for file upload
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'recording.wav');
        formData.append('language', 'en-US');

        console.log('Sending audio for transcription...');

        // Send to frontend proxy endpoint (which forwards to backend)
        const response = await fetch('/api/voice/transcribe', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            const transcribedText = result.transcribed_text;

            console.log('Transcription successful:', transcribedText);

            // Remove processing indicator
            removeTranscriptionMessage("processing");

            // Auto-submit the transcribed text if it's not empty
            // Note: We don't add a separate transcription message here to avoid duplication
            // The regular message flow will handle displaying the user message
            if (transcribedText && transcribedText.trim()) {
                await submitTranscribedMessage(transcribedText, voiceSettings);
            } else {
                // Only show transcription message if text is empty or invalid
                addTranscriptionMessage(transcribedText || "No speech detected", "error");
            }

        } else {
            console.error('Transcription failed:', response.status, response.statusText);
            const errorData = await response.json().catch(() => ({}));

            removeTranscriptionMessage("processing");
            addTranscriptionMessage(`❌ Transcription failed: ${errorData.detail || 'Unknown error'}`, "error");
        }

    } catch (error) {
        console.error('Error sending audio for transcription:', error);
        removeTranscriptionMessage("processing");
        addTranscriptionMessage(`❌ Error: ${error.message}`, "error");
    }
}

/**
 * Add transcription message to chat
 */
function addTranscriptionMessage(text, type) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message transcription-message ${type}`;
    messageDiv.id = `transcription-${type}`;

    let iconAndLabel = '';
    switch (type) {
        case 'processing':
            iconAndLabel = '🎤 Processing:';
            break;
        case 'transcribed':
            iconAndLabel = '🎤 You said:';
            break;
        case 'error':
            iconAndLabel = '❌ Error:';
            break;
    }

    messageDiv.innerHTML = `
        <div class="message-content">
            <strong>${iconAndLabel}</strong>
            <span class="message-text">${text}</span>
        </div>
        <div class="message-time">${new Date().toLocaleTimeString()}</div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Remove transcription message by type
 */
function removeTranscriptionMessage(type) {
    const messageElement = document.getElementById(`transcription-${type}`);
    if (messageElement) {
        messageElement.remove();
    }
}

/**
 * Submit transcribed message for AI response
 */
async function submitTranscribedMessage(transcribedText, voiceSettings) {
    try {
        console.log('Submitting transcribed message:', transcribedText);

        // Trigger the same flow as text input
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-btn');

        if (messageInput && sendButton) {
            // Clear any existing text first
            messageInput.value = '';

            // Set the transcribed text in the input field
            messageInput.value = transcribedText;

            // Trigger the send button click (this will create the user message)
            sendButton.click();

            // Clear the input after sending
            setTimeout(() => {
                messageInput.value = '';
            }, 100);
        }

    } catch (error) {
        console.error('Error submitting transcribed message:', error);
        // Show error message if submission fails
        addTranscriptionMessage(`Error: ${error.message}`, "error");
    }
}

/**
 * Convert blob to base64
 */
function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

/**
 * Test microphone availability on page load
 */
async function testMicrophoneAvailability() {
    try {
        await checkMicrophoneSupport();
        console.log('✅ Microphone support detected');

        // Update UI to show microphone is available
        const recordBtn = document.getElementById('record-btn');
        if (recordBtn) {
            recordBtn.title = 'Click to start voice recording';
        }
    } catch (error) {
        console.warn('⚠️ Microphone not available:', error.message);

        // Update UI to show microphone is not available
        const recordBtn = document.getElementById('record-btn');
        if (recordBtn) {
            recordBtn.title = `Microphone not available: ${error.message}`;
            recordBtn.style.opacity = '0.5';
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Audio Queue Manager loaded');

    // Test microphone availability
    testMicrophoneAvailability();

    // Enable debug mode if needed
    if (window.location.search.includes('debug=true')) {
        window.audioQueueManager.enableDebug();
    }

    // Handle Enter key in message input
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('send-btn').click();
                this.value = '';
            }
        });
    }
});
