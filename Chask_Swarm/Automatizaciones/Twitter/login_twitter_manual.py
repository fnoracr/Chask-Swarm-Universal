import time
from playwright.sync_api import sync_playwright

USER_DATA_DIR = r"C:\Users\fnora\Desktop\TwitterBotProfile"

def main():
    print("Por favor, inicia sesión manualmente en la ventana que se acaba de abrir.")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://x.com/login")
        
        print("Esperando a que inicies sesión. Cierra la ventana del navegador cuando veas tu muro (Timeline) o espera a que detectemos el login.")
        try:
            # Esperar a estar logueado (url cambia a home) o a que se cierre la ventana
            page.wait_for_url("https://x.com/home", timeout=0)
            print("Login detectado (redirección a /home). Esperando 10 segundos por seguridad antes de cerrar y guardar...")
            time.sleep(10)
        except Exception as e:
            print("El navegador se cerró o algo interrumpió la espera.")
            
        print("Guardando perfil y finalizando.")
        context.close()

if __name__ == "__main__":
    main()
