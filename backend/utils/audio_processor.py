"""
Audio processing utilities for voice bot functionality
"""
import os
import tempfile
import base64
from typing import Optional, Tuple, Union
from io import BytesIO

class AudioProcessor:
    """Utility class for audio processing operations"""
    
    def __init__(self):
        self.supported_formats = ['wav', 'mp3', 'ogg', 'webm', 'm4a', 'flac']
        self.max_file_size = 25 * 1024 * 1024  # 25MB
    
    def validate_audio_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate audio file format and size
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return False, f"File size ({file_size} bytes) exceeds maximum ({self.max_file_size} bytes)"
            
            # Check file format
            file_extension = file_path.lower().split('.')[-1]
            if file_extension not in self.supported_formats:
                return False, f"Unsupported format: {file_extension}. Supported: {self.supported_formats}"
            
            return True, "Valid audio file"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def save_uploaded_audio(self, audio_data: bytes, filename: str = "audio.wav") -> str:
        """
        Save uploaded audio data to temporary file
        
        Args:
            audio_data: Audio data as bytes
            filename: Desired filename
            
        Returns:
            Path to saved temporary file
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=f'.{filename.split(".")[-1]}', delete=False) as temp_file:
                temp_file.write(audio_data)
                return temp_file.name
                
        except Exception as e:
            raise Exception(f"Error saving audio data: {str(e)}")
    
    async def base64_to_audio_file_async(self, base64_data: str, output_format: str = "wav") -> str:
        """
        Async convert base64 encoded audio to temporary file

        Args:
            base64_data: Base64 encoded audio data
            output_format: Output audio format

        Returns:
            Path to temporary audio file
        """
        try:
            from utils.performance_optimizer import async_optimizer

            # Run file operations in thread pool to avoid blocking
            return await async_optimizer.run_in_thread(
                self.base64_to_audio_file, base64_data, output_format
            )

        except Exception as e:
            raise Exception(f"Error converting base64 to audio file: {str(e)}")

    def base64_to_audio_file(self, base64_data: str, output_format: str = "wav") -> str:
        """
        Convert base64 encoded audio to temporary file (sync version)
        """
        try:
            # Decode base64 data
            audio_data = base64.b64decode(base64_data)

            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False) as temp_file:
                temp_file.write(audio_data)
                return temp_file.name

        except Exception as e:
            raise Exception(f"Error converting base64 to audio file: {str(e)}")
    
    def audio_file_to_base64(self, file_path: str) -> str:
        """
        Convert audio file to base64 string
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Base64 encoded audio data
        """
        try:
            with open(file_path, "rb") as audio_file:
                audio_data = audio_file.read()
                return base64.b64encode(audio_data).decode('utf-8')
                
        except Exception as e:
            raise Exception(f"Error converting audio file to base64: {str(e)}")
    
    def cleanup_temp_file(self, file_path: str) -> bool:
        """
        Clean up temporary audio file
        
        Args:
            file_path: Path to temporary file
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                return True
            return False
            
        except Exception:
            return False
    
    def get_audio_info(self, file_path: str) -> dict:
        """
        Get basic information about audio file
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with audio file information
        """
        try:
            if not os.path.exists(file_path):
                return {"error": "File does not exist"}
            
            file_size = os.path.getsize(file_path)
            file_extension = file_path.lower().split('.')[-1]
            
            return {
                "file_path": file_path,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "format": file_extension,
                "is_supported": file_extension in self.supported_formats
            }
            
        except Exception as e:
            return {"error": f"Error getting audio info: {str(e)}"}
    
    def create_audio_response(self, audio_data: bytes, filename: str = "response.wav") -> dict:
        """
        Create standardized audio response format
        
        Args:
            audio_data: Audio data as bytes
            filename: Filename for the audio
            
        Returns:
            Dictionary with audio response data
        """
        try:
            # Convert to base64 for web transmission
            base64_audio = base64.b64encode(audio_data).decode('utf-8')
            
            return {
                "audio_data": base64_audio,
                "filename": filename,
                "format": filename.split('.')[-1],
                "size_bytes": len(audio_data),
                "mime_type": f"audio/{filename.split('.')[-1]}"
            }
            
        except Exception as e:
            raise Exception(f"Error creating audio response: {str(e)}")

# Global audio processor instance
audio_processor = AudioProcessor()
