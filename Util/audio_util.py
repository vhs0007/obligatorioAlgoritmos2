import os
import requests
import time

HF_API_KEY = os.getenv("HF_API_KEY")


def transcribe_audio_hf(binary_audio: bytes) -> str:
    if not HF_API_KEY:
        raise ValueError("Variable de entorno HF_API_KEY no configurada")

    model = "openai/whisper-small"

    response = requests.post(
        f"https://api-inference.huggingface.co/models/{model}",
        headers={
            "Authorization": f"Bearer {HF_API_KEY}"
        },
        data={"inputs": binary_audio},
    )

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code} → {response.text}")

    result = response.json()

    text = result.get("text") or result.get("generated_text")
    if not text:
        raise Exception(f"Formato inesperado: {result}")

    return text


def get_transcription(binary_audio: bytes) -> str:
    if not HF_API_KEY:
        raise ValueError("Variable de entorno HF_API_KEY no configurada")

    model = "openai/whisper-small"
    max_retries = 3
    base_delay = 2

    for attempt in range(max_retries):
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers={"Authorization": f"Bearer {HF_API_KEY}"},
            data={"inputs": binary_audio},
        )

        if response.status_code == 429:
            delay = base_delay * (attempt + 1)
            print(f"⚠️ Rate limit. Reintentando en {delay}s...")
            time.sleep(delay)
            continue

        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code} → {response.text}")

        result = response.json()
        text = result.get("text") or result.get("generated_text")
        if not text:
            raise Exception(f"Formato inesperado: {result}")
        return text

    raise Exception("No se pudo transcribir el audio después de varios intentos")


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

