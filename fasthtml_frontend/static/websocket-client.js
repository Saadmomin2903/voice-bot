/**
 * HTTP-based Communication Client for Voice Bot
 * Handles backend connectivity and status updates
 */

class VoiceBotClient {
    constructor() {
        this.isConnected = false;
        this.lastHealthCheck = null;
        this.healthCheckInterval = null;
        this.backendUrl = 'http://localhost:8000';

        // Note: Health checks removed to prevent 404 errors
        // Backend connectivity will be checked when actually needed
    }

    /**
     * Check backend connectivity when needed
     */
    async checkBackendHealth() {
        try {
            const response = await fetch(`${this.backendUrl}/health`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const data = await response.json();
                this.isConnected = data.status === 'healthy';
                this.lastHealthCheck = new Date().toISOString();
                return data;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Backend health check failed:', error);
            this.isConnected = false;
            return null;
        }
    }
    
    /**
     * Send HTTP request to backend
     */
    async sendRequest(endpoint, method = 'GET', data = null) {
        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
            };

            if (data && method !== 'GET') {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(endpoint, options);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Request to ${endpoint} failed:`, error);
            throw error;
        }
    }

    /**
     * Get backend configuration
     */
    async getBackendConfig() {
        try {
            return await this.sendRequest(`${this.backendUrl}/config`);
        } catch (error) {
            console.error('Failed to get backend config:', error);
            return null;
        }
    }

    /**
     * Get available voices
     */
    async getAvailableVoices() {
        try {
            return await this.sendRequest(`${this.backendUrl}/api/voice/voices`);
        } catch (error) {
            console.error('Failed to get available voices:', error);
            return null;
        }
    }
    




    /**
     * Cleanup when page unloads
     */
    cleanup() {
        // No periodic health checks to stop
        console.log('VoiceBotClient cleanup completed');
    }
}

// Initialize HTTP client when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing HTTP-based communication...');

    // Initialize HTTP client
    window.voiceBotClient = new VoiceBotClient();

    // Make it globally accessible for other scripts
    window.voiceBotHTTP = window.voiceBotClient;

    // Connection check button functionality (if needed)
    const checkConnectionBtn = document.getElementById('check-connection-btn');
    if (checkConnectionBtn) {
        checkConnectionBtn.addEventListener('click', async function() {
            await window.voiceBotClient.checkBackendHealth();
        });
    }

    console.log('Voice Bot HTTP client initialized');
});



// Handle page unload
window.addEventListener('beforeunload', function() {
    if (window.voiceBotClient) {
        window.voiceBotClient.cleanup();
    }
});
