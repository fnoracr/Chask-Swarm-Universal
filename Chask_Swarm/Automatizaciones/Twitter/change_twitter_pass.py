import os
import sys
import time
from playwright.sync_api import sync_playwright
import json

CONFIG_PATH = r"C:\Program Files\Chask_Swarm\Advanced_Tools\modules\YouTube_y_Social\twitter_config.json"
USER_DATA_DIR = r"C:\Users\fnora\Desktop\TwitterBotProfile"

OLD_PASS = "AQUI_VA_TU_FTP_PASS"
NEW_PASS = "12@N0r4Z0e?*"
EMAIL = "nora@chask.fun"
USERNAME = "nora_chask"

def do_login(page):
    page.goto("https://x.com/home", timeout=60000)
    time.sleep(5)
    
    if page.locator('a[href="/login"]').is_visible() or page.url.endswith("login") or page.url.endswith("signup"):
        page.goto("https://x.com/login", timeout=60000)
        time.sleep(5)
        
        if page.locator('input[autocomplete="username"]').is_visible():
            page.fill('input[autocomplete="username"]', EMAIL)
            page.keyboard.press("Enter")
            time.sleep(3)
            
            handle_input = page.locator('input[data-testid="ocfEnterTextTextInput"]')
            if handle_input.is_visible():
                handle_input.fill(USERNAME)
                page.keyboard.press("Enter")
                time.sleep(3)
                
            pwd_input = page.locator('input[name="password"]')
            if pwd_input.is_visible():
                pwd_input.fill(OLD_PASS)
                page.keyboard.press("Enter")
                time.sleep(5)

def main():
    print("Iniciando Playwright para cambiar contraseña...")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        try:
            print("Verificando sesión...")
            do_login(page)
            
            print("Navegando a configuración de contraseña...")
            page.goto("https://x.com/settings/password", timeout=60000)
            time.sleep(8)
            
            curr_input = page.locator('input[name="current_password"]')
            if curr_input.is_visible():
                print("Rellenando contraseña actual...")
                curr_input.fill(OLD_PASS)
                time.sleep(1)
                
                print("Rellenando nueva contraseña...")
                page.locator('input[name="new_password"]').fill(NEW_PASS)
                time.sleep(1)
                
                print("Confirmando nueva contraseña...")
                page.locator('input[name="password_confirmation"]').fill(NEW_PASS)
                time.sleep(1)
                
                print("Guardando cambios...")
                save_btn = page.locator('button[data-testid="settingsDetailSave"]')
                if save_btn.is_visible():
                    save_btn.click()
                    print("Boton de guardar clickeado.")
                    time.sleep(10)
                    
                    try:
                        with open(CONFIG_PATH, "r") as f:
                            cfg = json.load(f)
                        cfg["password"] = NEW_PASS
                        with open(CONFIG_PATH, "w") as f:
                            json.dump(cfg, f, indent=2)
                        print("Archivo twitter_config.json actualizado con la nueva contraseña.")
                    except Exception as e:
                        print(f"Error actualizando JSON: {e}")
                else:
                    print("No se encontró el botón de guardar.")
            else:
                print("No se encontró el campo de contraseña actual. Posiblemente estemos bloqueados en un CAPTCHA.")
                
        except Exception as e:
            print(f"Excepción: {e}")
            
        print("Proceso terminado. Cerrando navegador en 10 segundos...")
        time.sleep(10)
        context.close()

if __name__ == "__main__":
    main()
