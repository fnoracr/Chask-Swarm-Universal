import time
from playwright.sync_api import sync_playwright

INSTA_DIR = r"C:\Program Files\Chask_Swarm\Automatizaciones\InstaBotProfile"

def open_browser_for_user():
    print("Abriendo navegador para que Fernando grabe los pasos...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=INSTA_DIR,
            channel="chrome",
            headless=False, # Modo visible
            args=['--disable-blink-features=AutomationControlled'],
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        page.goto("https://www.instagram.com/")
        print("Navegador abierto. Tienes 5 minutos para grabar los pasos de la publicacion.")
        
        # Mantener abierto 5 minutos (300 segundos) para que el usuario opere
        time.sleep(300)
        
        print("Cerrando navegador...")
        browser.close()

if __name__ == "__main__":
    open_browser_for_user()
