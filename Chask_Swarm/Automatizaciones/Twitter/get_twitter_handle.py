import time
from playwright.sync_api import sync_playwright

USER_DATA_DIR = r"C:\Users\fnora\Desktop\TwitterBotProfile"

def main():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",
            headless=True
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://x.com/home", timeout=60000)
        time.sleep(5)
        
        profile_link = page.locator('a[data-testid="AppTabBar_Profile_Link"]')
        if profile_link.is_visible():
            href = profile_link.get_attribute("href")
            print(f"HANDLE_ENCONTRADO: {href}")
        else:
            print("No se encontró el enlace al perfil.")
        
        context.close()

if __name__ == "__main__":
    main()
