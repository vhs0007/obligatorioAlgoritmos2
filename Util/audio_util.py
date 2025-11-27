import os
import time
import io
import subprocess
import requests
from huggingface_hub import InferenceClient

HF_API_KEY = os.getenv("HF_API_KEY")
if not HF_API_KEY:
    raise ValueError("HF_API_KEY no configurada")

client = InferenceClient(api_key=HF_API_KEY)

MODEL_NAME = "openai/whisper-medium"


def convertir_audio_a_wav(binary_audio: bytes) -> bytes:
    try:
        print(f"🔄 Convirtiendo audio a WAV usando ffmpeg, tamaño original: {len(binary_audio)} bytes")
        
        # Crear archivo temporal de entrada
        input_buffer = io.BytesIO(binary_audio)
        
        # Usar ffmpeg para convertir a WAV
        process = subprocess.Popen(
            [
                'ffmpeg',
                '-i', 'pipe:0',  # Leer desde stdin
                '-f', 'wav',      # Formato de salida WAV
                '-ar', '16000',   # Sample rate 16kHz (recomendado para Whisper)
                '-ac', '1',       # Mono
                'pipe:1'          # Escribir a stdout
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate(input=binary_audio)
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore')
            raise Exception(f"ffmpeg falló con código {process.returncode}: {error_msg}")
        
        print(f"✅ Audio convertido a WAV, tamaño final: {len(stdout)} bytes")
        return stdout
        
    except FileNotFoundError:
        raise Exception("ffmpeg no está instalado o no está en el PATH. Por favor, instala ffmpeg.")
    except Exception as e:
        raise Exception(f"Error al convertir audio: {type(e).__name__} → {e}")


def transcribe_audio_hf(binary_audio: bytes) -> str:
    print(f"🎤 Iniciando transcripción con modelo {MODEL_NAME}, tamaño audio: {len(binary_audio)} bytes")
    wav_audio = convertir_audio_a_wav(binary_audio)
    result = client.automatic_speech_recognition(
        audio=wav_audio,
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
            wav_audio = convertir_audio_a_wav(binary_audio)
            
            print(f"📤 Enviando audio WAV a Hugging Face API...")
            result = client.automatic_speech_recognition(
                audio=wav_audio,
                model=MODEL_NAME
            )
            
            print(f"📝 Tipo de resultado: {type(result)}")
            print(f"📝 Resultado repr: {repr(result)}")
            
            # Intentar obtener información del resultado sin acceder a .text directamente
            texto = None
            
            # Primero verificar si es un dict
            if isinstance(result, dict):
                texto = result.get('text') or result.get('generated_text', '')
                print(f"✅ Texto obtenido de dict: {texto[:50] if texto else 'None'}...")
            
            # Si no funcionó, intentar como string
            elif isinstance(result, str):
                texto = result
                print(f"✅ Texto obtenido como string: {texto[:50] if texto else 'None'}...")
            
            # Si tiene atributo text, intentar accederlo con cuidado
            elif hasattr(result, 'text'):
                print(f"🔄 Resultado tiene atributo 'text', intentando acceder...")
                try:
                    # Verificar si text es una propiedad o método
                    text_attr = getattr(result, 'text', None)
                    if callable(text_attr):
                        texto = text_attr()
                    else:
                        texto = text_attr
                    print(f"✅ Texto obtenido de result.text: {texto[:50] if texto else 'None'}...")
                except StopIteration as e:
                    print(f"❌ StopIteration al acceder a result.text: {e}")
                    # Intentar convertir a dict o string
                    try:
                        if hasattr(result, '__dict__'):
                            result_dict = result.__dict__
                            texto = result_dict.get('text') or result_dict.get('generated_text', '')
                            print(f"✅ Texto obtenido de __dict__: {texto[:50] if texto else 'None'}...")
                    except Exception as e2:
                        print(f"❌ Error al acceder a __dict__: {type(e2).__name__} → {e2}")
                except Exception as e:
                    print(f"❌ Error al acceder a result.text: {type(e).__name__} → {e}")
            
            # Si es un iterador, intentar obtener elementos
            if not texto and hasattr(result, '__iter__') and not isinstance(result, (str, bytes, dict)):
                print(f"🔄 Intentando iterar sobre el resultado...")
                try:
                    # Convertir a lista para evitar problemas con iteradores
                    result_list = list(result)
                    print(f"📋 Resultado convertido a lista, longitud: {len(result_list)}")
                    if result_list:
                        first_item = result_list[0]
                        print(f"📋 Primer elemento: {first_item}, tipo: {type(first_item)}")
                        if isinstance(first_item, dict):
                            texto = first_item.get('text') or first_item.get('generated_text', '')
                        elif hasattr(first_item, 'text'):
                            try:
                                texto = first_item.text if not callable(first_item.text) else first_item.text()
                            except StopIteration:
                                texto = None
                        elif isinstance(first_item, str):
                            texto = first_item
                except StopIteration as e:
                    print(f"❌ StopIteration al iterar: {e}")
                    raise Exception(f"No se obtuvo transcripción. Iterador vacío: {result}")
                except Exception as e:
                    print(f"❌ Error al iterar: {type(e).__name__} → {e}")
            
            if not texto:
                # Último intento: convertir a string
                try:
                    texto = str(result)
                    if texto and texto != repr(result):
                        print(f"✅ Texto obtenido de str(result): {texto[:50]}...")
                    else:
                        raise Exception(f"No se obtuvo transcripción. Formato inesperado: {type(result)} → {result}")
                except:
                    raise Exception(f"No se obtuvo transcripción. Formato inesperado: {type(result)} → {result}")
            
            print(f"✅ Transcripción exitosa: {texto[:50]}...")
            return texto

        except StopIteration as e:
            print(f"❌ StopIteration en intento {attempt + 1}: {e}")
            print(f"📋 Stack trace completo:")
            import traceback
            traceback.print_exc()
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
