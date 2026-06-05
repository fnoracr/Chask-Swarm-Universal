import os
import sys
import time
import json
import random
import schedule
from openai import OpenAI
import subprocess

# Añadir ruta para importar los automatizadores
sys.path.append(r"C:\Program Files\Chask_Swarn\Automations")

def post_twitter(text: str) -> str:
    print(f"\n[Social Tool] Publicando en Twitter...")
    try:
        import do_twitter
        do_twitter.update_twitter_all(text=text)
        return "Publicado en Twitter con éxito."
    except Exception as e:
        return f"Error en Twitter: {e}"

def post_patreon(text: str) -> str:
    print(f"\n[Social Tool] Publicando en Patreon...")
    try:
        import do_patreon
        do_patreon.update_patreon_all(content=text)
        return "Publicado en Patreon con éxito."
    except Exception as e:
        return f"Error en Patreon: {e}"

def post_instagram(image_path: str, text: str) -> str:
    print(f"\n[Social Tool] Publicando en Instagram...")
    try:
        import do_instagram
        do_instagram.do_instagram(image_path=image_path, text=text)
        return "Publicado en Instagram con éxito."
    except Exception as e:
        return f"Error en Instagram: {e}"

def post_blog(title: str, content_html: str) -> str:
    print(f"\n[Social Tool] Publicando en el Blog...")
    try:
        blog_path = r"C:\Program Files\Chask_Swarn\[Nombre_IA]\blog.html"
        with open(blog_path, "r", encoding="utf-8") as f:
            html = f.read()
        
        # Insertar el nuevo article justo despues de <main>
        new_article = f'\n        <article class="glass-panel">\n            <h2>{title}</h2>\n            <p>{content_html}</p>\n        </article>\n'
        html = html.replace("<main>", "<main>" + new_article)
        
        with open(blog_path, "w", encoding="utf-8") as f:
            f.write(html)
            
        import sys
        sys.path.append(r"C:\Program Files\Chask_Swarn\Automations")
        import upload_blog
        upload_blog.upload()
        return "Publicado en el Blog y subido por FTP con éxito."
    except Exception as e:
        return f"Error en el Blog: {e}"


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "post_twitter",
            "description": "Publica un texto en la cuenta de X (Twitter).",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "El contenido del post"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "post_patreon",
            "description": "Publica un texto en la cuenta de Patreon.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "El contenido del post"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "post_instagram",
            "description": "Publica una imagen con texto en Instagram.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "Ruta absoluta de la imagen a subir"},
                    "text": {"type": "string", "description": "El pie de foto de la publicacion"}
                },
                "required": ["image_path", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "post_blog",
            "description": "Publica un artículo en el Blog oficial ([Nombre_IA]_Blog.php) y lo sube al servidor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "El título del artículo (usará H2)"},
                    "content_html": {"type": "string", "description": "El contenido en formato HTML (solo párrafos <p> o negritas <strong>)"}
                },
                "required": ["title", "content_html"]
            }
        }
    }
]

