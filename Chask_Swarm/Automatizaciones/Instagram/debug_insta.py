import time
import os
import random
from playwright.sync_api import sync_playwright

INSTA_DIR = r"C:\Users\fnora\Desktop\InstaBotProfile"

def debug_instagram():
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=INSTA_DIR,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        page.goto("https://www.instagram.com/", timeout=60000)
        time.sleep(10)
        
        # Take screenshot of homepage
        page.screenshot(path=r"C:\Users\fnora\Desktop\insta_debug_1.png")
        
        create_btn = page.locator('svg[aria-label="Nueva publicación"], svg[aria-label="New post"]').locator("..").locator("..")
        if not create_btn.is_visible():
            create_btn = page.locator('a[href="#"]:has(svg[aria-label="Nueva publicación"]), a[href="#"]:has(svg[aria-label="New post"])')
        
        if create_btn.is_visible():
            create_btn.first.click()
        else:
            page.locator('span:has-text("Crear"), span:has-text("Create")').first.click()
            
        time.sleep(3)
        page.screenshot(path=r"C:\Users\fnora\Desktop\insta_debug_2.png")
        
        try:
            post_menu = page.locator('span:has-text("Publicación"), span:has-text("Post")').first
            if post_menu.is_visible():
                post_menu.click()
                time.sleep(3)
        except: pass
        
        page.screenshot(path=r"C:\Users\fnora\Desktop\insta_debug_3.png")
        
        browser.close()

if __name__ == "__main__":
    debug_instagram()
