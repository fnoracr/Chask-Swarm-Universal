import time
from playwright.sync_api import sync_playwright

TWITTER_DIR = r"C:\Users\fnora\Desktop\TwitterBotProfile"

def update_twitter():
    print("Iniciando actualización de Twitter...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=TWITTER_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        page.goto("https://x.com/Chask_Swarm", timeout=60000)
        time.sleep(8)
        
        for _ in range(2):
            try:
                caret = page.locator('button[data-testid="caret"]').first
                if caret.is_visible():
                    caret.click(force=True)
                    time.sleep(2)
                    
                    menu_items = page.locator('div[data-testid="Dropdown"] [role="menuitem"]')
                    for i in range(menu_items.count()):
                        item = menu_items.nth(i)
                        text = item.inner_text().lower()
                        if "delete" in text or "eliminar" in text:
                            item.click(force=True)
                            time.sleep(2)
                            
                            confirm_btn = page.locator('button[data-testid="confirmationSheetConfirm"]')
                            if confirm_btn.is_visible():
                                confirm_btn.click(force=True)
                                time.sleep(4)
                                print("Tweet eliminado exitosamente.")
                            break
            except Exception as e:
                print(f"Error al eliminar tweet: {e}")
                
            time.sleep(2)

        text = "¡Descubre la revolución en productividad con IA! Entra en el ecosistema Chask Swarm y lee toda la información en nuestro blog. 👇\n\n🌐 www.chask.com\n\n#charm"
        page.goto("https://x.com/compose/tweet", timeout=60000)
        time.sleep(6)
        
        try:
            editor = page.locator('div[data-testid="tweetTextarea_0"]').first
            if editor.is_visible():
                editor.click(force=True)
                page.keyboard.insert_text(text)
                time.sleep(2)
                
                btn = page.locator('button[data-testid="tweetButton"]').first
                if btn.is_visible():
                    btn.click(force=True)
                    time.sleep(5)
                    print("Nuevo tweet publicado con éxito.")
        except Exception as e:
            print(f"Error al publicar tweet: {e}")
            
        browser.close()

if __name__ == "__main__":
    update_twitter()
