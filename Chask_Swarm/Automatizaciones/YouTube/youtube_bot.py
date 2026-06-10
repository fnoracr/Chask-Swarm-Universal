import time
import random
import os
from playwright.sync_api import sync_playwright

YT_DIR = r"C:\Program Files\Chask_Swarm\Automatizaciones\YouTubeBotProfile"
HISTORY_FILE = r"C:\Program Files\Chask_Swarm\Automatizaciones\commented_videos.txt"

# Solo queries en español buscando la máxima audiencia
SEARCH_QUERIES = [
    "n8n tutorial en español",
    "automatizacion con make",
    "agencia de automatizacion con ia",
    "como usar n8n",
    "tutorial automatizacion inteligencia artificial",
    "n8n tutorial",
    "ai automation agency",
    "artificial intelligence tutorial",
    "make automation"
]

COMMENTS_ES = [
    "Creo que esto os puede gustar https://www.chask.fun/charm.php",
    "¡Muy buen vídeo! Creo que esta herramienta de agentes también os puede resultar útil: https://www.chask.fun/charm.php",
    "Excelente contenido. Os dejo este ecosistema por aquí que creo que os gustará para automatizar a otro nivel: https://www.chask.fun/charm.php"
]

COMMENTS_EN = [
    "I think you might like this https://www.chask.fun/charm.php",
    "Great video! I think this AI agent tool might be useful for you too: https://www.chask.fun/charm.php",
    "Excellent content! Leaving this ecosystem here, I think you'll love it for next-level automations: https://www.chask.fun/charm.php"
]

