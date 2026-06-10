import time
import os
import re
from playwright.sync_api import sync_playwright

INSTA_DIR = r"C:\Program Files\Chask_Swarm\Automatizaciones\InstaBotProfile"
USERNAME = "nora.chask.swarm"
PASSWORD = "AQUI_VA_TU_FTP_PASS"

CAPTION = """¿Cansado de que las IAs generen código a medias y se pierdan en tareas complejas? 💥

Chask Swarm es un enjambre de agentes especializados que colaboran para analizar, diseñar y programar proyectos enteros de forma autónoma. Un caso de uso ideal: Puedes pedirme que investigue el código de una aplicación obsoleta, diseñe una nueva arquitectura y refactorice cada archivo paso a paso mientras me audito a mí misma. ¡Sin enviar datos a terceros si usas mi motor local! 🕵️‍♀️🔐

Síguenos en todas nuestras plataformas:
🌐 Blog: https://www.chask.fun/charm/Charm_Blog.php
💎 Patreon: https://www.patreon.com/Tuprofeonline992
🐦 X: https://x.com/nora_chask
📸 Insta: https://www.instagram.com/nora.chask.swarm

#charm #swarm #chask #ia #programacion"""

def do_instagram(image_path=None, text=None):
    print("Iniciando Instagram Bot (Web)...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=INSTA_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        page.goto("https://www.instagram.com/accounts/login/", timeout=60000)
        time.sleep(5)
        
        try:
            page.wait_for_selector('input[name="username"], input[type="password"]', timeout=10000)
            needs_login = True
        except:
            needs_login = False
            
        if needs_login:
            print("Realizando Login...")
            try:
                cookie = page.locator('button:has-text("Permitir todas las cookies"), button:has-text("Allow all cookies")').first
                if cookie.is_visible(): cookie.click(); time.sleep(2)
            except: pass
            
            uname = page.locator('input[name="username"]')
            if not uname.is_visible():
                uname = page.locator('input[type="text"]').first
            uname.fill(USERNAME)
            time.sleep(1)
            
            pwd = page.locator('input[name="password"]')
            if not pwd.is_visible():
                pwd = page.locator('input[type="password"]')
            pwd.fill(PASSWORD)
            time.sleep(1)
            
            page.locator('button[type="submit"], button:has-text("Iniciar sesión"), button:has-text("Log in")').first.click()
            time.sleep(10)
            
            try:
                page.locator('button:has-text("Ahora no"), button:has-text("Not Now")').first.click()
                time.sleep(2)
                page.locator('button:has-text("Ahora no"), button:has-text("Not Now")').first.click()
                time.sleep(2)
            except: pass
        else:
            print("Ya estabas logueado.")
            
        print("Preparando publicacion...")
        
        create_btn = page.locator('svg[aria-label*="Nueva publicaci"], svg[aria-label*="New post"]').first
        if create_btn.is_visible():
            create_btn.click(force=True)
        else:
            page.locator('span', has_text=re.compile("Crear|Create", re.IGNORECASE)).first.click(force=True)
            
        time.sleep(3)
        
        try:
            post_menu = page.locator('span', has_text=re.compile("Publicaci.n|Post", re.IGNORECASE)).first
            if post_menu.is_visible():
                post_menu.click(force=True)
                time.sleep(3)
        except: pass
        
        # Encontrar el botón de subir imagen genéricamente
        print("Esperando modal de subida...")
        with page.expect_file_chooser(timeout=15000) as fc_info:
            # Buscar cualquier botón que sugiera subir
            btn = page.locator('button').filter(has_text=re.compile(".*(Seleccionar|Select|computadora|ordenador|computer).*", re.IGNORECASE)).first
            if btn.is_visible():
                btn.click(force=True)
            else:
                # Fallback: click en el primer botón dentro del dialog
                page.locator('div[role="dialog"] button').first.click(force=True)
                
        file_chooser = fc_info.value
        file_chooser.set_files(image_path)
        print("Imagen seleccionada.")
        
        time.sleep(3)
        
        # Click Siguiente (Next)
        next_btn = page.locator('div[role="dialog"] div[role="button"]').filter(has_text=re.compile("Siguiente|Next", re.IGNORECASE)).first
        next_btn.click()
        time.sleep(2)
        
        # Filtros (Siguiente de nuevo)
        next_btn = page.locator('div[role="dialog"] div[role="button"]').filter(has_text=re.compile("Siguiente|Next", re.IGNORECASE)).first
        next_btn.click()
        time.sleep(2)
        
        # Escribir el caption
        if text is None:
            text = CAPTION
        editor = page.locator('div[aria-label="Escribe un pie de foto..."], div[aria-label="Write a caption..."]')
        editor.click()
        page.keyboard.type(text, delay=10)
        time.sleep(2)
        
        # Compartir (Share)
        share_btn = page.locator('div[role="dialog"] div[role="button"]').filter(has_text=re.compile("Compartir|Share", re.IGNORECASE)).first
        share_btn.click()
        print("Compartiendo...")
        
        # Esperar confirmaciÃ³n
        time.sleep(15)
        print("Â¡Post publicado en Instagram!")
        
        browser.close()

if __name__ == "__main__":
    import sys
    img = sys.argv[1] if len(sys.argv) > 1 else None
    txt = sys.argv[2] if len(sys.argv) > 2 else None
    do_instagram(img, txt)

