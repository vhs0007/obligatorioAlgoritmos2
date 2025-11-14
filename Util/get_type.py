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
            print("Tipo interactivo no reconocido")

    elif tipo == "location":
        loc = message.get("location", {})
        lat, lon = loc.get("latitude"), loc.get("longitude")
        if lat and lon:
            contenido = f"{lat},{lon}"

    elif tipo == "audio":
        contenido = message.get("audio", {}).get("id", "")

    else:
        print(f"Tipo de mensaje no manejado: {tipo}")

    return tipo, contenido
