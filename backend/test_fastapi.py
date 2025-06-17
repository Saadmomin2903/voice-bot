"""
Test FastAPI setup to debug middleware issues
"""
import sys
import os

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    import fastapi
    print(f"FastAPI version: {fastapi.__version__}")
except ImportError as e:
    print(f"FastAPI import error: {e}")

try:
    import uvicorn
    print(f"Uvicorn version: {uvicorn.__version__}")
except ImportError as e:
    print(f"Uvicorn import error: {e}")

try:
    import starlette
    print(f"Starlette version: {starlette.__version__}")
except ImportError as e:
    print(f"Starlette import error: {e}")

try:
    from fastapi import FastAPI
    print("Creating basic FastAPI app...")
    app = FastAPI()
    print("✅ FastAPI app created successfully")
    
    @app.get("/")
    def root():
        return {"message": "test"}
    
    print("✅ Route added successfully")
    
    # Try to access the middleware stack
    print("Checking middleware stack...")
    print(f"App middleware: {app.middleware}")
    print(f"App user middleware: {app.user_middleware}")
    
    # Try to build middleware stack manually
    print("Attempting to build middleware stack...")
    try:
        middleware_stack = app.build_middleware_stack()
        print("✅ Middleware stack built successfully")
    except Exception as e:
        print(f"❌ Middleware stack build failed: {e}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"❌ FastAPI setup failed: {e}")
    import traceback
    traceback.print_exc()

print("Test completed.")
