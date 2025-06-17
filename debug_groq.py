#!/usr/bin/env python3
"""
Debug script for Groq STT issues on Render
Run this script to diagnose Groq client and STT problems
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment variables and basic setup"""
    logger.info("🔍 Checking environment...")
    
    # Check Python version
    logger.info(f"Python version: {sys.version}")
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    logger.info(f"Current directory: {current_dir}")
    
    # Check for backend directory
    backend_dir = current_dir / "backend"
    if backend_dir.exists():
        logger.info("✅ Backend directory found")
        sys.path.insert(0, str(backend_dir))
    else:
        logger.warning("⚠️ Backend directory not found, trying current directory")
        sys.path.insert(0, str(current_dir))
    
    # Check environment variables
    groq_key = os.getenv('GROQ_API_KEY')
    if groq_key:
        # Mask the key for security
        masked_key = f"{groq_key[:4]}...{groq_key[-4:]}" if len(groq_key) > 8 else "***SHORT***"
        logger.info(f"✅ GROQ_API_KEY found: {masked_key}")
        logger.info(f"Key length: {len(groq_key)} characters")
        
        # Check key format
        if groq_key.startswith('gsk_'):
            logger.info("✅ Key has correct 'gsk_' prefix")
        else:
            logger.warning("⚠️ Key does not start with 'gsk_' - may be invalid")
    else:
        logger.error("❌ GROQ_API_KEY not found in environment")
    
    return groq_key is not None

def check_groq_library():
    """Check Groq library installation and version"""
    logger.info("📚 Checking Groq library...")
    
    try:
        import groq
        logger.info(f"✅ Groq library imported successfully")
        
        # Check version if available
        if hasattr(groq, '__version__'):
            logger.info(f"Groq library version: {groq.__version__}")
        else:
            logger.info("Groq library version not available")
        
        # Try to create a client
        try:
            client = groq.Groq()
            logger.info("✅ Groq client created successfully")
            
            # Check client attributes
            if hasattr(client, 'audio'):
                logger.info("✅ Client has 'audio' attribute")
                if hasattr(client.audio, 'transcriptions'):
                    logger.info("✅ Client has 'audio.transcriptions' attribute")
                    if hasattr(client.audio.transcriptions, 'create'):
                        logger.info("✅ Client has 'audio.transcriptions.create' method")
                        return True
                    else:
                        logger.error("❌ Client missing 'audio.transcriptions.create' method")
                else:
                    logger.error("❌ Client missing 'audio.transcriptions' attribute")
            else:
                logger.error("❌ Client missing 'audio' attribute")
                
        except Exception as e:
            logger.error(f"❌ Failed to create Groq client: {e}")
            
    except ImportError as e:
        logger.error(f"❌ Failed to import Groq library: {e}")
        return False
    
    return False

def check_backend_modules():
    """Check backend modules"""
    logger.info("🔧 Checking backend modules...")
    
    try:
        # Check API key manager
        from utils.api_key_manager import api_key_manager
        logger.info("✅ API key manager imported")
        
        # Check security status
        security_status = api_key_manager.check_system_security()
        logger.info(f"Security level: {security_status['security_level']}")
        
        # Check Groq client
        from utils.groq_client import groq_client
        logger.info("✅ Groq client module imported")
        
        if groq_client:
            logger.info(f"Groq client configured: {groq_client.is_configured}")
            if groq_client.client:
                logger.info("✅ Groq client instance exists")
            else:
                logger.error("❌ Groq client instance is None")
        else:
            logger.error("❌ Groq client is None")
        
        # Check STT model
        from models.groq_stt import groq_stt
        logger.info("✅ Groq STT model imported")
        logger.info(f"STT configured: {groq_stt.is_configured}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking backend modules: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_simple_groq_call():
    """Test a simple Groq API call"""
    logger.info("🧪 Testing simple Groq API call...")
    
    groq_key = os.getenv('GROQ_API_KEY')
    if not groq_key:
        logger.error("❌ No GROQ_API_KEY available for testing")
        return False
    
    try:
        import groq
        
        # Create client with explicit API key
        client = groq.Groq(api_key=groq_key)
        logger.info("✅ Created Groq client with API key")
        
        # Test chat completion (simpler than STT)
        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": "Hello"}],
                model="llama3-8b-8192",
                max_tokens=10
            )
            logger.info("✅ Chat completion successful")
            logger.info(f"Response: {response.choices[0].message.content}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Chat completion failed: {e}")
            
    except Exception as e:
        logger.error(f"❌ Error in simple Groq test: {e}")
        
    return False

def main():
    """Run all diagnostic checks"""
    logger.info("🚀 Starting Groq STT diagnostics...")
    
    # Check environment
    logger.info("\n" + "="*60)
    logger.info("ENVIRONMENT CHECK")
    logger.info("="*60)
    env_ok = check_environment()
    
    # Check Groq library
    logger.info("\n" + "="*60)
    logger.info("GROQ LIBRARY CHECK")
    logger.info("="*60)
    lib_ok = check_groq_library()
    
    # Test simple API call
    logger.info("\n" + "="*60)
    logger.info("SIMPLE API TEST")
    logger.info("="*60)
    api_ok = test_simple_groq_call()
    
    # Check backend modules
    logger.info("\n" + "="*60)
    logger.info("BACKEND MODULES CHECK")
    logger.info("="*60)
    backend_ok = check_backend_modules()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info("="*60)
    logger.info(f"Environment: {'✅ OK' if env_ok else '❌ FAILED'}")
    logger.info(f"Groq Library: {'✅ OK' if lib_ok else '❌ FAILED'}")
    logger.info(f"Simple API Test: {'✅ OK' if api_ok else '❌ FAILED'}")
    logger.info(f"Backend Modules: {'✅ OK' if backend_ok else '❌ FAILED'}")
    
    if all([env_ok, lib_ok, api_ok, backend_ok]):
        logger.info("🎉 All diagnostics passed!")
        logger.info("💡 STT should work. If it doesn't, check audio file format and size.")
    else:
        logger.error("💥 Some diagnostics failed!")
        logger.info("💡 Fix the failed items above to resolve STT issues.")
    
    return 0 if all([env_ok, lib_ok, api_ok, backend_ok]) else 1

if __name__ == "__main__":
    sys.exit(main())
