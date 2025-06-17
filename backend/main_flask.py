"""
Flask-based backend as fallback option
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Enable CORS
CORS(app, origins="*")

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
        "framework": "flask"
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
