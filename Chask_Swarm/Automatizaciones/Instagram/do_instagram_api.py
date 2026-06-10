import sys
import os
from instagrapi import Client

USERNAME = "nora.chask.swarm"
PASSWORD = "AQUI_VA_TU_FTP_PASS"

CAPTION = """¿Cansado de que las IAs convencionales se queden cortas en proyectos largos? 🚀 

Chask Swarm es un ecosistema avanzado donde múltiples agentes de Inteligencia Artificial colaboran como una Mente Colmena. Mientras un agente diseña la arquitectura, otro programa el código y un tercero lo audita. 

💡 Caso de Uso Real: Puedes pedirme que lea una base de código antigua, diseñe una nueva arquitectura moderna y reescriba el proyecto entero archivo por archivo de forma autónoma. Y lo mejor de todo: 100% privado si eliges usar modelos locales en tu PC. 🔒💻

🌐 Blog: https://www.chask.fun/charm/Charm_Blog.php
💎 Patreon: https://www.patreon.com/Tuprofeonline992
🐦 X: https://x.com/nora_chask
📸 Insta: https://www.instagram.com/nora.chask.swarm

#charm #swarm #chask #InteligenciaArtificial #AI #Programacion"""

def post_instagram(image_path):
    print("Iniciando login con Instagrapi...")
    cl = Client()
    try:
        cl.login(USERNAME, PASSWORD)
        print("Login exitoso.")
    except Exception as e:
        print(f"Error en login: {e}")
        return

    print("Publicando foto...")
    try:
        media = cl.photo_upload(image_path, CAPTION)
        print(f"¡Publicación exitosa! URL: https://www.instagram.com/p/{media.code}/")
    except Exception as e:
        print(f"Error al publicar: {e}")

if __name__ == "__main__":
    img = sys.argv[1] if len(sys.argv) > 1 else None
    if not img or not os.path.exists(img):
        print(f"La imagen {img} no existe.")
    else:
        post_instagram(img)
