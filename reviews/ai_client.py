import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

AI_SERVICE_URL = getattr(settings, 'AI_SERVICE_URL', 'http://localhost:8001')


def detect_spoiler_via_ai(text):
    try:
        response = requests.post(
            f"{AI_SERVICE_URL}/spoiler/detect",
            json={"text": text},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return (
                data['has_spoiler'],
                data['confidence'],
                data['method'],
                data.get('reasoning', '')  
            )
    except Exception as e:
        logger.error(f"AI service error: {e}")
        return False, 0.0, "error", ""