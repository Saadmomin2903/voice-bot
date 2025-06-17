"""
Debug FastAPI middleware issue by inspecting the middleware stack
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Creating FastAPI app...")
app = FastAPI(title="Debug Middleware API")

print("🔍 Inspecting initial middleware state...")
print(f"app.middleware: {app.middleware}")
print(f"app.user_middleware: {app.user_middleware}")

print("🔍 Adding CORS middleware...")
try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    print("✅ CORS middleware added successfully")
except Exception as e:
    print(f"❌ Error adding CORS middleware: {e}")

print("🔍 Inspecting middleware state after CORS...")
print(f"app.middleware: {app.middleware}")
print(f"app.user_middleware: {app.user_middleware}")

# Try to inspect each middleware item
print("🔍 Inspecting individual middleware items...")
for i, middleware_item in enumerate(app.user_middleware):
    print(f"Middleware {i}: {middleware_item}")
    print(f"  Type: {type(middleware_item)}")
    print(f"  Length: {len(middleware_item) if hasattr(middleware_item, '__len__') else 'N/A'}")
    if hasattr(middleware_item, '__len__') and len(middleware_item) >= 1:
        for j, item in enumerate(middleware_item):
            print(f"    Item {j}: {item} (type: {type(item)})")

@app.get("/")
async def root():
    return {"message": "Debug API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Debug API is running"}

print("🔍 Attempting to build middleware stack manually...")
try:
    # This is what FastAPI does internally
    middleware = app.user_middleware.copy()
    print(f"Middleware to process: {middleware}")
    
    for i, middleware_item in enumerate(reversed(middleware)):
        print(f"Processing middleware {i}: {middleware_item}")
        try:
            cls, options = middleware_item
            print(f"  Successfully unpacked: cls={cls}, options={options}")
        except ValueError as e:
            print(f"  ❌ Failed to unpack: {e}")
            print(f"  Item has {len(middleware_item)} elements: {middleware_item}")
    
    print("✅ Manual middleware stack processing completed")
except Exception as e:
    print(f"❌ Manual middleware stack processing failed: {e}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting Debug API on http://{host}:{port}")
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()
