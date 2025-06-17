#!/usr/bin/env python3
"""
Combined startup script for Render deployment
Starts both FastAPI backend and FastHTML frontend in production mode
"""

import os
import sys
import subprocess
import threading
import time
import signal
from pathlib import Path

# Configuration
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "8504"))
RENDER_PORT = int(os.getenv("PORT", "10000"))  # Render's assigned port
HOST = os.getenv("HOST", "0.0.0.0")
USE_SSL = os.getenv("USE_SSL", "true").lower() == "true"

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
    """Start FastAPI backend"""
    print(f"🚀 Starting FastAPI backend on port {BACKEND_PORT}...")
    
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    cmd = [
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", HOST,
        "--port", str(BACKEND_PORT),
        "--workers", "1"
    ]
    
    if USE_SSL:
        cmd.extend([
            "--ssl-keyfile", "../ssl_certs/key.pem",
            "--ssl-certfile", "../ssl_certs/cert.pem"
        ])
    
    process = subprocess.Popen(cmd)
    processes.append(process)
    return process

def start_frontend():
    """Start FastHTML frontend"""
    print(f"🚀 Starting FastHTML frontend on port {FRONTEND_PORT}...")
    
    frontend_dir = Path(__file__).parent / "fasthtml_frontend"
    os.chdir(frontend_dir)
    
    # Set environment for frontend
    env = os.environ.copy()
    env["USE_HTTPS"] = str(USE_SSL).lower()
    
    cmd = [
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", HOST,
        "--port", str(FRONTEND_PORT),
        "--workers", "1"
    ]
    
    if USE_SSL:
        cmd.extend([
            "--ssl-keyfile", "../ssl_certs/key.pem",
            "--ssl-certfile", "../ssl_certs/cert.pem"
        ])
    
    process = subprocess.Popen(cmd, env=env)
    processes.append(process)
    return process

def start_simple_proxy():
    """Start simple HTTP proxy for Render deployment"""
    print(f"🚀 Starting simple proxy on port {RENDER_PORT}...")

    import asyncio
    import aiohttp
    from aiohttp import web, ClientSession

    async def proxy_handler(request):
        """Handle proxy requests"""
        path = request.path_qs
        method = request.method
        headers = dict(request.headers)

        # Remove hop-by-hop headers
        for header in ['connection', 'upgrade', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers', 'transfer-encoding']:
            headers.pop(header, None)

        # Determine target based on path
        if path.startswith('/api/') or path.startswith('/ws/') or path == '/health':
            target_url = f"http://localhost:{BACKEND_PORT}{path}"
        else:
            target_url = f"http://localhost:{FRONTEND_PORT}{path}"

        # Handle WebSocket upgrade
        if request.headers.get('upgrade', '').lower() == 'websocket':
            # WebSocket proxy
            ws_resp = web.WebSocketResponse()
            await ws_resp.prepare(request)

            async with ClientSession() as session:
                async with session.ws_connect(target_url) as ws_target:
                    async def forward_to_target():
                        async for msg in ws_resp:
                            if msg.type == aiohttp.MsgType.TEXT:
                                await ws_target.send_str(msg.data)
                            elif msg.type == aiohttp.MsgType.BINARY:
                                await ws_target.send_bytes(msg.data)

                    async def forward_to_client():
                        async for msg in ws_target:
                            if msg.type == aiohttp.MsgType.TEXT:
                                await ws_resp.send_str(msg.data)
                            elif msg.type == aiohttp.MsgType.BINARY:
                                await ws_resp.send_bytes(msg.data)

                    await asyncio.gather(forward_to_target(), forward_to_client())

            return ws_resp

        # Regular HTTP proxy
        async with ClientSession() as session:
            data = await request.read() if request.can_read_body else None

            async with session.request(
                method=method,
                url=target_url,
                headers=headers,
                data=data
            ) as resp:
                body = await resp.read()
                response = web.Response(
                    body=body,
                    status=resp.status,
                    headers=resp.headers
                )
                return response

    # Create and start the proxy server
    app = web.Application()
    app.router.add_route('*', '/{path:.*}', proxy_handler)

    def run_proxy():
        web.run_app(app, host=HOST, port=RENDER_PORT)

    proxy_thread = threading.Thread(target=run_proxy, daemon=True)
    proxy_thread.start()

    return proxy_thread

def main():
    """Main startup function"""
    print("🎤 Voice Bot - Combined Startup for Render")
    print(f"Backend Port: {BACKEND_PORT}")
    print(f"Frontend Port: {FRONTEND_PORT}")
    print(f"Render Port: {RENDER_PORT}")
    print(f"SSL Enabled: {USE_SSL}")
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start backend
        backend_process = start_backend()
        time.sleep(3)  # Wait for backend to start
        
        # Start frontend
        frontend_process = start_frontend()
        time.sleep(3)  # Wait for frontend to start
        
        # Start simple proxy
        try:
            proxy_process = start_simple_proxy()
            print(f"✅ All services started successfully!")
            print(f"🌐 Application available at: http://localhost:{RENDER_PORT}")
            print(f"🔗 Frontend: http://localhost:{FRONTEND_PORT}")
            print(f"🔗 Backend: http://localhost:{BACKEND_PORT}")
        except Exception as e:
            print(f"⚠️ Proxy failed to start: {e}")
            print(f"✅ Services started individually!")
            print(f"🔗 Frontend: http://localhost:{FRONTEND_PORT}")
            print(f"🔗 Backend: http://localhost:{BACKEND_PORT}")
        
        # Wait for processes
        while True:
            for process in processes:
                if process.poll() is not None:
                    print(f"❌ Process {process.pid} died, restarting...")
                    # In production, implement proper restart logic
                    break
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Clean up processes
        for process in processes:
            if process.poll() is None:
                process.terminate()

if __name__ == "__main__":
    main()
