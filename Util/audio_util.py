import os
import requests
import tempfile
import time
from huggingface_hub import InferenceClient

HF_API_KEY = os.getenv("HF_API_KEY")

_client = None

def get_hf_client():
    """Obtiene o crea el cliente de Hugging Face."""
    global _client
    if _client is None:
        if not HF_API_KEY:
            raise ValueError("Variable de entorno HF_API_KEY no configurada")
        _client = InferenceClient(token=HF_API_KEY)
    return _client


def transcribe_audio_hf(binary_audio: bytes) -> str:
    if not HF_API_KEY:
        raise ValueError("Variable de entorno HF_API_KEY no configurada")
    
    client = get_hf_client()
    response = client.audio_to_text(
        model="openai/whisper-tiny",
        audio_bytes=binary_audio,
    )
    return response["text"]


def get_transcription(binary_audio: bytes) -> str:
    if not HF_API_KEY:
        raise ValueError("Variable de entorno HF_API_KEY no configurada")
    
    max_retries = 2
    base_delay = 2
    client = get_hf_client()
    
    for attempt in range(max_retries):
        try:
            response = client.audio_to_text(
                model="openai/whisper-tiny",
                audio_bytes=binary_audio,
            )
            return response["text"]
                
        except Exception as error:
            error_str = str(error).lower()
            if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"⚠️ Rate limit alcanzado. Reintentando en {delay} segundos... (intento {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    raise Exception(f"429 Too Many Requests después de {max_retries} intentos: {str(error)}")
            raise error


def get_url_media(id_audio: str) -> str:
    url = f'https://graph.facebook.com/v18.0/{id_audio}/'
    headers = {
        'Authorization': f'Bearer {os.getenv("WHATSAPP_ACCESS_TOKEN")}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()['url']
    except Exception as error:
        raise error


def get_binary_media(url: str) -> bytes:
    headers = {
        'Authorization': f'Bearer {os.getenv("WHATSAPP_ACCESS_TOKEN")}'
    }
    
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        return response.content
    except Exception as error:
        raise error

