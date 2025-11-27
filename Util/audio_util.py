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
    print(f"🎤 Iniciando transcripción con modelo {MODEL_NAME}, tamaño audio: {len(binary_audio)} bytes")
    result = client.automatic_speech_recognition(
        audio=binary_audio,
        model=MODEL_NAME
    )
    print(f"📝 Tipo de resultado: {type(result)}, contenido: {result}")
    
    # Manejar diferentes formatos de respuesta
    if hasattr(result, 'text'):
        texto = result.text
    elif isinstance(result, dict):
        texto = result.get('text') or result.get('generated_text', '')
    elif isinstance(result, str):
        texto = result
    else:
        # Si es un iterador, obtener el primer elemento
        try:
            if hasattr(result, '__iter__') and not isinstance(result, (str, bytes)):
                texto = next(iter(result))
                if isinstance(texto, dict):
                    texto = texto.get('text') or texto.get('generated_text', '')
        except StopIteration:
            raise Exception(f"No se obtuvo transcripción. Resultado vacío: {result}")
    
    if not texto:
        raise Exception(f"No se obtuvo transcripción. Formato inesperado: {type(result)} → {result}")
    
    print(f"✅ Transcripción obtenida: {texto[:50]}...")
    return texto


def get_transcription(binary_audio: bytes) -> str:
    print(f"🔄 get_transcription: tamaño audio {len(binary_audio)} bytes")
    max_retries = 3
    base_delay = 2

    for attempt in range(max_retries):
        try:
            print(f"🔄 Intento {attempt + 1}/{max_retries} de transcripción")
            result = client.automatic_speech_recognition(
                audio=binary_audio,
                model=MODEL_NAME
            )
            print(f"📝 Tipo de resultado: {type(result)}, contenido: {result}")
            
            # Manejar diferentes formatos de respuesta
            if hasattr(result, 'text'):
                texto = result.text
            elif isinstance(result, dict):
                texto = result.get('text') or result.get('generated_text', '')
            elif isinstance(result, str):
                texto = result
            else:
                # Si es un iterador, obtener el primer elemento
                try:
                    if hasattr(result, '__iter__') and not isinstance(result, (str, bytes)):
                        texto = next(iter(result))
                        if isinstance(texto, dict):
                            texto = texto.get('text') or texto.get('generated_text', '')
                except StopIteration:
                    raise Exception(f"No se obtuvo transcripción. Resultado vacío: {result}")
            
            if not texto:
                raise Exception(f"No se obtuvo transcripción. Formato inesperado: {type(result)} → {result}")
            
            print(f"✅ Transcripción exitosa: {texto[:50]}...")
            return texto

        except StopIteration as e:
            print(f"❌ StopIteration en intento {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                delay = base_delay * (attempt + 1)
                print(f"⚠️ Reintentando en {delay}s...")
                time.sleep(delay)
                continue
            raise Exception(f"StopIteration después de {max_retries} intentos: {e}")
            
        except Exception as error:
            error_type = type(error).__name__
            error_str = str(error).lower()
            print(f"❌ Error en intento {attempt + 1}: {error_type} → {error}")
            
            if "429" in error_str or "too many requests" in error_str:
                if attempt < max_retries - 1:
                    delay = base_delay * (attempt + 1)
                    print(f"⚠️ Rate limit. Reintentando en {delay}s...")
                    time.sleep(delay)
                    continue
                raise Exception(f"429 después de {max_retries} intentos: {error}")

            # Para otros errores, lanzar inmediatamente
            raise error

    raise Exception("No se logró transcribir el audio después de varios intentos")


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
