import os
import requests
import tempfile


def get_transcription(binary_audio: bytes) -> str:
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            temp_file.write(binary_audio)
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as audio_file:
                files = {
                    'file': ('audio.ogg', audio_file, 'audio/ogg')
                }
                data = {
                    'model': 'whisper-1'
                }
                headers = {
                    'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}'
                }
                
                response = requests.post(
                    'https://api.openai.com/v1/audio/transcriptions',
                    headers=headers,
                    files=files,
                    data=data
                )
                
                response.raise_for_status()
                return response.json()['text']
                
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as error:
        if temp_file and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass
        raise error


def get_url_media(id_audio: str) -> str:
    url = f'https://graph.facebook.com/v18.0/{id_audio}/'
    headers = {
        'Authorization': f'Bearer {os.getenv("WHATSAPP_CLOUD_API_KEY")}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()['url']
    except Exception as error:
        raise error


def get_binary_media(url: str) -> bytes:
    headers = {
        'Authorization': f'Bearer {os.getenv("WHATSAPP_CLOUD_API_KEY")}'
    }
    
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        return response.content
    except Exception as error:
        raise error

