import time
from playwright.sync_api import sync_playwright

TWITTER_DIR = r"C:\Users\fnora\Desktop\TwitterBotProfile"

def debug_twitter():
    print("Iniciando debug de Twitter...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=TWITTER_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        # Publicar nuevo tweet
        text = "¡Descubre la revolución en productividad con IA! Entra en el ecosistema Chask Swarm y lee toda la información en nuestro blog. 👇\n\n🌐 www.chask.com\n\n#charm"
        page.goto("https://x.com/compose/tweet", timeout=60000)
        time.sleep(8)
        
        page.screenshot(path="twitter_debug_1_compose.png")
        
        try:
            editor = page.locator('div[data-testid="tweetTextarea_0"]').first
            if editor.is_visible():
                editor.click(force=True)
                page.keyboard.insert_text(text)
                time.sleep(3)
                
                page.screenshot(path="twitter_debug_2_filled.png")
                
                btn = page.locator('button[data-testid="tweetButton"]').first
                if btn.is_visible():
                    print("Boton visible. Haciendo click...")
                    btn.click(force=True)
                    time.sleep(6)
                    
                    page.screenshot(path="twitter_debug_3_after_click.png")
                    print("Intento de publicacion finalizado.")
                else:
                    print("Boton de tweet no visible.")
            else:
                print("Textarea no visible.")
        except Exception as e:
            print(f"Error al publicar tweet: {e}")
            
        browser.close()

if __name__ == "__main__":
    debug_twitter()
