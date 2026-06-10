import time
import re
from playwright.sync_api import sync_playwright

PATREON_DIR = r"C:\Program Files\Chask_Swarm\Automatizaciones\PatreonBotProfile"

def update_patreon_all(content=None):
    print("Iniciando actualización completa de Patreon...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PATREON_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        # 1. Borrar todas las publicaciones anteriores
        page.goto("https://www.patreon.com/Tuprofeonline992/posts", timeout=60000)
        time.sleep(8)
        
        try:
            print("Buscando posts de Patreon para borrar...")
            for _ in range(5): # Borrar hasta 5 posts
                menu_buttons = page.locator('button[aria-label="Más acciones de publicación" i]')
                if menu_buttons.count() == 0:
                    menu_buttons = page.locator('button[aria-label="More post actions" i]')
                
                if menu_buttons.count() > 0:
                    print("Borrando un post de Patreon...")
                    menu_buttons.first.click()
                    time.sleep(1)
                    
                    delete_btn = page.locator('li:has-text("Eliminar"), li:has-text("Delete")').first
                    if delete_btn.is_visible():
                        delete_btn.click()
                        time.sleep(1)
                        
                        confirm_btn = page.locator('button:has-text("Eliminar"), button:has-text("Delete")').filter(has_not=page.locator('svg')).first
                        if confirm_btn.is_visible():
                            confirm_btn.click()
                            time.sleep(4)
                    else:
                        page.keyboard.press("Escape")
                        time.sleep(1)
                        break
                else:
                    break
        except Exception as e:
            print(f"Error borrando en Patreon: {e}")
            
        # 2. Publicar nuevo post
        page.goto("https://www.patreon.com/posts/new", timeout=60000)
        time.sleep(8)
        
        try:
            text_btn = page.locator('a[href*="/posts/new?post_type=text_only" i], button:has-text("Texto"), button:has-text("Text")').first
            if text_btn.is_visible():
                text_btn.click()
                time.sleep(4)
                
            title = page.locator('input[placeholder*="Título" i], input[placeholder*="Title" i]').first
            if title.is_visible():
                title.fill("Descubre el ecosistema Chask Swarm")
                time.sleep(1)
                
            if content is None:
                content = "¡Descubre la revolución en productividad con IA! Entra en el ecosistema Chask Swarm.\n\nSíguenos en todas nuestras plataformas:\n🌐 Blog: https://www.chask.fun/charm/Charm_Blog.php\n💎 Patreon: https://www.patreon.com/Tuprofeonline992\n🐦 X: https://x.com/nora_chask\n📸 Insta: https://www.instagram.com/nora.chask.swarm\n\n#charm #swarm #chask"
            
            editor = page.locator('div[contenteditable="true"]').first
            if editor.is_visible():
                editor.click()
                page.keyboard.type(content, delay=30)
                time.sleep(2)
                
            publish_btn = page.locator('button, div[role="button"]').filter(has_text=re.compile("^(Publicar ahora|Publish now|Publish|Publicar|Post)$", re.IGNORECASE)).first
            if publish_btn.is_visible():
                publish_btn.click(force=True)
                time.sleep(10)
                print("Fin de publicación en Patreon.")
            else:
                print("No se encontró el botón de publicar. Intentando forzar con Javascript...")
                try:
                    # In case Patreon changed their button class/text
                    page.evaluate("Array.from(document.querySelectorAll('button, div[role=\"button\"]')).find(el => el.textContent.trim().match(/^(Publicar ahora|Publish now|Publish|Publicar|Post)$/i)).click()")
                    time.sleep(10)
                    print("Click forzado por JS ejecutado.")
                except Exception as e:
                    print(f"Fallo el click por JS: {e}")
        except Exception as e:
            print(f"Error publicando en Patreon: {e}")
            
        browser.close()

if __name__ == "__main__":
    import sys
    custom_content = sys.argv[1] if len(sys.argv) > 1 else None
    update_patreon_all(content=custom_content)
