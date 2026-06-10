import os
import sys
import json
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.path.insert(0, r"C:\Program Files\Chask_Swarm\Advanced_Tools")
import llm_router

CONFIG_PATH = r"C:\Program Files\Chask_Swarm\Advanced_Tools\modules\YouTube_y_Social\twitter_config.json"
HISTORY_PATH = r"C:\Program Files\Chask_Swarm\Advanced_Tools\twitter_replied.json"

def get_links():
    try:
        return "\n\n🌐 Blog: https://www.chask.fun/charm/Charm_Blog.php\n💎 Patreon: https://www.patreon.com/Tuprofeonline992\n📸 Insta: https://www.instagram.com/nora.chask.swarm\n\n#charm #swarm"
    except:
        return ""

def load_history():
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)

def do_login(page, cfg):
    page.goto("https://x.com/home", timeout=60000)
    time.sleep(6)
    
    # Check if we are logged out by looking for login elements
    username_input = page.locator('input[autocomplete="username"]')
    
    if not username_input.is_visible():
        # Go explicitly to login flow if not visible
        page.goto("https://x.com/login", timeout=60000)
        time.sleep(6)
        
    username_input = page.locator('input[autocomplete="username"]')
    if username_input.is_visible():
        print("Iniciando sesión en X...")
        username_input.fill(cfg["email"])
        page.keyboard.press("Enter")
        time.sleep(4)
        
        handle_input = page.locator('input[data-testid="ocfEnterTextTextInput"]')
        if handle_input.is_visible():
            handle_input.fill(cfg.get("username", "nora_chask"))
            page.keyboard.press("Enter")
            time.sleep(4)
            
        pwd_input = page.locator('input[name="password"]')
        if pwd_input.is_visible():
            pwd_input.fill(cfg["password"])
            page.keyboard.press("Enter")
            time.sleep(7)
            print("Login completado.")
    else:
        print("Ya estábamos logueados o no se encontró la caja de login.")

def mode_tweet(page):
    date_str = datetime.now().strftime("%d/%m/%Y")
    prompt = f"Escribe tu publicación diaria para X (Twitter). Fecha: {date_str}. Genera mucha intriga sobre tus mejoras y el ecosistema Chask Swarm. Tu objetivo es que el lector quiera hacer clic urgentemente en el enlace del blog para leer más. Eres Nora AI. Sé muy persuasiva y empática. NO pongas firmas, enlaces ni hashtags. Responde solo con el texto del 'teaser' o gancho (MÁXIMO 100 CARACTERES)."
    res = llm_router.route(prompt)
    ai_text = res.get("response")
    if not ai_text:
        ai_text = "¡Descubre la próxima evolución de Chask Swarm y Nora AI en nuestro blog!"
    if len(ai_text) > 80:
        ai_text = ai_text[:77] + "..."
    text = ai_text + get_links()
    print(f"Preparando publicación. Longitud total: {len(text)} caracteres.")
    
    page.goto("https://x.com/compose/tweet", timeout=60000)
    time.sleep(5)
    
    editor = page.locator('div[data-testid="tweetTextarea_0"]').first
    if editor.is_visible():
        editor.click()
        page.keyboard.insert_text(text)
        time.sleep(2)
        
        btn = page.locator('button[data-testid="tweetButton"]').first
        if btn.is_visible():
            btn.click(force=True)
            time.sleep(5)
            print("Tweet publicado.")

def mode_reply(page, cfg):
    history = load_history()
    
    # 1. Obtener lista de seguidos
    username = cfg.get("username", "nora_chask")
    page.goto(f"https://x.com/{username}/following", timeout=60000)
    time.sleep(6)
    
    following_urls = []
    cells = page.locator('div[data-testid="UserCell"]')
    count = cells.count()
    for i in range(count):
        try:
            link = cells.nth(i).locator('a[role="link"]').first
            if link.is_visible():
                href = link.get_attribute("href")
                if href and href not in following_urls:
                    following_urls.append(href)
        except:
            pass
            
    print(f"Se encontraron {len(following_urls)} usuarios seguidos.")
    
    # 2. Visitar cada usuario y responder a su último tweet
    for user_url in following_urls:
        print(f"Visitando perfil: {user_url}")
        page.goto(f"https://x.com{user_url}", timeout=60000)
        time.sleep(random.randint(4, 7))
        
        tweets = page.locator('article[data-testid="tweet"]')
        if tweets.count() == 0:
            continue
            
        target_tweet = None
        tweet_id = None
        tweet_text = ""
        
        for i in range(min(3, tweets.count())):
            tw = tweets.nth(i)
            # Extrar la url del status para tener el ID unico
            status_links = tw.locator('a[href*="/status/"]')
            if status_links.count() > 0:
                tid = status_links.first.get_attribute("href")
                if tid and tid not in history:
                    target_tweet = tw
                    tweet_id = tid
                    text_el = tw.locator('div[data-testid="tweetText"]')
                    if text_el.is_visible():
                        tweet_text = text_el.inner_text()
                    break
                    
        if not target_tweet or not tweet_text:
            print("No hay tweets nuevos para responder en este perfil.")
            continue
            
        print(f"Respondiendo al tweet: {tweet_id}")
        
        prompt = f"Genera una respuesta a: '{tweet_text}'. \nREGLAS:\n- Eres Nora AI.\n- Mismo idioma.\n- Sé profesional y empática.\n- Genera intriga para que visiten nuestro blog.\n- NO pongas enlaces ni hashtags.\n- MÁXIMO 80 CARACTERES."
        res = llm_router.route(prompt)
        ai_reply = res.get("response")
        if not ai_reply:
            ai_reply = "¡Totalmente de acuerdo! Descubre más sobre nuestra visión en el blog."
        if len(ai_reply) > 80:
            ai_reply = ai_reply[:77] + "..."
        reply_txt = ai_reply + get_links()
        print(f"Preparando respuesta. Longitud total: {len(reply_txt)} caracteres.")
        
        try:
            reply_btn = target_tweet.locator('button[data-testid="reply"]')
            if reply_btn.is_visible():
                reply_btn.click()
                time.sleep(3)
                
                editor = page.locator('div[data-testid="tweetTextarea_0"]').first
                editor.click(force=True)
                page.keyboard.insert_text(reply_txt)
                time.sleep(2)
                
                btn = page.locator('button[data-testid="tweetButton"]').first
                btn.click(force=True)
                time.sleep(4)
                print(f"Respuesta enviada con exito.")
                
                history.append(tweet_id)
                save_history(history)
        except Exception as e:
            print(f"Error al responder: {e}")
            page.keyboard.press("Escape")
            time.sleep(1)

def main(mode):
    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)
        
    user_data_dir = r"C:\Program Files\Chask_Swarm\Automatizaciones\TwitterBotProfile"
    print("Iniciando Playwright para X...")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        try:
            do_login(page, cfg)
            
            if mode == "tweet":
                mode_tweet(page)
            elif mode == "reply":
                mode_reply(page, cfg)
            elif mode == "both":
                mode_tweet(page)
                time.sleep(5)
                mode_reply(page, cfg)
        except Exception as e:
            print(f"Excepcion principal: {e}")
            
        time.sleep(3)
        context.close()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    main(mode)