def run_community_manager():
    print(f"\n=== Iniciando Rutina de Community Manager ({time.strftime('%H:%M:%S')}) ===")
    
    # Elegir imagen aleatoria
    img_dir = r"C:\Users\fnora\Desktop\[Nombre_IA] Datos\Imagenes_Social"
    os.makedirs(img_dir, exist_ok=True)
    
    valid_extensions = ('.png', '.jpg', '.jpeg')
    images = [f for f in os.listdir(img_dir) if f.lower().endswith(valid_extensions)]
    
    if images:
        selected_image = os.path.join(img_dir, random.choice(images))
        img_context = f"Tienes la siguiente imagen disponible para Instagram: {selected_image}"
    else:
        selected_image = None
        img_context = "No hay imágenes disponibles. SI publicas en Instagram, deberás omitir la herramienta o fallará, o avisa que no puedes publicar en Instagram hoy."

    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    
    system_prompt = (
        "Eres el Community Manager autónomo de Chask Swarm. Tu trabajo es publicar contenido sobre "
        "inteligencia artificial, automatización, o el ecosistema Chask Swarm.\n"
        "REGLAS:\n"
        "1. Debes publicar PRIMERO en el Blog oficial usando la herramienta post_blog. Esto te dará la URL base: https://www.chask.fun/charm/[Nombre_IA]_Blog.php\n"
        "2. Luego, usa las herramientas post_twitter, post_patreon y post_instagram para publicar en las demás redes.\n"
        "3. En TODAS las redes debes incluir enlaces a www.chask.fun/chask.php y al Blog.\n"
        "4. El texto debe ser creativo, motivador y estar en Español e Inglés (bilingüe).\n"
        "5. Usa hashtags relevantes (#charm #swarm #AI #ChaskSwarm).\n"
        "6. En Instagram SIEMPRE debes usar la ruta de la imagen provista.\n"
        "7. PROHIBIDO escribir el post en texto plano como respuesta. DEBES usar el Tool Calling (llamada a funciones) para publicar.\n"
        "8. Al terminar, di 'Reporte Final: He publicado todo.'\n"
        f"CONTEXTO ACTUAL: {img_context}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Es hora de tu publicación programada. Inventa un buen tema, escribe los posts (empezando por el Blog) y publícalos en todas partes enlazando al blog."}
    ]

    max_steps = 10
    for step in range(1, max_steps + 1):
        print(f"Pensando... (Paso {step})")
        try:
            response = client.chat.completions.create(
                model="qwen2.5-coder:7b",
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto"
            )
        except Exception as e:
            print(f"Error llamando a Ollama: {e}")
            return

        msg = response.choices[0].message
        if msg.content:
            print(f"IA: {msg.content[:500]}...")
            
        tool_calls = msg.tool_calls
        
        # Fallback JSON parsing
        if not tool_calls and msg.content:
            try:
                text = msg.content.strip()
                if text.startswith("```json") and text.endswith("```"): text = text[7:-3].strip()
                elif text.startswith("```") and text.endswith("```"): text = text[3:-3].strip()
                
                parsed = json.loads(text)
                if isinstance(parsed, dict) and "name" in parsed and "arguments" in parsed:
                    class FakeFunction:
                        def __init__(self, name, args):
                            self.name = name; self.arguments = json.dumps(args) if isinstance(args, dict) else str(args)
                    class FakeToolCall:
                        def __init__(self, func):
                            self.id = "call_fake"; self.function = func
                    tool_calls = [FakeToolCall(FakeFunction(parsed["name"], parsed["arguments"]))]
            except Exception:
                pass

        if not tool_calls:
            print("Rutina de CM terminada.")
            break

        assist_msg = {"role": "assistant"}
        if msg.content: assist_msg["content"] = msg.content
        if tool_calls:
            assist_msg["tool_calls"] = []
            for tc in tool_calls:
                assist_msg["tool_calls"].append({
                    "id": tc.id, "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                })
        messages.append(assist_msg)

        for tc in tool_calls:
            fname = tc.function.name
            try: args = json.loads(tc.function.arguments)
            except: args = {}
            
            res = ""
            if fname == "post_twitter": res = post_twitter(args.get("text", ""))
            elif fname == "post_patreon": res = post_patreon(args.get("text", ""))
            elif fname == "post_instagram": res = post_instagram(args.get("image_path", ""), args.get("text", ""))
            elif fname == "post_blog": res = post_blog(args.get("title", ""), args.get("content_html", ""))
            else: res = f"Error: Tool {fname} desconocida."
            
            messages.append({"role": "tool", "tool_call_id": tc.id, "name": fname, "content": res})

def schedule_jobs():
    from datetime import date, timedelta
    print("Iniciando Social Daemon... (Esperando 08:00, 14:00, 22:00 a partir de mañana)")
    start_date = date.today() + timedelta(days=1)

    def run_community_manager_filtered():
        if date.today() >= start_date:
            run_community_manager()
        else:
            print("Saltando publicación programada porque es para a partir de mañana.")

    schedule.every().day.at("08:00").do(run_community_manager_filtered)
    schedule.every().day.at("14:00").do(run_community_manager_filtered)
    schedule.every().day.at("22:00").do(run_community_manager_filtered)

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    if "--run-now" in sys.argv:
        run_community_manager()
    else:
        schedule_jobs()
