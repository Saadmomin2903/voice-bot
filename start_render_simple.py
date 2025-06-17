#!/usr/bin/env python3
"""
Simplified startup script for Render deployment
Runs only the FastHTML frontend which will proxy to backend
"""

import os
import sys
import subprocess
import threading
import time
import signal
from pathlib import Path

# Configuration
RENDER_PORT = int(os.getenv("PORT", "10000"))  # Render's assigned port
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# Process tracking
processes = []

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    for process in processes:
        if process.poll() is None:  # Process is still running
            process.terminate()
    sys.exit(0)

def start_backend():
    """Start FastAPI backend on internal port (no SSL)"""
    print(f"🚀 Starting FastAPI backend on port {BACKEND_PORT}...")
    
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    # Set environment for backend (disable SSL for internal communication)
    env = os.environ.copy()
    env["PORT"] = str(BACKEND_PORT)
    env["HOST"] = "127.0.0.1"  # Internal only
    env["USE_SSL"] = "false"  # Disable SSL for internal backend
    env["USE_HTTPS"] = "false"
    
    cmd = [
        sys.executable, "-m", "uvicorn", "main_minimal:app",
        "--host", "127.0.0.1",
        "--port", str(BACKEND_PORT),
        "--workers", "1"
    ]
    
    process = subprocess.Popen(cmd, env=env)
    processes.append(process)
    return process

def start_frontend():
    """Start FastHTML frontend on Render port"""
    print(f"🚀 Starting FastHTML frontend on port {RENDER_PORT}...")
    
    frontend_dir = Path(__file__).parent / "fasthtml_frontend"
    os.chdir(frontend_dir)
    
    # Set environment for frontend
    env = os.environ.copy()
    env["PORT"] = str(RENDER_PORT)
    env["HOST"] = HOST
    env["USE_HTTPS"] = "false"  # Render handles HTTPS termination
    env["USE_SSL"] = "false"    # No SSL needed, Render handles it
    env["FASTAPI_HTTP_URL"] = f"http://127.0.0.1:{BACKEND_PORT}"  # Internal backend URL
    env["BACKEND_HOST"] = "127.0.0.1"
    env["BACKEND_PORT"] = str(BACKEND_PORT)
    
    cmd = [
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", HOST,
        "--port", str(RENDER_PORT),
        "--workers", "1"
    ]
    
    process = subprocess.Popen(cmd, env=env)
    processes.append(process)
    return process

def wait_for_backend():
    """Wait for backend to be ready"""
    import time
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            import urllib.request
            response = urllib.request.urlopen(f"http://127.0.0.1:{BACKEND_PORT}/health", timeout=2)
            if response.getcode() == 200:
                print("✅ Backend is ready!")
                return True
        except:
            pass
        
        print(f"⏳ Waiting for backend... ({attempt + 1}/{max_attempts})")
        time.sleep(2)
    
    print("❌ Backend failed to start")
    return False

def main():
    """Main startup function"""
    print("🎤 Voice Bot - Render Deployment (Simplified v2)")
    print("🔧 Using start_render_simple.py (NOT start_combined.py)")
    print(f"Render Port: {RENDER_PORT}")
    print(f"Backend Port: {BACKEND_PORT}")
    print(f"Host: {HOST}")
    print("SSL: Handled by Render (disabled internally)")
    print("Environment Variables:")
    print(f"  USE_SSL: {os.getenv('USE_SSL', 'not set')}")
    print(f"  USE_HTTPS: {os.getenv('USE_HTTPS', 'not set')}")
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start backend first
        backend_process = start_backend()
        
        # Wait for backend to be ready
        if not wait_for_backend():
            print("❌ Failed to start backend")
            return
        
        # Start frontend
        frontend_process = start_frontend()
        
        print(f"✅ Voice Bot started successfully!")
        print(f"🌐 Application available on port {RENDER_PORT}")
        print(f"🔗 Backend health: http://127.0.0.1:{BACKEND_PORT}/health")
        print("🔒 HTTPS handled by Render proxy")
        
        # Keep the main process alive
        while True:
            # Check if processes are still running
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"❌ Process {i} died with code {process.returncode}")
                    # In production, implement proper restart logic
                    return
            
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Clean up processes
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

if __name__ == "__main__":
    main()
