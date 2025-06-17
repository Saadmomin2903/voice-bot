#!/usr/bin/env python3
"""
Test script to run the new UI locally
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fasthtml
        import uvicorn
        print("✅ FastHTML and Uvicorn are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Install with: pip install fasthtml uvicorn")
        return False

def start_backend():
    """Start the backend server"""
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return None
    
    print("🚀 Starting backend server...")
    try:
        backend_process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)  # Give backend time to start
        
        if backend_process.poll() is None:
            print("✅ Backend server started")
            return backend_process
        else:
            print("❌ Backend server failed to start")
            return None
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return None

def start_frontend():
    """Start the frontend server"""
    frontend_dir = Path("fasthtml_frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return None
    
    print("🚀 Starting frontend server...")
    try:
        frontend_process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2)  # Give frontend time to start
        
        if frontend_process.poll() is None:
            print("✅ Frontend server started")
            return frontend_process
        else:
            print("❌ Frontend server failed to start")
            return None
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return None

def main():
    """Main function to test the UI"""
    print("🧪 Testing New Voice Bot UI")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print("💥 Cannot start without backend")
        return 1
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print("💥 Cannot start frontend")
        if backend_process:
            backend_process.terminate()
        return 1
    
    # Open browser
    print("\n🌐 Opening browser...")
    time.sleep(1)
    webbrowser.open("http://localhost:8504")
    
    print("\n" + "=" * 40)
    print("🎉 Voice Bot UI is running!")
    print("📱 Frontend: http://localhost:8504")
    print("🔧 Backend: http://localhost:8000")
    print("=" * 40)
    print("\n💡 Features to test:")
    print("  • Modern dark theme with gradients")
    print("  • Responsive design (try resizing window)")
    print("  • Voice recording with visual feedback")
    print("  • Chat interface with message bubbles")
    print("  • Voice settings panel")
    print("  • Audio playback controls")
    print("\n⌨️  Press Ctrl+C to stop servers")
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process stopped")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend process stopped")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        
    finally:
        # Clean up processes
        if backend_process and backend_process.poll() is None:
            backend_process.terminate()
            print("✅ Backend stopped")
            
        if frontend_process and frontend_process.poll() is None:
            frontend_process.terminate()
            print("✅ Frontend stopped")
    
    print("👋 UI test completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
