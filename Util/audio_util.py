import os
import time
import requests
from huggingface_hub import InferenceClient

HF_API_KEY = os.getenv("HF_API_KEY")
if not HF_API_KEY:
    raise ValueError("HF_API_KEY no configurada")

client = InferenceClient(api_key=HF_API_KEY)

MODEL_NAME = "openai/whisper-small"


def transcribe_audio_hf(binary_audio: bytes) -> str:
    result = client.automatic_speech_recognition(
        audio=binary_audio,
        model=MODEL_NAME
    )
    return result.text


def get_transcription(binary_audio: bytes) -> str:
    max_retries = 3
    base_delay = 2

    for attempt in range(max_retries):
        try:
            result = client.automatic_speech_recognition(
                audio=binary_audio,
                model=MODEL_NAME
            )
            return result.text

        except Exception as error:
            error_str = str(error).lower()
            if "429" in error_str or "too many requests" in error_str:
                if attempt < max_retries - 1:
                    delay = base_delay * (attempt + 1)
                    print(f"⚠️ Rate limit. Reintentando en {delay}s...")
                    time.sleep(delay)
                    continue
                raise Exception(f"429 después de {max_retries} intentos: {error}")

            raise error

    raise Exception("No se logró transcribir el audio")


def get_url_media(id_audio: str) -> str:
    url = f'https://graph.facebook.com/v18.0/{id_audio}/'
    headers = {
        'Authorization': f'Bearer {os.getenv("WHATSAPP_ACCESS_TOKEN")}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['url']


def get_binary_media(url: str) -> bytes:
    headers = {
        'Authorization': f'Bearer {os.getenv("WHATSAPP_ACCESS_TOKEN")}'
    }
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()
    return response.content
