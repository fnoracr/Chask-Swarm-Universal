from playwright.sync_api import sync_playwright

def open_login():
    user_data_dir = r"C:\Users\fnora\Desktop\PatreonBotProfile"
    print("Abriendo navegador del bot...")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://www.patreon.com/login")
        print("Por favor, inicia sesión en Patreon en la ventana que se acaba de abrir.")
        print("Cierra la ventana de Chrome cuando hayas terminado de iniciar sesión.")
        
        # Esperar hasta que el usuario cierre el navegador
        try:
            page.wait_for_event("close", timeout=0) # Espera infinita hasta que se cierre la pestaña
        except Exception:
            pass
        print("Navegador cerrado. Perfil guardado.")

if __name__ == "__main__":
    open_login()
