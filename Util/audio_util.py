import os
import requests
import tempfile
import time


def get_transcription(binary_audio: bytes) -> str:
    temp_file_path = None
    try:
        # Intentar primero con OPENAI_API_KEY, luego con OPEN_API_KEY como fallback
        openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY o OPEN_API_KEY no está configurada en las variables de entorno")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            temp_file.write(binary_audio)
            temp_file_path = temp_file.name
        
        try:
            # Retry con backoff exponencial para manejar rate limiting (429)
            max_retries = 3
            base_delay = 2  # segundos
            
            for attempt in range(max_retries):
                with open(temp_file_path, 'rb') as audio_file:
                    files = {
                        'file': ('audio.ogg', audio_file, 'audio/ogg')
                    }
                    data = {
                        'model': 'whisper-1'
                    }
                    headers = {
                        'Authorization': f'Bearer {openai_api_key}'
                    }
                    
                    response = requests.post(
                        'https://api.openai.com/v1/audio/transcriptions',
                        headers=headers,
                        files=files,
                        data=data
                    )
                    
                    # Si es 429, esperar y reintentar
                    if response.status_code == 429:
                        if attempt < max_retries - 1:
                            # Backoff exponencial: 2s, 4s, 8s
                            delay = base_delay * (2 ** attempt)
                            print(f"⚠️ Rate limit alcanzado. Reintentando en {delay} segundos... (intento {attempt + 1}/{max_retries})")
                            time.sleep(delay)
                            continue
                        else:
                            # Último intento falló
                            error_msg = response.json().get('error', {})
                            rate_limit_msg = error_msg.get('message', 'Límite de solicitudes excedido')
                            raise requests.exceptions.HTTPError(
                                f"429 Too Many Requests después de {max_retries} intentos: {rate_limit_msg}"
                            )
                    
                    # Si hay otro error HTTP, lanzarlo
                    response.raise_for_status()
                    return response.json()['text']
                
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                
    except requests.exceptions.HTTPError as error:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass
        raise error
    except Exception as error:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass
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

