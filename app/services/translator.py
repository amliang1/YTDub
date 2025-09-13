import os
import time
import random
from typing import List, Optional

import requests
from app.core.logging import get_logger
from app.core.settings import settings

logger = get_logger(__name__)

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_time_sec: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_time_sec = recovery_time_sec
        self.failures = 0
        self.opened_at: Optional[float] = None

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        if (time.time() - self.opened_at) >= self.recovery_time_sec:
            # half-open: allow one request
            return True
        return False

    def on_success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def on_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = time.time()


class Translator:
    def __init__(self, failure_threshold: int = 5, recovery_time_sec: float = 30.0):
        """Google Translate client with retry + circuit breaker."""
        # Prefer settings/env; avoid hardcoded secrets
        self.api_key = (
            settings.google_translate_api_key
            or os.getenv("GOOGLE_TRANSLATE_API_KEY")
            or "test"
        )
        self.base_url = "https://translation.googleapis.com/language/translate/v2"
        self._breaker = CircuitBreaker(failure_threshold, recovery_time_sec)
        logger.info("Initialized Translate client (key set=%s)", bool(self.api_key))

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
        def do_request():
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
            return result['data']['translations'][0]['translatedText']

        if not source_language:
            source_language = self.detect_language(text)

        return self._with_retry(do_request)

    def translate_batch(
        self,
        texts: List[str],
        target_language: str,
        source_language: Optional[str] = None,
        max_per_request: int = 100,
    ) -> List[str]:
        """Translate multiple strings efficiently with retries and circuit breaker.

        Splits into chunks, sends list in single API call using repeated 'q' params.
        If source_language is not given, detect once from first non-empty string.
        """
        if not texts:
            return []

        if not source_language:
            sample = next((t for t in texts if t), "")
            if sample:
                source_language = self.detect_language(sample)

        outputs: List[str] = []
        for i in range(0, len(texts), max_per_request):
            batch = texts[i : i + max_per_request]

            def do_request(batch=batch):
                # multiple 'q' values
                params = [('key', self.api_key), ('target', target_language)]
                if source_language:
                    params.append(('source', source_language))
                for t in batch:
                    params.append(('q', t))
                response = requests.post(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()['data']['translations']
                return [item['translatedText'] for item in data]

            translated = self._with_retry(do_request)
            outputs.extend(translated)
        return outputs

    def _with_retry(self, func, max_retries: int = 3, base_delay: float = 0.3, max_delay: float = 2.0):
        """Execute func with exponential backoff and circuit breaker."""
        if not self._breaker.allow():
            raise RuntimeError("translator_circuit_open")

        attempt = 0
        while True:
            try:
                result = func()
                self._breaker.on_success()
                return result
            except Exception as e:
                attempt += 1
                self._breaker.on_failure()
                if attempt > max_retries:
                    logger.error("Translation failed after retries: %s", e)
                    raise
                delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
                delay += random.uniform(0, delay * 0.1)
                time.sleep(delay)
