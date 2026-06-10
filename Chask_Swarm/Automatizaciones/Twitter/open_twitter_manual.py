import time
from playwright.sync_api import sync_playwright

TWITTER_DIR = r"C:\Users\fnora\Desktop\TwitterBotProfile"

def open_twitter():
    print("Abriendo navegador para control manual...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=TWITTER_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto("https://x.com/compose/tweet", timeout=60000)
        
        print("Navegador abierto. Tienes 5 minutos para interactuar...")
        # Mantener el navegador abierto durante 5 minutos para que el usuario pueda usarlo
        time.sleep(300)
        browser.close()

if __name__ == "__main__":
    open_twitter()
