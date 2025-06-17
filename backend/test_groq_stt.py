#!/usr/bin/env python3
"""
Test script to verify Groq STT functionality
"""

import os
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_groq_client():
    """Test Groq client initialization"""
    try:
        from utils.groq_client import groq_client
        
        logger.info("Testing Groq client initialization...")
        
        if groq_client is None:
            logger.error("❌ Groq client is None")
            return False
        
        logger.info(f"Groq client configured: {groq_client.is_configured}")
        logger.info(f"Groq client instance: {groq_client.client}")
        
        if groq_client.is_configured:
            logger.info("✅ Groq client is properly configured")
            
            # Test client attributes
            if hasattr(groq_client.client, 'audio'):
                logger.info("✅ Groq client has 'audio' attribute")
                if hasattr(groq_client.client.audio, 'transcriptions'):
                    logger.info("✅ Groq client has 'audio.transcriptions' attribute")
                    if hasattr(groq_client.client.audio.transcriptions, 'create'):
                        logger.info("✅ Groq client has 'audio.transcriptions.create' method")
                        return True
                    else:
                        logger.error("❌ Groq client missing 'audio.transcriptions.create' method")
                else:
                    logger.error("❌ Groq client missing 'audio.transcriptions' attribute")
            else:
                logger.error("❌ Groq client missing 'audio' attribute")
        else:
            logger.error("❌ Groq client is not configured")
            
        return False
        
    except Exception as e:
        logger.error(f"❌ Error testing Groq client: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_groq_stt():
    """Test Groq STT model initialization"""
    try:
        from models.groq_stt import groq_stt
        
        logger.info("Testing Groq STT model...")
        
        logger.info(f"STT configured: {groq_stt.is_configured}")
        logger.info(f"STT client: {groq_stt.client}")
        logger.info(f"STT model: {groq_stt.model}")
        
        if groq_stt.is_configured:
            logger.info("✅ Groq STT is properly configured")
            return True
        else:
            logger.error("❌ Groq STT is not configured")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing Groq STT: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_api_key_manager():
    """Test API key manager"""
    try:
        from utils.api_key_manager import api_key_manager
        
        logger.info("Testing API key manager...")
        
        # Check security status
        security_status = api_key_manager.check_system_security()
        logger.info(f"Security level: {security_status['security_level']}")
        
        # Check required keys
        required_keys = security_status['required_keys']
        logger.info(f"Required keys - Total: {required_keys['total']}, Valid: {required_keys['valid']}")
        
        for key_name, details in required_keys['details'].items():
            logger.info(f"  {key_name}: {details['status']} ({details['masked_key']})")
        
        # Check GROQ_API_KEY specifically
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key:
            logger.info(f"GROQ_API_KEY found: {api_key_manager.mask_api_key(groq_key)}")
            is_valid = api_key_manager.validate_api_key_format(groq_key, "groq")
            logger.info(f"GROQ_API_KEY format valid: {is_valid}")
        else:
            logger.error("❌ GROQ_API_KEY not found in environment")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing API key manager: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all tests"""
    logger.info("🧪 Starting Groq STT tests...")
    
    # Test API key manager
    logger.info("\n" + "="*50)
    logger.info("Testing API Key Manager")
    logger.info("="*50)
    test_api_key_manager()
    
    # Test Groq client
    logger.info("\n" + "="*50)
    logger.info("Testing Groq Client")
    logger.info("="*50)
    client_ok = test_groq_client()
    
    # Test Groq STT
    logger.info("\n" + "="*50)
    logger.info("Testing Groq STT Model")
    logger.info("="*50)
    stt_ok = test_groq_stt()
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("Test Summary")
    logger.info("="*50)
    logger.info(f"Groq Client: {'✅ OK' if client_ok else '❌ FAILED'}")
    logger.info(f"Groq STT: {'✅ OK' if stt_ok else '❌ FAILED'}")
    
    if client_ok and stt_ok:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
