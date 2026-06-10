import time
from playwright.sync_api import sync_playwright

TWITTER_DIR = r"C:\Program Files\Chask_Swarm\Automatizaciones\TwitterBotProfile"

def final_twitter_post():
    print("Iniciando publicacion en Twitter...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=TWITTER_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        text = "¡Descubre la revolución en productividad con IA! Entra en el ecosistema Chask Swarm y lee toda la información en nuestro blog. 👇\n\n🌐 www.chask.com\n\n#charm"
        
        # Eliminar los tweets previos que tengan la imagen antigua si los hubiera (opcional, saltamos para ir directo al post)
        
        page.goto("https://x.com/compose/tweet", timeout=60000)
        time.sleep(8)
        
        try:
            editor = page.locator('div[data-testid="tweetTextarea_0"]').first
            if editor.is_visible():
                editor.click(force=True)
                
                # Simular tipeo real para que React active el boton
                page.keyboard.type(text, delay=30)
                time.sleep(5)
                
                btn = page.locator('div[role="dialog"] button[data-testid="tweetButton"]').first
                
                print("Intentando publicar mediante click nativo...")
                try:
                    # Intento 1: dispatchEvent
                    btn.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}))")
                    time.sleep(2)
                except Exception as e:
                    print(f"Error en dispatchEvent: {e}")
                
                print("Intentando publicar mediante atajo de teclado (Ctrl+Enter)...")
                # Intento 2: Ctrl+Enter (Atajo global en X para tuitear)
                page.keyboard.press("Control+Enter")
                time.sleep(2)
                
                print("Intentando publicar mediante click directo en el DOM...")
                try:
                    # Intento 3: .click() en JS
                    btn.evaluate("el => el.click()")
                except:
                    pass
                
                time.sleep(10)
                print("Fin de los intentos de publicación.")
                page.screenshot(path="twitter_final_result.png")
            else:
                print("Textarea no visible.")
        except Exception as e:
            print(f"Error general en la publicacion: {e}")
            
        browser.close()

if __name__ == "__main__":
    final_twitter_post()
