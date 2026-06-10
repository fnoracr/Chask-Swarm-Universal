import time
import os
from playwright.sync_api import sync_playwright

YT_DIR = r"C:\Program Files\Chask_Swarm\Automatizaciones\YouTubeBotProfile"

def login_youtube():
    print("Abriendo navegador para que Fernando inicie sesión en YouTube (Google)...")
    os.makedirs(YT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=YT_DIR,
            channel="chrome",
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--start-maximized'
            ],
            no_viewport=True,
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        print("Navegando a YouTube...")
        page.goto("https://accounts.google.com/signin/v2/identifier?service=youtube&continue=https%3A%2F%2Fwww.youtube.com%2Fsignin%3Faction_handle%3Dsignin%26app%3Ddesktop%26hl%3Des%26next%3Dhttps%253A%252F%252Fwww.youtube.com%252F")
        
        print("Tienes 5 minutos para:")
        print("1. Iniciar sesión con nora@chask.fun")
        print("2. Aceptar/saltar opciones de seguridad")
        print("3. Entrar a YouTube y aceptar las cookies si aparecen.")
        
        time.sleep(300)
        
        print("Cerrando navegador. Sesión guardada.")
        browser.close()

if __name__ == "__main__":
    login_youtube()
