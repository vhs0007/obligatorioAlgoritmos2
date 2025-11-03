"""
Script para verificar los permisos del token de acceso
"""

import requests
from whatsapp_api import WHATSAPP_ACCESS_TOKEN, WHATSAPP_API_URL

def verificar_permisos_token():
    """Verifica qué permisos tiene el token actual."""
    print("="*60)
    print("🔍 Verificando permisos del token de acceso")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }
    
    # Verificar información del token
    try:
        url = f"{WHATSAPP_API_URL}/me"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Token válido")
            print(f"   👤 App ID: {data.get('id', 'N/A')}")
            print(f"   📝 Nombre: {data.get('name', 'N/A')}")
        else:
            error_data = response.json()
            print(f"\n❌ Error con el token: {error_data.get('error', {}).get('message', 'Error desconocido')}")
            return False
    except Exception as e:
        print(f"\n❌ Error al verificar token: {str(e)}")
        return False
    
    # Intentar obtener permisos del token
    try:
        url = f"{WHATSAPP_API_URL}/me/permissions"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            permisos = data.get('data', [])
            print(f"\n📋 Permisos del token:")
            permisos_whatsapp = []
            for permiso in permisos:
                permiso_str = permiso.get('permission', 'N/A')
                estado = permiso.get('status', 'N/A')
                icono = "✅" if estado == "granted" else "❌"
                print(f"   {icono} {permiso_str}: {estado}")
                if 'whatsapp' in permiso_str.lower():
                    permisos_whatsapp.append(permiso_str)
            
            # Verificar permisos necesarios
            print(f"\n🔍 Verificando permisos necesarios para WhatsApp:")
            permisos_necesarios = [
                "whatsapp_business_messaging",
                "whatsapp_business_management"
            ]
            
            permisos_otorgados = [p.get('permission') for p in permisos if p.get('status') == 'granted']
            
            faltantes = []
            for permiso in permisos_necesarios:
                if permiso in permisos_otorgados:
                    print(f"   ✅ {permiso}: Otorgado")
                else:
                    print(f"   ❌ {permiso}: FALTA")
                    faltantes.append(permiso)
            
            if faltantes:
                print(f"\n⚠️ FALTAN PERMISOS NECESARIOS!")
                print(f"\n💡 Para solucionarlo:")
                print(f"   1. Ve a https://developers.facebook.com/apps/")
                print(f"   2. Selecciona tu app → WhatsApp → API Setup")
                print(f"   3. Genera un nuevo token con los permisos:")
                for permiso in faltantes:
                    print(f"      - {permiso}")
                print(f"\n   4. O usa Graph API Explorer:")
                print(f"      https://developers.facebook.com/tools/explorer/")
                print(f"      - Selecciona tu app")
                print(f"      - Agrega los permisos faltantes")
                print(f"      - Genera un nuevo token")
                return False
            else:
                print(f"\n✅ Todos los permisos necesarios están otorgados!")
                return True
        else:
            print(f"\n⚠️ No se pudieron verificar los permisos")
            print(f"   Esto puede ser normal en algunos casos")
            return True
    except Exception as e:
        print(f"\n⚠️ Error al verificar permisos: {str(e)}")
        print(f"   Esto puede ser normal en algunos casos")
        return True
    
    print("\n" + "="*60)
    return True

if __name__ == "__main__":
    verificar_permisos_token()
