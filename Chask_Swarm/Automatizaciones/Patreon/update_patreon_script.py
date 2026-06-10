import time
from playwright.sync_api import sync_playwright

PATREON_DIR = r"C:\Users\fnora\Desktop\PatreonBotProfile"

def update_patreon():
    print("Iniciando actualización de Patreon...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PATREON_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        page.goto("https://www.patreon.com/manage/posts", timeout=60000)
        time.sleep(8)
        
        for _ in range(2):
            try:
                menu_btn = page.locator('button[aria-label="Más acciones"], button[aria-label="More actions"]').first
                if not menu_btn.is_visible():
                    menu_btn = page.locator('button').filter(has_text="More").first
                    
                if menu_btn.is_visible():
                    menu_btn.click()
                    time.sleep(2)
                    
                    delete_btn = page.locator('li:has-text("Delete"), li:has-text("Eliminar")').first
                    if not delete_btn.is_visible():
                        delete_btn = page.locator('div[role="menuitem"]:has-text("Delete"), div[role="menuitem"]:has-text("Eliminar")').first
                    
                    if delete_btn.is_visible():
                        delete_btn.click()
                        time.sleep(2)
                        
                        confirm_btn = page.locator('button:has-text("Delete"), button:has-text("Eliminar")').nth(1)
                        if not confirm_btn.is_visible():
                             confirm_btn = page.locator('button[data-tag="modal-confirm"]')
                        if confirm_btn.is_visible():
                            confirm_btn.click()
                            time.sleep(4)
                            print("Post de Patreon eliminado exitosamente.")
            except Exception as e:
                print(f"Error al eliminar post en Patreon: {e}")
                
            time.sleep(2)
            
        page.goto("https://www.patreon.com/posts/new", timeout=60000)
        time.sleep(6)
        
        try:
            text_post_btn = page.locator('a[href*="/posts/new?post_type=text_only"], button:has-text("Text"), button:has-text("Texto")').first
            if text_post_btn.is_visible():
                text_post_btn.click()
                time.sleep(5)
                
            title = page.locator('input[placeholder="Post title"], input[placeholder="Título de la publicación"], textarea[placeholder="Post title"]').first
            if title.is_visible():
                title.fill("Descubre el ecosistema Chask Swarm")
                time.sleep(1)
                
            content = "¡Descubre la revolución en productividad con IA! Entra en el ecosistema Chask Swarm y lee toda la información en nuestro blog. 👇\n\n🌐 https://chask.fun/blog.html\n\n#charm"
            
            editor = page.locator('div[contenteditable="true"]').first
            if editor.is_visible():
                editor.click()
                page.keyboard.insert_text(content)
                time.sleep(2)
                
            publish_btn = page.locator('button:has-text("Publish now"), button:has-text("Publicar ahora")').first
            if publish_btn.is_visible():
                publish_btn.click()
                time.sleep(6)
                print("Nuevo post en Patreon publicado con éxito.")
        except Exception as e:
            print(f"Error al publicar en Patreon: {e}")
            
        browser.close()

if __name__ == "__main__":
    update_patreon()
