import os
import requests
import tempfile
import time

HF_API_KEY = os.getenv("HF_API_KEY")


def transcribe_audio_hf(binary_audio: bytes) -> str:
    if not HF_API_KEY:
        raise ValueError("Variable de entorno HF_API_KEY no configurada")
    
    model = "openai/whisper-small"
    
    response = requests.post(
        f"https://api-inference.huggingface.co/models/{model}",
        headers={"Authorization": f"Bearer {HF_API_KEY}"},
        files={"file": ("audio.ogg", binary_audio, "audio/ogg")}
    )
    
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code} → {response.text}")
    
    data = response.json()
    return data["text"]


def get_transcription(binary_audio: bytes) -> str:
    if not HF_API_KEY:
        raise ValueError("Variable de entorno HF_API_KEY no configurada")
    
    model = "openai/whisper-small"
    max_retries = 2
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers={"Authorization": f"Bearer {HF_API_KEY}"},
                files={"file": ("audio.ogg", binary_audio, "audio/ogg")}
            )
            
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"⚠️ Rate limit alcanzado. Reintentando en {delay} segundos... (intento {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    raise Exception(f"429 Too Many Requests después de {max_retries} intentos: {response.text}")
            
            if response.status_code != 200:
                raise Exception(f"Error: {response.status_code} → {response.text}")
            
            data = response.json()
            return data["text"]
                
        except Exception as error:
            error_str = str(error).lower()
            if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
                if attempt == max_retries - 1:
                    raise error
                continue
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

