from Util.audio_util import get_url_media, get_binary_media, get_transcription


def get_type(message):
    tipo = message.get("type", "unknown")
    contenido = ""

    if tipo == "text":
        contenido = message.get("text", {}).get("body", "")

    elif tipo == "interactive":
        interactive = message.get("interactive", {})
        t = interactive.get("type")
        if t == "button_reply":
            contenido = interactive["button_reply"].get("id", "")
        elif t == "list_reply":
            contenido = interactive["list_reply"].get("id", "")
        else:
            print("⚠️ Tipo interactivo no reconocido")

    elif tipo == "location":
        loc = message.get("location", {})
        lat, lon = loc.get("latitude"), loc.get("longitude")
        if lat and lon:
            contenido = f"{lat},{lon}"

    elif tipo == "audio":
        try:
            id_audio = message.get("audio", {}).get("id", "")
            if not id_audio:
                contenido = "No pude procesar el audio. Por favor, envía un mensaje de texto."
            else:
                url = get_url_media(id_audio)
                binary_audio = get_binary_media(url)
                contenido = get_transcription(binary_audio)
        except Exception as error:
            print(f"⚠️ Error al procesar audio: {error}")
            contenido = "No pude procesar el audio. Por favor, envía un mensaje de texto."

    else:
        print(f"⚠️ Tipo de mensaje no manejado: {tipo}")

    return tipo, contenido