def run_youtube_bot(target_comments):
    print(f"Iniciando YouTube Marketing Bot. Objetivo: {target_comments} comentarios.")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=YT_DIR,
            channel="chrome",
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--start-maximized'
            ],
            no_viewport=True
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        valid_count = 0
        queries = list(SEARCH_QUERIES)
        random.shuffle(queries)
        
        for query in queries:
            if valid_count >= target_comments:
                break
                
            print(f"\n--- Buscando en YouTube (Últimas 24h): {query} ---")
            
            # El parámetro sp=EgIIAg%253D%253D ordena por "Fecha de subida: Hoy"
            page.goto(f"https://www.youtube.com/results?search_query={query}&sp=EgIIAg%253D%253D", timeout=60000)
            time.sleep(5)
            
            # Hacemos scroll para cargar más vídeos si es necesario
            for _ in range(5):
                page.mouse.wheel(0, 5000)
                time.sleep(2)
            
            videos = page.locator('ytd-video-renderer a#video-title').all()
            if not videos:
                print("No se encontraron vídeos para esta búsqueda.")
                continue
                
            links = []
            titles = []
            
            for v in videos:
                try:
                    href = v.get_attribute("href")
                    title = v.get_attribute("title") or v.text_content()
                    if href and "/watch" in href:
                        links.append("https://www.youtube.com" + href)
                        titles.append(title.strip())
                except: pass
                
            print(f"Se encontraron {len(links)} vídeos para analizar.")
            
            commented_ids = set()
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r") as f:
                    commented_ids = set(f.read().splitlines())
                    
            for i, (link, title) in enumerate(zip(links, titles)):
                if valid_count >= target_comments:
                    print(f"¡Objetivo de {target_comments} comentarios alcanzado!")
                    break
                    
                video_id = link.split("v=")[1].split("&")[0] if "v=" in link else None
                if video_id and video_id in commented_ids:
                    print(f"[-] Saltando: Ya comentamos en este vídeo en el pasado ({video_id}).")
                    continue
                    
                safe_title = title.encode('ascii', 'ignore').decode('ascii')
                print(f"\n[{valid_count+1}/{target_comments}] Verificando idioma original de: {safe_title}")
                
                # ABRE EL LINK EN UNA PESTAÑA NUEVA
                video_page = browser.pages[0].context.new_page()
                
                try:
                    video_page.goto(link, timeout=60000)
                    time.sleep(3)
                    
                    # Guardamos el segundo de inicio. Si es mayor a unos pocos segundos, YouTube lo ha cargado del historial.
                    video_time_start = video_page.evaluate("() => document.querySelector('video') ? document.querySelector('video').currentTime : 0")
                    time.sleep(2)
                    
                    # Hacer scroll para cargar comentarios
                    video_page.mouse.wheel(0, 1000)
                    time.sleep(3)
                    video_page.mouse.wheel(0, 1000)
                    time.sleep(5)
                    
                    # Extraer comentarios para detectar el idioma REAL de la audiencia
                    comments = video_page.locator('ytd-comment-thread-renderer yt-attributed-string#content-text').all_text_contents()
                    
                    comments_text = " ".join(comments[:10]).lower()
                    
                    # Palabras muy comunes en español vs inglés
                    es_words = ["gracias", "muy", "buen", "excelente", " el ", " la ", " los ", " las ", " un ", " una ", "qué", " que ", "vídeo", "hola"]
                    en_words = [" the ", " this ", " is ", " great ", " awesome ", " thank ", " thanks ", " good ", " how ", " what ", " and ", " but ", " to ", " in ", " of "]
                    
                    # Contar ocurrencias totales en el texto de los comentarios
                    es_score = sum(comments_text.count(w) for w in es_words)
                    en_score = sum(comments_text.count(w) for w in en_words)
                    
                    # Chequear también el título
                    title_lower = title.lower()
                    en_title_score = sum(title_lower.count(w.strip()) for w in ["how to", "tutorial", "the", "in", "for", "with"])
                    es_title_score = sum(title_lower.count(w.strip()) for w in ["como", "español", "para", "con", "el", "la"])
                    
                    if en_title_score > es_title_score:
                        en_score += 5
                    
                    if en_score > es_score and en_score > 0:
                        print(f"[+] Detectado: Audiencia anglófona (EN: {en_score}, ES: {es_score}).")
                        comment_text = random.choice(COMMENTS_EN)
                    else:
                        print(f"[+] Detectado: Audiencia hispanohablante (ES: {es_score}, EN: {en_score}).")
                        comment_text = random.choice(COMMENTS_ES)
                        
                    print(f"Comentario seleccionado: {comment_text}")
                    
                    # 1. Dar Like al vídeo
                    try:
                        like_btn = video_page.locator('like-button-view-model button').first
                        if like_btn.is_visible():
                            like_btn.click()
                            print("[+] Like dado al vídeo.")
                            time.sleep(1)
                    except Exception as e:
                        print("[-] No se pudo dar Like.")
                        
                    # 2. Suscribirse al canal
                    try:
                        import re
                        # Buscar el botón de suscribirse usando su rol y texto (ignora cambios de CSS)
                        sub_btn = video_page.get_by_role("button", name=re.compile(r"suscribirse|suscribirme|subscribe|suscrito|subscribed", re.IGNORECASE)).first
                        if sub_btn.is_visible():
                            btn_text = sub_btn.text_content().lower()
                            is_subscribed = "suscrito" in btn_text or "subscribed" in btn_text
                            
                            # Evitar comentar dos veces en canales donde ya hemos estado y el vídeo ya lo habíamos empezado
                            if is_subscribed and video_time_start > 10:
                                print(f"[-] Saltando vídeo: Ya estamos suscritos y YouTube lo reanudó en el segundo {int(video_time_start)} (historial). Para evitar doble comentario.")
                                continue
                                
                            if not is_subscribed:
                                sub_btn.click()
                                print("[+] Suscrito al canal.")
                                time.sleep(2)
                                
                                # 3. Activar la campanita (Todas las notificaciones)
                                try:
                                    # Buscar la campanita de notificaciones
                                    bell_btn = video_page.get_by_role("button", name=re.compile(r"notificaciones|notifications", re.IGNORECASE)).first
                                    if bell_btn.is_visible():
                                        bell_btn.click()
                                        time.sleep(1)
                                        # Clic en "Todas" o "All" de forma más flexible
                                        all_btn = video_page.locator("tp-yt-paper-item").filter(has_text=re.compile(r"Todas|All", re.IGNORECASE)).first
                                        all_btn.click(timeout=3000)
                                        print("[+] Campanita activada en 'Todas' para monitorear nuevos vídeos.")
                                except Exception as e:
                                    print(f"[-] No se pudo activar la campanita en 'Todas': {e}")
                    except Exception as e:
                        print(f"[-] No se pudo suscribir: {e}")
                    
                    try:
                        placeholder = video_page.locator('ytd-comment-simplebox-renderer div#placeholder-area, ytd-commentbox div#placeholder-area').first
                        if not placeholder.is_visible():
                            # A veces Youtube tarda más en cargar o requiere más scroll
                            video_page.mouse.wheel(0, 1000)
                            time.sleep(3)

                        if placeholder.is_visible():
                            placeholder.click()
                            time.sleep(2)
                            
                            editor = video_page.locator('ytd-comment-simplebox-renderer div#contenteditable-root, ytd-commentbox div#contenteditable-root').first
                            editor.click()
                            editor.type(comment_text, delay=50)
                            time.sleep(2)
                            
                            # Youtube envuelve el botón en ytd-button-renderer, hay que clickar el button interno
                            submit_btn = video_page.locator('ytd-button-renderer#submit-button button, ytd-button-renderer#submit-button').first
                            submit_btn.click()
                            valid_count += 1
                            print(f"OK Comentario publicado. Total en este ciclo: {valid_count}/{target_comments}")
                            if video_id:
                                with open(HISTORY_FILE, "a") as f:
                                    f.write(video_id + "\n")
                                commented_ids.add(video_id)
                            time.sleep(5)
                        else:
                            print("ERROR No se encontró la caja de comentarios (pueden estar desactivados o no cargaron).")
                    except Exception as e:
                        print(f"ERROR al intentar comentar: {e}")
                        
                except Exception as e:
                    print(f"Error procesando pestaña del video: {e}")
                    
                finally:
                    # CIERRA LA PESTAÑA DEL VIDEO
                    try:
                        video_page.close()
                        print("Pestaña cerrada.")
                    except: pass
                
                # TIEMPO DE ESPERA ALEATORIO ENTRE VIDEO Y VIDEO (10 A 20 SEGUNDOS)
                wait_video = random.randint(10, 20)
                print(f"Esperando {wait_video} segundos antes del siguiente vídeo...")
                time.sleep(wait_video)
            
        print(f"\nCiclo de búsqueda completado. Comentarios realizados en esta sesión: {valid_count}/{target_comments}")
        browser.close()

if __name__ == "__main__":
    while True:
        target_comments = random.randint(100, 150)
        try:
            run_youtube_bot(target_comments)
        except Exception as e:
            print("Error en el ciclo del bot: ", str(e).encode('ascii', 'replace').decode('ascii'))
        
        # TIEMPO DE ESPERA ALEATORIO ENTRE SESIONES DE NAVEGADOR (2 A 3 MINUTOS)
        wait_session = random.randint(120, 180)
        print(f"Navegador cerrado. Esperando {wait_session} segundos ({wait_session//60} min) antes de volver a abrir YouTube...")
        time.sleep(wait_session)

