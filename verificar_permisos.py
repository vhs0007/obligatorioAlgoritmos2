import requests
from whatsapp_api import WHATSAPP_ACCESS_TOKEN, WHATSAPP_API_URL

def verificar_permisos_token():
    print("==============================================================")
    print("Verificando permisos del token de acceso")
    print("==============================================================")
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }
    
    try:
        url = f"{WHATSAPP_API_URL}/me"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"Token válido")
            print(f"App ID: {data.get('id', 'N/A')}")
            print(f"Nombre: {data.get('name', 'N/A')}")
        else:
            error_data = response.json()
            print(f"Error con el token: {error_data.get('error', {}).get('message', 'Error desconocido')}")
            return False
    except Exception as e:
        print(f"Error al verificar token: {str(e)}")
        return False
    
    try:
        url = f"{WHATSAPP_API_URL}/me/permissions"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            permisos = data.get('data', [])
            print(f"Permisos del token:")
            permisos_whatsapp = []
            for permiso in permisos:
                permiso_str = permiso.get('permission', 'N/A')
                estado = permiso.get('status', 'N/A')
                print(f"{permiso_str}: {estado}")
                if 'whatsapp' in permiso_str.lower():
                    permisos_whatsapp.append(permiso_str)
            
            print(f"Verificando permisos necesarios para WhatsApp:")
            permisos_necesarios = [
                "whatsapp_business_messaging",
                "whatsapp_business_management"
            ]
            
            permisos_otorgados = [p.get('permission') for p in permisos if p.get('status') == 'granted']
            
            faltantes = []
            for permiso in permisos_necesarios:
                if permiso in permisos_otorgados:
                    print(f"{permiso}: Otorgado")
                else:
                    print(f"{permiso}: FALTA")
                    faltantes.append(permiso)
            
            if faltantes:
                print("FALTAN PERMISOS NECESARIOS!")
                print("Para solucionarlo:")
                print("1. Ve a https://developers.facebook.com/apps/")
                print("2. Selecciona tu app → WhatsApp → API Setup")
                print("3. Genera un nuevo token con los permisos:")
                for permiso in faltantes:
                    print(f"{permiso}")
                print("4. O usa Graph API Explorer:")
                print("https://developers.facebook.com/tools/explorer/")
                print("Selecciona tu app")
                print("Agrega los permisos faltantes")
                print("Genera un nuevo token")
                return False
            else:
                print("Todos los permisos necesarios están otorgados!")
                return True
        else:
            print("No se pudieron verificar los permisos")
            print("Esto puede ser normal en algunos casos")
            return True
    except Exception as e:
        print("Error al verificar permisos: {str(e)}")
        print("Esto puede ser normal en algunos casos")
        return True
    
    print("==============================================================")
    return True

if __name__ == "__main__":
    verificar_permisos_token()
