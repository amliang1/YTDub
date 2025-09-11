import json
import requests
from pathlib import Path
import os
from app.core.logging import get_logger

logger = get_logger(__name__)

class AllTalkTTS:
    def __init__(self, host: str = "127.0.0.1", port: int = 7852):
        """
        Initialize AllTalk TTS client.
        
        Args:
            host: AllTalk server host
            port: AllTalk server port
        """
        self.base_url = f"http://{host}:{port}"
        self.output_dir = Path("tts_output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_speech(self, text: str, output_file: str, 
                       voice_model: str = "tts_models/multilingual/multi-dataset/xtts_v2", 
                       language: str = "en") -> str:
        """
        Generate speech from text using AllTalk TTS.
        
        Args:
            text: Text to convert to speech
            output_file: Path to save the audio file
            voice_model: TTS model to use
            language: Language code for the text
            
        Returns:
            Path to the generated audio file
        """
        try:
            # Prepare the request payload
            payload = {
                "text": text,
                "model": voice_model,
                "language": language,
                "output_file": str(self.output_dir / output_file),
                "speed": 1.0,
                "temperature": 0.7
            }
            
            # Make API call to AllTalk
            response = requests.post(
                f"{self.base_url}/api/tts",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"AllTalk API error: {response.text}")
            
            result = response.json()
            if result.get("status") != "success":
                raise Exception(f"TTS generation failed: {result.get('message')}")
            
            output_path = result.get("output_file")
            if not os.path.exists(output_path):
                raise Exception(f"Generated audio file not found: {output_path}")
            
            logger.info(f"Successfully generated speech: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            raise

    def list_available_models(self) -> list:
        """
        Get list of available TTS models.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/models")
            if response.status_code != 200:
                raise Exception(f"Failed to get models: {response.text}")
            
            return response.json().get("models", [])
            
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            raise

    def get_languages(self) -> list:
        """
        Get list of supported languages.
        
        Returns:
            List of language codes
        """
        try:
            response = requests.get(f"{self.base_url}/api/languages")
            if response.status_code != 200:
                raise Exception(f"Failed to get languages: {response.text}")
            
            return response.json().get("languages", [])
            
        except Exception as e:
            logger.error(f"Error listing languages: {str(e)}")
            raise
