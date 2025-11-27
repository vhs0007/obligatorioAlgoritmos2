import os
import requests
import tempfile
import time

HF_API_KEY = os.getenv("HF_API_KEY")


def transcribe_audio_hf(binary_audio: bytes) -> str:
    if not HF_API_KEY:
        raise ValueError("Variable de entorno HF_API_KEY no configurada")

    files = {"file": ("audio.ogg", binary_audio, "audio/ogg")}
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    response = requests.post(
        "https://api-inference.huggingface.co/models/openai/whisper-tiny",
        headers=headers,
        files=files
    )

    response.raise_for_status()
    data = response.json()

    if "text" in data:
        return data["text"]
    else:
        return data[0]["text"]


def get_transcription(binary_audio: bytes) -> str:

    if not HF_API_KEY:
        raise ValueError("Variable de entorno HF_API_KEY no configurada")
    
    max_retries = 2
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
            files = {"file": ("audio.ogg", binary_audio, "audio/ogg")}
            headers = {"Authorization": f"Bearer {HF_API_KEY}"}
            
            response = requests.post(
                "https://api-inference.huggingface.co/models/openai/whisper-tiny",
                headers=headers,
                files=files
            )
            
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"⚠️ Rate limit alcanzado. Reintentando en {delay} segundos... (intento {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    try:
                        error_msg = response.json().get('error', {})
                        rate_limit_msg = error_msg.get('message', 'Límite de solicitudes excedido')
                    except:
                        rate_limit_msg = 'Límite de solicitudes excedido'
                    raise requests.exceptions.HTTPError(
                        f"429 Too Many Requests después de {max_retries} intentos: {rate_limit_msg}"
                    )
            
            response.raise_for_status()
            data = response.json()
            
            if "text" in data:
                return data["text"]
            else:
                return data[0]["text"]
                
        except requests.exceptions.HTTPError as error:
            if hasattr(error, 'response') and error.response is not None:
                if error.response.status_code != 429:
                    raise error
            if attempt == max_retries - 1:
                raise error
            continue
        except Exception as error:
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

