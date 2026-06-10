import time
from playwright.sync_api import sync_playwright

TWITTER_DIR = r"C:\Program Files\Chask_Swarm\Automatizaciones\TwitterBotProfile"

def update_twitter_all(text=None):
    print("Iniciando actualización completa de Twitter...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=TWITTER_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        # 1. Borrar todas las publicaciones anteriores
        page.goto("https://x.com/Chask_Swarm", timeout=60000)
        time.sleep(5)
        
        try:
            print("Buscando posts para borrar...")
            for _ in range(10): # Borrar hasta 10 posts
                menu_buttons = page.locator('button[aria-label="Más" i]')
                if menu_buttons.count() == 0:
                    menu_buttons = page.locator('button[aria-label="More" i]')
                
                if menu_buttons.count() > 0:
                    print("Borrando un post...")
                    menu_buttons.first.click()
                    time.sleep(1)
                    
                    delete_btn = page.locator('div[role="menuitem"]:has-text("Eliminar"), div[role="menuitem"]:has-text("Delete")').first
                    if delete_btn.is_visible():
                        delete_btn.click()
                        time.sleep(1)
                        
                        confirm_btn = page.locator('button[data-testid="confirmationSheetConfirm"]').first
                        if confirm_btn.is_visible():
                            confirm_btn.click()
                            time.sleep(2)
                    else:
                        # Cerrar el menu pulsando escape
                        page.keyboard.press("Escape")
                        time.sleep(1)
                        # No es tuyo o no se puede borrar, hacemos break para evitar loop infinito
                        break
                else:
                    break
        except Exception as e:
            print(f"Error borrando tweets: {e}")
            
        # 2. Publicar nuevo tweet
        if text is None:
            text = "¡Descubre la revolución en productividad con IA! Entra en el ecosistema Chask Swarm y lee toda la información en nuestro blog. 👇\n\n🌐 https://www.chask.fun/charm/Charm_Blog.php\n\n#charm #swarm #chask #chask_swarm"
        
        page.goto("https://x.com/compose/tweet", timeout=60000)
        time.sleep(8)
        
        try:
            editor = page.locator('div[data-testid="tweetTextarea_0"]').first
            if editor.is_visible():
                editor.click(force=True)
                page.keyboard.type(text, delay=30)
                time.sleep(5)
                
                btn = page.locator('div[role="dialog"] button[data-testid="tweetButton"]').first
                
                print("Intentando publicar mediante click nativo...")
                try:
                    btn.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}))")
                    time.sleep(2)
                except:
                    pass
                
                print("Intentando publicar mediante atajo de teclado (Ctrl+Enter)...")
                page.keyboard.press("Control+Enter")
                time.sleep(2)
                
                try:
                    btn.evaluate("el => el.click()")
                except:
                    pass
                
                time.sleep(10)
                print("Fin de publicación en Twitter.")
            else:
                print("Textarea no visible en Twitter.")
        except Exception as e:
            print(f"Error publicando en Twitter: {e}")
            
        browser.close()

if __name__ == "__main__":
    import sys
    custom_text = sys.argv[1] if len(sys.argv) > 1 else None
    update_twitter_all(text=custom_text)
