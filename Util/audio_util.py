import os
import time
import tempfile
import requests
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_transcription(binary_audio: bytes) -> str:
    
    max_retries = 3
    base_delay = 2
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            temp_file.write(binary_audio)
            temp_file_path = temp_file.name
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Intento {attempt + 1}/{max_retries} de transcripción")
                
                with open(temp_file_path, 'rb') as audio_file:
                    files = {
                        'file': ('audio.ogg', audio_file, 'audio/ogg')
                    }
                    data = {
                        'model': 'whisper-1'
                    }
                    headers = {
                        'Authorization': f'Bearer {os.getenv("GEMINI_API_KEY")}'
                    }
                    
                    myfile = client.files.upload(file=temp_file_path)

                    response = client.models.generate_content(
                        model="gemini-2.5-flash", contents=["Transcribe this audio file", myfile]
                    )
                    
                    if response.status_code == 429:
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            print(f"⚠️ Rate limit. Reintentando en {delay}s...")
                            time.sleep(delay)
                            continue
                        else:
                            error_msg = response.json().get('error', {})
                            rate_limit_msg = error_msg.get('message', 'Límite de solicitudes excedido')
                            raise Exception(f"429 Too Many Requests después de {max_retries} intentos: {rate_limit_msg}")
                    
                    response.raise_for_status()
                    result = response.json()
                    texto = result.get('text', '')
                    
                    if not texto:
                        raise Exception(f"No se obtuvo transcripción. Respuesta: {result}")
                    
                    print(f"✅ Transcripción exitosa: {texto[:50]}...")
                    return texto
                    
            except requests.exceptions.HTTPError as error:
                if response.status_code == 429 and attempt < max_retries - 1:
                    continue
                raise error
            except Exception as error:
                error_str = str(error).lower()
                print(f"❌ Error en intento {attempt + 1}: {type(error).__name__} → {error}")
                
                if "429" in error_str or "too many requests" in error_str:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"⚠️ Rate limit. Reintentando en {delay}s...")
                        time.sleep(delay)
                        continue
                    raise Exception(f"429 después de {max_retries} intentos: {error}")
                
                raise error
        
        raise Exception("No se logró transcribir el audio después de varios intentos")
                
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass


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
