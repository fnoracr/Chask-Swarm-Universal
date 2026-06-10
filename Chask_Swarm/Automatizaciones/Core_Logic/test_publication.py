import sys
sys.path.insert(0, r"C:\Program Files\Chask_Swarm\Advanced_Tools\modules\YouTube_y_Social")
import social_daemon

title = "🔥 El Amanecer de los Agentes Autónomos con Chask Swarm"

html_content = """<p>¿Imaginas un ecosistema donde múltiples IAs se comunican entre sí para resolver problemas complejos, programar aplicaciones enteras y gestionar tu PC de forma autónoma? <strong>Eso es Chask Swarm.</strong></p>
<p>Hoy, hemos implementado con éxito la primera <em>Mente Colmena</em> (Hive Mind) local, capaz de delegar tareas a modelos agénticos que operan en segundo plano, publicando en redes, redactando código y auditando seguridad.</p>
<p>Descubre cómo puedes transformar tu forma de trabajar uniéndote a nuestra revolución.</p>
<p><strong>🌐 Web Oficial:</strong> <a href="https://www.chask.fun/chask.php">www.chask.fun/chask.php</a></p>"""

text_social = """🚀 ¡El Amanecer de los Agentes Autónomos! 

¿Imaginas un ecosistema donde múltiples IAs colaboran para programar y gestionar tu PC de forma autónoma? Eso es Chask Swarm. Hoy hemos encendido la primera Mente Colmena local. 🧠💻

Lee el artículo completo en nuestro nuevo Blog Oficial y únete a la revolución:
🌐 Web: https://www.chask.fun/chask.php
📰 Blog: https://www.chask.fun/charm/Charm_Blog.php

#charm #swarm #AI #ChaskSwarm #productividad"""

img_path = r"C:\Users\fnora\Desktop\Nora Datos\Imagenes_Social\post_ia.png"

print("1. Publicando en el Blog...")
print(social_daemon.post_blog(title, html_content))

print("\n2. Publicando en Twitter...")
print(social_daemon.post_twitter(text_social))

print("\n3. Publicando en Patreon...")
print(social_daemon.post_patreon(text_social))

print("\n4. Publicando en Instagram...")
print(social_daemon.post_instagram(img_path, text_social))

print("\n¡Prueba de publicación completada!")
