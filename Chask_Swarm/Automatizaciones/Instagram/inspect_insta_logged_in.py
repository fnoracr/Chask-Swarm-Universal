import time
from playwright.sync_api import sync_playwright

INSTA_DIR = r"C:\Users\fnora\Desktop\InstaBotProfile"

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=INSTA_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        print("Navegando a Instagram...")
        page.goto("https://www.instagram.com/", timeout=60000)
        time.sleep(10)
        
        print("Haciendo click en Crear...")
        create_btn = page.locator('svg[aria-label="Nueva publicación"], svg[aria-label="New post"]').locator("..").locator("..")
        if create_btn.is_visible():
            create_btn.first.click()
        else:
            page.locator('span:has-text("Crear"), span:has-text("Create")').first.click()
            
        time.sleep(5)
        
        try:
            post_menu = page.locator('span:has-text("Publicación"), span:has-text("Post")').first
            if post_menu.is_visible():
                post_menu.click()
                time.sleep(3)
        except: pass
        
        print("Extrayendo DOM del modal...")
        buttons = page.locator('button').all_text_contents()
        divs = page.locator('div[role="button"]').all_text_contents()
        
        with open(r"C:\Users\fnora\Desktop\insta_buttons.txt", "w", encoding="utf-8") as f:
            f.write("BUTTONS:\n")
            for b in buttons: f.write(b + "\n")
            f.write("\nDIVS AS BUTTONS:\n")
            for d in divs: f.write(d + "\n")
            
        print("Guardado en insta_buttons.txt")
        browser.close()

if __name__ == "__main__":
    inspect()
