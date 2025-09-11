import requests
import os
from app.core.logging import get_logger

logger = get_logger(__name__)

class Translator:
    def __init__(self):
        """
        Initialize Google Cloud Translate client.
        Uses API key authentication.
        """
        self.api_key = "AIzaSyDy8otd4bgVBSY9N9DA2mHNFglSDguds10"
        self.base_url = "https://translation.googleapis.com/language/translate/v2"
        logger.info("Successfully initialized Google Cloud Translate client")

    def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text.
        
        Args:
            text: Text to detect language for
            
        Returns:
            Language code (e.g., 'en', 'es', 'fr')
        """
        try:
            url = f"{self.base_url}/detect"
            params = {
                'key': self.api_key,
                'q': text
            }
            
            response = requests.post(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            detected_lang = result['data']['detections'][0][0]['language']
            logger.info(f"Detected language: {detected_lang}")
            return detected_lang
            
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            raise

    def translate(self, text: str, target_language: str, source_language: str = None) -> str:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'es' for Spanish)
            source_language: Source language code (optional, will be auto-detected if not provided)
            
        Returns:
            Translated text
        """
        try:
            if not source_language:
                source_language = self.detect_language(text)
                
            params = {
                'key': self.api_key,
                'q': text,
                'target': target_language,
            }
            
            if source_language:
                params['source'] = source_language
                
            response = requests.post(self.base_url, params=params)
            response.raise_for_status()
            
            result = response.json()
            translated_text = result['data']['translations'][0]['translatedText']
            logger.info(f"Successfully translated text from {source_language} to {target_language}")
            return translated_text
            
        except Exception as e:
            logger.error(f"Error translating text: {str(e)}")
            raise
