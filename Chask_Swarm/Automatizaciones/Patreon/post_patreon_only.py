import time
from playwright.sync_api import sync_playwright

PATREON_DIR = r"C:\Program Files\Chask_Swarm\Automatizaciones\PatreonBotProfile"

def post_patreon_only():
    print("Iniciando publicacion en Patreon...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PATREON_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
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
                
            content = "¡Descubre la revolución en productividad con IA! Entra en el ecosistema Chask Swarm y lee toda la información en nuestro blog oficial. 👇\n\n🌐 https://www.chask.fun/charm/Charm_Blog.php\n\n#charm #swarm #chask #chask_swarm"
            
            editor = page.locator('div[contenteditable="true"]').first
            if editor.is_visible():
                editor.click(force=True)
                page.keyboard.type(content, delay=30)
                time.sleep(4)
                
            # Trying different variations for publish button since it failed before
            publish_btn = page.locator('button:has-text("Publicar ahora"), button:has-text("Publish now"), button:has-text("Publish"), button:has-text("Publicar")').first
            if publish_btn.is_visible():
                publish_btn.click(force=True)
                time.sleep(10)
                print("Fin de publicación en Patreon.")
            else:
                print("No se encontró el botón de publicar. Intentando forzar con Javascript...")
                try:
                    # In case Patreon changed their button class/text
                    page.evaluate("Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('Publish') || el.textContent.includes('Publicar')).click()")
                    time.sleep(10)
                    print("Click forzado por JS ejecutado.")
                except Exception as e:
                    print(f"Fallo el click por JS: {e}")
        except Exception as e:
            print(f"Error publicando en Patreon: {e}")
            
        browser.close()

if __name__ == "__main__":
    post_patreon_only()
