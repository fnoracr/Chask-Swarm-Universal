from playwright.sync_api import sync_playwright
import time

def clear_popups(page):
    page.keyboard.press("Escape")
    time.sleep(1)

def go_to_feed():
    user_data_dir = r"C:\Users\fnora\Desktop\PatreonBotProfile"
    print("Yendo al feed público...")
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel="chrome",
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            page = context.pages[0] if context.pages else context.new_page()
            
            page.goto("https://www.patreon.com/c/Tuprofeonline992", timeout=60000)
            time.sleep(5)
            clear_popups(page)
            
            # Scroll down to see posts
            page.evaluate("window.scrollBy(0, 1500)")
            time.sleep(3)
            page.screenshot(path=r"C:\Users\fnora\Desktop\patreon_feed2.png")
            print("Feed screenshot tomada.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    go_to_feed()
