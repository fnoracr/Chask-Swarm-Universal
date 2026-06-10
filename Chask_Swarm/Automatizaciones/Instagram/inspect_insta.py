import time
from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("Navegando al login...")
        page.goto("https://www.instagram.com/?flo=true")
        
        # Aceptar cookies
        try:
            page.locator('button:has-text("Permitir todas las cookies"), button:has-text("Allow all cookies")').first.click(timeout=5000)
        except: pass
        
        # Login
        page.locator('input[name="username"]').fill("nora@chask.fun")
        page.locator('input[name="password"]').fill("AQUI_VA_TU_FTP_PASS")
        page.locator('button[type="submit"]').click()
        
        print("Esperando a cargar inicio...")
        page.wait_for_selector('svg[aria-label="Nueva publicación"], svg[aria-label="New post"]', timeout=20000)
        time.sleep(5)
        
        print("Haciendo click en Crear...")
        create_btn = page.locator('svg[aria-label="Nueva publicación"], svg[aria-label="New post"]').locator("..").locator("..")
        if create_btn.is_visible():
            create_btn.first.click()
        else:
            page.locator('span:has-text("Crear"), span:has-text("Create")').first.click()
            
        time.sleep(5)
        
        # Guardar todo el texto de los botones del modal
        print("Extrayendo botones del modal...")
        buttons = page.locator('button').all_text_contents()
        with open(r"C:\Users\fnora\Desktop\insta_buttons.txt", "w", encoding="utf-8") as f:
            for b in buttons:
                f.write(b + "\n")
        
        print("Guardado en insta_buttons.txt")
        browser.close()

if __name__ == "__main__":
    inspect()
