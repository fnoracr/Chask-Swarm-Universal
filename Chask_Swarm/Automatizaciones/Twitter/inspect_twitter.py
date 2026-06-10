import time
from playwright.sync_api import sync_playwright

TWITTER_DIR = r"C:\Users\fnora\Desktop\TwitterBotProfile"

def inspect_twitter():
    print("Iniciando inspeccion de Twitter...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=TWITTER_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        text = "¡Descubre la revolución en productividad con IA! Entra en el ecosistema Chask Swarm y lee toda la información en nuestro blog. 👇\n\n🌐 www.chask.com\n\n#charm"
        page.goto("https://x.com/compose/tweet", timeout=60000)
        time.sleep(8)
        
        try:
            editor = page.locator('div[data-testid="tweetTextarea_0"]').first
            if editor.is_visible():
                editor.click(force=True)
                
                # Use type to simulate actual key presses for React state update
                page.keyboard.type(text, delay=20)
                time.sleep(4)
                
                # Tomar captura visual
                page.screenshot(path="twitter_visual_inspect.png")
                
                # Extraer HTML del modal
                dialog = page.locator('div[role="dialog"]').first
                if dialog.is_visible():
                    html_content = dialog.evaluate("el => el.innerHTML")
                    with open("twitter_modal_dom.html", "w", encoding="utf-8") as f:
                        f.write(html_content)
                    print("HTML del modal extraído a twitter_modal_dom.html")
                
                # Inspeccionar el botón
                buttons = page.locator('div[role="dialog"] button[data-testid="tweetButton"]')
                print(f"Encontrados {buttons.count()} botones de tweet en el modal.")
                
                for i in range(buttons.count()):
                    btn = buttons.nth(i)
                    disabled = btn.evaluate("el => el.disabled")
                    opacity = btn.evaluate("el => window.getComputedStyle(el).opacity")
                    print(f"Botón {i}: disabled={disabled}, opacity={opacity}")
                
            else:
                print("Textarea no visible.")
        except Exception as e:
            print(f"Error en la inspeccion: {e}")
            
        browser.close()

if __name__ == "__main__":
    inspect_twitter()
