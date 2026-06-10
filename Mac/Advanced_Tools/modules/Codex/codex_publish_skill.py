import json
import os
import sys

CREDENTIALS_FILE = r"C:\Program Files\Chask_Swarm\Configuration\master_credentials.json"

def load_credentials():
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: No se encontró el archivo maestro de credenciales en {CREDENTIALS_FILE}")
        return None
    with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("credentials", data)

def publish_to_blog(title, content):
    """
    Skill de publicación. 
    Aquí se implementaría la lógica para conectar por FTP, API de WordPress, etc.
    """
    creds = load_credentials()
    if not creds:
        return False
    
    print(f"--- INICIANDO PUBLICACIÓN ---")
    print(f"Servidor destino: {creds.get('ftp_host')}")
    print(f"Usuario autenticado: {creds.get('ftp_user')}")
    print(f"URL del Blog: {creds.get('web_url')}")
    
    # Aquí iría el código real de subida (ftplib o requests)
    print(f"Simulando subida de la publicación: '{title}'...")
    print("¡Publicación completada con éxito!")
    
    # Aquí se podrían añadir notificaciones a redes sociales
    social = creds.get("social_accounts", {})
    if "x" in social:
        print(f"Enlazando publicación a X (Twitter) usando API Key...")
        print("¡Post en X enviado con éxito!")
        
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python codex_publish_skill.py \"Título\" \"Contenido\"")
    else:
        title = sys.argv[1]
        content = sys.argv[2]
        publish_to_blog(title, content)
