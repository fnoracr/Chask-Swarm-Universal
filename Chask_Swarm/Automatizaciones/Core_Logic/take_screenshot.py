import time
from playwright.sync_api import sync_playwright

USER_DATA_DIR = r"C:\Users\fnora\Desktop\TwitterBotProfile"

def main():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        print("Navegando al perfil...")
        page.goto("https://x.com/Chask_Swarm", timeout=60000)
        time.sleep(5)
        
        # Guardar captura
        page.screenshot(path=r"C:\Users\fnora\Desktop\perfil_twitter.png")
        print("Captura del perfil guardada en el escritorio (perfil_twitter.png).")
        
        context.close()

if __name__ == "__main__":
    main()
