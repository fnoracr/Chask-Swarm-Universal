from playwright.sync_api import sync_playwright
import time
import os

INSTA_DIR = r"C:\Program Files\Chask_Swarm\Automatizaciones\InstaBotProfile"

def debug():
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=INSTA_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto("https://www.instagram.com/", timeout=60000)
        time.sleep(8)
        
        # Click on something that looks like the "Create" button
        try:
            btn = page.locator('svg[aria-label*="Nueva publicaci"], svg[aria-label*="New post"], svg[aria-label="Create"], svg[aria-label="Crear"]').first
            btn.click(force=True)
            time.sleep(5)
            
            # Save HTML
            with open(r"C:\Program Files\Chask_Swarm\Automatizaciones\insta_dom.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("DOM saved.")
        except Exception as e:
            print(f"Error: {e}")
            with open(r"C:\Program Files\Chask_Swarm\Automatizaciones\insta_dom_error.html", "w", encoding="utf-8") as f:
                f.write(page.content())
                
        browser.close()

if __name__ == "__main__":
    debug()
