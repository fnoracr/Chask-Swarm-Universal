import time
from playwright.sync_api import sync_playwright

TWITTER_DIR = r"C:\Users\fnora\Desktop\TwitterBotProfile"

def fix_twitter():
    print("Iniciando fix de Twitter...")
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
        
        try:
            editor = page.locator('div[data-testid="tweetTextarea_0"]').first
            if editor.is_visible():
                editor.click(force=True)
                page.keyboard.insert_text(text)
                time.sleep(4)
                
                # Buscar el botón de publicar específicamente dentro del modal de composición
                btn = page.locator('div[role="dialog"] button[data-testid="tweetButton"]').first
                if not btn.is_visible():
                     # Fallback
                     btn = page.locator('button:has-text("Post"), button:has-text("Twittear"), button:has-text("Postear")').filter(has_not=page.locator('svg')).last
                     
                if btn.is_visible():
                    print("Boton de Post visible en el dialogo. Haciendo click...")
                    btn.click(force=True)
                    time.sleep(10)
                    print("Click realizado y espera terminada.")
                else:
                    print("Boton de tweet no visible en el dialogo.")
            else:
                print("Textarea no visible.")
        except Exception as e:
            print(f"Error al publicar tweet: {e}")
            
        browser.close()

if __name__ == "__main__":
    fix_twitter()
