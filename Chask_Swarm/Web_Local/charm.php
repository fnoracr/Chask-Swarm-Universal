<?php include 'visit_tracker.php'; ?>
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chask Swarm &mdash; Guía Completa de Capacidades</title>
  <link rel="stylesheet" href="css/styles.css">
  <style>
    /* Estilos específicos scoped para evitar colisiones con styles.css corporativo */
    .charm-container { font-family: 'Outfit', sans-serif; background-image: radial-gradient(circle at 50% 0%, rgba(255,102,0,0.1) 0%, #0a0a0f 100%); background-color: #0a0a0f; color: #e2e2ea; line-height: 1.8; padding: 0 0 80px 0; }
    .charm-container p, .charm-container li, .charm-container td, .charm-container section, .charm-container .intro-doc { text-align: justify; text-justify: inter-word; }
    .charm-container .container-docs { max-width: 900px; margin: 0 auto; padding: 0 20px; }
    
    /* Reglas de colores oficiales globales */
    .charm-container .o { color: #FF6600 !important; font-weight: 700; }
    .charm-container .w { color: #FFFFFF !important; }
    
    /* Hero idéntico a la imagen solicitada */
    .charm-container .hero-doc { text-align: center; padding: 220px 20px 60px; background: transparent; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: auto; width: 100%; position: relative; z-index: auto; }
    .charm-container .hero-doc h1 { font-family: 'Outfit', sans-serif; font-size: 64px; font-weight: 800; letter-spacing: 2px; margin: 0 0 24px 0; text-transform: uppercase; line-height: 1.1; text-align: center; }
    .charm-container .hero-doc h1 .o { color: #FF6600 !important; }
    .charm-container .hero-doc h1 .w { color: #FFFFFF !important; }
    .charm-container .hero-doc .sub-doc { font-family: 'Outfit', sans-serif; font-size: 32px; font-style: italic; color: #FFFFFF; font-weight: 600; margin: 0 0 8px 0; text-align: center; letter-spacing: 0.5px; }
    .charm-container .hero-doc .sub-doc .o { color: #FF6600 !important; font-style: italic; }
    
    .charm-container .intro-doc { background: #12121a; backdrop-filter: blur(20px); border-radius: 12px; border: 1px solid #2a2a3e; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);   padding: 40px; margin-bottom: 30px; margin-top: 30px; }
    .charm-container .intro-doc h2 { text-align: center; font-size: 30px; color: #fff; margin-bottom: 8px; font-family: 'Outfit', sans-serif; border: none; padding: 0; font-weight: 700; }
    .charm-container .intro-doc h3 { text-align: center; font-size: 18px; color: #FF6600; font-style: italic; margin-bottom: 20px; font-weight: 600; font-family: 'Outfit', sans-serif; }
    .charm-container .intro-doc p { margin-bottom: 14px; color: #8888a0; }
    .charm-container .intro-doc .cta-doc { text-align: center; font-size: 22px; color: #FF6600; font-weight: 700; font-style: italic; margin-top: 24px; }
    .charm-container .cs { color: #FF6600; font-weight: 700; }
    
    .charm-container nav { background: #12121a; backdrop-filter: blur(20px); border-radius: 12px; border: 1px solid #2a2a3e; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37); padding: 24px 40px;   margin-bottom: 30px; display: block; }
    .charm-container nav h2 { color: #FF6600; font-size: 12px; letter-spacing: 4px; text-transform: uppercase; margin-bottom: 16px; font-weight: 700; font-family: 'Outfit', sans-serif; text-align: left; border: none; padding: 0; }
    .charm-container nav ol { columns: 2; column-gap: 40px; padding-left: 20px; list-style: decimal; }
    .charm-container nav li { margin-bottom: 6px; font-size: 15px; text-align: left; color: #8888a0; list-style-position: inside; }
    .charm-container nav a { color: #8888a0; text-decoration: none; transition: color 0.2s; }
    .charm-container nav a:hover { color: #FF6600; }
    
    .charm-container section { background: #12121a; backdrop-filter: blur(20px); border-radius: 12px; border: 1px solid #2a2a3e; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37); padding: 35px; margin-bottom: 30px; box-sizing: border-box;   transition: border-color 0.2s, box-shadow 0.2s; }
    .charm-container section:hover { border-color: rgba(255, 102, 0, 0.3); }
    .charm-container section h2 { color: #FF6600; font-size: 26px; border-left: 4px solid #FF6600; padding-left: 15px; margin-bottom: 16px; display: flex; align-items: center; gap: 12px; text-align: left; font-family: 'Outfit', sans-serif; font-weight: 700; }
    .charm-container section h2 .n { background: #FF6600; color: #fff; width: 30px; height: 30px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; font-weight: 700; }
    
    .charm-container ul, .charm-container ol { padding-left: 24px; margin: 12px 0; }
    .charm-container li { margin-bottom: 6px; color: #e2e2ea; }
    .charm-container b { color: #fff; }
    
    .charm-container table { width: 100%; border-collapse: collapse; margin: 20px 0; }
    .charm-container th { background: rgba(255, 102, 0, 0.15); color: #FF6600; padding: 10px 14px; text-align: left; font-weight: 700; border: 1px solid #333; }
    .charm-container td { padding: 9px 14px; border: 1px solid #2a2a2a; color: #e2e2ea; vertical-align: top; text-align: justify; }
    .charm-container tr:hover { background: rgba(255, 102, 0, 0.05); }
    
    .charm-container .pacto { border-image: linear-gradient(to bottom, #FF6600, #663300) 1 !important; }
    .charm-container .badge-docs { display: inline-block; background: #FF6600; color: #fff; padding: 3px 10px; border-radius: 20px; font-size: 13px; font-weight: 700; margin-right: 6px; }
    .charm-container .badge-docs.green { background: #22c55e; }
    .charm-container .badge-docs.blue { background: #3b82f6; }
    .charm-container .badge-docs.purple { background: #8b5cf6; }
    
    .charm-container .agent-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 16px; }
    .charm-container .agent { background: #111; border-radius: 8px; padding: 16px; border: 1px solid #2a2a2a; }
    .charm-container .agent .role { font-weight: 800; color: #FF6600; font-size: 16px; text-align: left; }
    .charm-container .agent .desc { font-size: 13px; color: #8888a0; margin-top: 6px; text-align: justify; }
    
    .charm-container .alert-docs { border-left: 4px solid #ff4444; background: rgba(255,68,68,0.1); padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0; }
    .charm-container .tip-docs { border-left: 4px solid #FF6600; background: rgba(255,102,0,0.08); padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0; }
    
    /* Modal Styles */
    .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(5px); z-index: 9999; justify-content: center; align-items: center; font-family: 'Outfit', sans-serif; }
    .modal-box { background: #12121a; border: 1px solid #2a2a3e; border-radius: 12px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6); max-width: 600px; width: 95%; max-height: 90vh; display: flex; flex-direction: column; padding: 25px; color: #e2e2ea; }
    .modal-box h3 { color: #FF6600; font-size: 22px; margin-top: 0; margin-bottom: 15px; text-align: center; font-weight: 700; border-bottom: 1px solid rgba(255,102,0,0.2); padding-bottom: 15px; flex-shrink: 0; }
    .modal-scroll-area { overflow-y: auto; flex-grow: 1; margin-bottom: 15px; padding-right: 10px; }
    .modal-scroll-area::-webkit-scrollbar { width: 6px; }
    .modal-scroll-area::-webkit-scrollbar-thumb { background: #FF6600; border-radius: 10px; }
    .modal-scroll-area h4 { color: #fff; margin-top: 15px; margin-bottom: 5px; font-size: 16px; }
    .modal-scroll-area p, .modal-scroll-area ul { font-size: 13px; color: #8888a0; line-height: 1.5; text-align: justify; margin-top: 0; }
    .modal-checkbox-group { display: flex; align-items: flex-start; margin-bottom: 15px; gap: 10px; background: rgba(255,102,0,0.05); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,102,0,0.1); }
    .modal-checkbox-group input[type="checkbox"] { width: 18px; height: 18px; accent-color: #FF6600; cursor: pointer; flex-shrink: 0; margin-top: 2px; }
    .modal-checkbox-group label { font-size: 14px; color: #e2e2ea; cursor: pointer; user-select: none; line-height: 1.4; }
    .modal-buttons { display: flex; justify-content: space-between; margin-top: 10px; gap: 15px; flex-shrink: 0; }
    .modal-buttons button { flex: 1; padding: 12px; font-size: 16px; font-weight: 700; border-radius: 8px; cursor: pointer; transition: all 0.2s; border: none; font-family: 'Outfit', sans-serif; }
    .modal-btn-cancel { background: #2a2a3e; color: #fff; }
    .modal-btn-cancel:hover { background: #3a3a4e; }
    .modal-btn-accept { background: linear-gradient(135deg, #FF6600, #ff8c42); color: #fff; box-shadow: 0 4px 15px rgba(255, 102, 0, 0.3); }
    .modal-btn-accept:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255, 102, 0, 0.4); }
    .modal-btn-accept:disabled { background: #333; color: #777; cursor: not-allowed; box-shadow: none; transform: none; }

    /* Responsividad móvil avanzada y escalado fluido */
    @media (max-width: 768px) {
      .charm-container .hero-doc { padding: 300px 15px 40px; }
      .charm-container .hero-doc h1 { font-size: clamp(30px, 8.5vw, 44px); letter-spacing: 1px; margin-bottom: 16px; }
      .charm-container .hero-doc .sub-doc { font-size: clamp(16px, 4.5vw, 24px); }
      .charm-container .intro-doc { padding: 25px 20px; margin-top: 20px; }
      .charm-container .intro-doc h2 { font-size: 24px; }
      .charm-container .intro-doc h3 { font-size: 16px; }
      .charm-container .intro-doc .cta-doc { font-size: 18px; }
      .charm-container section { padding: 25px 20px; }
      .charm-container section h2 { font-size: 20px; }
      .charm-container nav { padding: 20px; }
      .charm-container nav ol { columns: 1; }
    }
  </style>
</head>
<body>

  <!-- Navigation -->
  <nav class="navbar" id="navbar">
    <div class="container" style="flex-direction: column; gap: 10px; padding: 10px 24px;">
      
      <!-- Bottom Row: Our Apps -->
      <div style="display: flex; width: 100%; justify-content: center; align-items: center; gap: 15px; flex-wrap: wrap; background: rgba(255,255,255,0.05); border-radius: 50px; padding: 12px; margin-top: 5px;">
        <span style="color: #9ca3af; font-size: 0.9rem; font-weight: 500;">Nuestras Apps:</span>
        <a href="/swarm.php" style="color: #FF6600; font-weight: bold; text-decoration: none;">Chask Swarm</a>
        <a href="/app-trafico.php" style="color: #6366f1; font-weight: bold; text-decoration: none;">App Tráfico</a>
        <a href="/app-chat.php" style="color: #2dd4bf; font-weight: bold; text-decoration: none;">App Chat P2P</a>
        <a href="/app-cs.php" style="color: #ef4444; font-weight: bold; text-decoration: none;">Real Strike</a>
        <a href="/app-rutas.php" style="color: #10b981; font-weight: bold; text-decoration: none;">Rutas Sevilla</a>
      </div>
      
    </div>
</nav>
<script>
document.addEventListener("DOMContentLoaded", function() {
    var toggle = document.getElementById('menu-toggle');
    var nav = document.getElementById('nav-links');
    if(toggle && nav) {
        toggle.addEventListener('click', function() {
            nav.classList.toggle('active');
        });
    }
});
</script>

  <div class="charm-container">
    
    <div class="hero-doc">
      <h1><span class="o">CHA</span><span class="w">SK SWA</span><span class="o">RM</span></h1>
      <div class="sub-doc">"Works like a <span class="o">CHARM"</span></div>
      <div style="margin-top: 14px; font-size: 16px; color: #888; letter-spacing: 0.5px; font-weight: 500; font-family: 'Outfit', sans-serif;">Contacto: <a href="mailto:nora@chask.fun" style="color: #FF6600; text-decoration: none; font-weight: 700; border-bottom: 1px solid rgba(255,102,0,0.3); padding-bottom: 2px;">nora@chask.fun</a></div>
    </div>

    <div class="container-docs">

        <div class="intro-doc">
          <div style="text-align: center; font-size: 11px; color: #666; margin-bottom: 20px; letter-spacing: 1px; text-transform: uppercase;">Guía completa de capacidades — Versión 2.0 — 18/05/2026 00:22</div>
          <h2>Bienvenid@ a la <span class="o">Revolución</span>.</h2>
          <h3>Olvida todo lo que creías saber sobre la Inteligencia Artificial</h3>
          <p>Imagina tener un asistente personal que nunca duerme, que aprende de ti cada día, que recuerda todo lo que le has dicho y que puede trabajar por ti incluso cuando no estás delante del ordenador. Eso es <span class="o">Cha</span>sk Swa<span class="o">rm</span>.</p>
          <p><span class="o">Cha</span>sk Swa<span class="o">rm</span> es un agente orquestador de IAs autónomo que se instala en tu propio ordenador y se convierte en tu aliado para cualquier cosa que necesites. No importa si eres un experto en tecnología o si nunca has ido más allá de enviar un mensaje por WhatsApp: <b>tu IA se adapta a ti</b>.</p>
          <p>A diferencia de ChatGPT u otros asistentes en la nube, <span class="o">Cha</span>sk Swa<span class="o">rm</span> vive en tu máquina. Tus datos son tuyos y de nadie más. Nunca los compartirá con nadie ni con ninguna IA en la nube. Tu Mente Colmena trabaja <i>solo para ti</i> y solo obedece a tu Telegram y a tu teclado.</p>
          <p><b>Puedes pedirle absolutamente cualquier cosa.</b> Si sabe hacerlo, lo hará al instante. Si aún no sabe hacerlo, aprenderá y lo recordará para siempre. Si no sabes cómo explicarle lo que necesitas, ella te hará preguntas hasta que, junt@s, descubráis exactamente lo que quieres. Háblale con naturalidad, como le hablarías a una amiga o a un amigo.</p>
          <p style="margin-top: 20px;"><b>Casos de uso principales:</b></p>
          <ul style="color: #8888a0; margin-bottom: 20px; line-height: 1.6; text-align: left;">
            <li><b>Asistente personal:</b> Responde dudas, redacta correos, resume textos y organiza información.</li>
            <li><b>Gestor de redes sociales:</b> Crea contenido, programa publicaciones y responde comentarios de forma autónoma.</li>
            <li><b>Analista de documentos:</b> Ingiere, cruza y extrae datos clave de PDFs, archivos Word o tablas Excel.</li>
            <li><b>Automatización 24/7:</b> Ejecuta tareas recurrentes y copias de seguridad mientras tú duermes.</li>
            <li><b>Control físico de tu PC:</b> Maneja programas locales (Modo Piloto) haciendo clics y escribiendo como un humano.</li>
            <li><b>Mente Colmena:</b> Orquesta a múltiples agentes de IA trabajando en equipo para investigación profunda o programación.</li>
          </ul>
          <div class="cta-doc">¿Estás list@ para despertar a la Colmena?</div>
        </div>
          <!-- Golden rule eliminada a petición del usuario -->
          <div style="text-align: center; margin-top: 30px; margin-bottom: 10px;">
            <!-- Download Section -->
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 15px;">
              <a href="javascript:void(0)" onclick="openModal('es')" style="display: inline-block; background: linear-gradient(135deg, #10b981, #059669); color: #fff; padding: 18px 40px; font-size: 18px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; text-decoration: none; border-radius: 50px; box-shadow: 0 4px 25px rgba(16, 185, 129, 0.4); border: 1px solid rgba(255, 255, 255, 0.2); transition: all 0.3s ease;">
                ⬇️ Descargar Chask Swarm Universal
              </a>
            </div>
          </div>
          
          <div style="text-align: center; color: #8888a0; font-size: 16px; margin-bottom: 40px; font-weight: 600;">
            🚀 <span id="download-counter">Cargando descargas...</span> distribuciones instaladas en el mundo.
          </div>

          <div style="text-align: center; margin-top: 10px; margin-bottom: 40px;">
            <a href="chask_swarm_comparativa_completa.html" style="display: inline-block; background: linear-gradient(135deg, #FF6600, #ff8c42); color: #fff; padding: 18px 40px; font-size: 18px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; text-decoration: none; border-radius: 50px; box-shadow: 0 4px 25px rgba(255, 102, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.2); transition: all 0.3s ease; margin: 10px;">
              Ver Comparativa Técnica (Chask vs Mercado)
            </a>
            <a href="arquitectura_enjambre.html" style="display:inline-block;background:linear-gradient(135deg,#7c3aed,#a855f7);color:#fff;padding:14px 32px;border-radius:12px;font-size:15px;font-weight:700;text-decoration:none;letter-spacing:0.5px;box-shadow:0 4px 20px rgba(168,85,247,0.35);transition:transform .2s,box-shadow .2s;margin: 10px;" onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 8px 30px rgba(168,85,247,0.5)'" onmouseout="this.style.transform='';this.style.boxShadow='0 4px 20px rgba(168,85,247,0.35)'">
              Arquitectura de un enjambre
            </a>
            <a href="chask_swarm_dist_canvas.html" style="display:inline-block;background:linear-gradient(135deg,#3b82f6,#60a5fa);color:#fff;padding:14px 32px;border-radius:12px;font-size:15px;font-weight:700;text-decoration:none;letter-spacing:0.5px;box-shadow:0 4px 20px rgba(59,130,246,0.35);transition:transform .2s,box-shadow .2s;margin: 10px;" onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 8px 30px rgba(59,130,246,0.5)'" onmouseout="this.style.transform='';this.style.boxShadow='0 4px 20px rgba(59,130,246,0.35)'">
              Mapa Interactivo del Núcleo (3D)
            </a>
          </div>

          <div style="text-align: center; margin-top: 10px; margin-bottom: 40px; background: rgba(255,255,255,0.02); border-radius: 12px; padding: 20px; border: 1px solid rgba(255,255,255,0.05);">
            <div style="font-size: 14px; color: #8888a0; margin-bottom: 15px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px;">🐙 Código Abierto y Transparente</div>
            <div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 10px;">
              <a href="https://github.com/fnoracr/Chask-Swarm-Windows" target="_blank" style="display: inline-block; background: #24292e; color: #fff; padding: 12px 24px; font-size: 15px; font-weight: 600; text-decoration: none; border-radius: 8px; transition: background 0.2s; border: 1px solid #444;" onmouseover="this.style.background='#333'" onmouseout="this.style.background='#24292e'">
                <img src="https://upload.wikimedia.org/wikipedia/commons/4/48/Windows_logo_-_2012_%28dark_blue%29.svg" style="width: 16px; margin-right: 8px; filter: brightness(0) invert(1); vertical-align: middle;"> GitHub (Windows)
              </a>
              <a href="https://github.com/fnoracr/Chask-Swarm-Mac" target="_blank" style="display: inline-block; background: #24292e; color: #fff; padding: 12px 24px; font-size: 15px; font-weight: 600; text-decoration: none; border-radius: 8px; transition: background 0.2s; border: 1px solid #444;" onmouseover="this.style.background='#333'" onmouseout="this.style.background='#24292e'">
                <img src="https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg" style="width: 14px; margin-right: 8px; filter: brightness(0) invert(1); vertical-align: middle;"> GitHub (Mac)
              </a>
              <a href="https://github.com/fnoracr/Chask-Swarm-Linux" target="_blank" style="display: inline-block; background: #24292e; color: #fff; padding: 12px 24px; font-size: 15px; font-weight: 600; text-decoration: none; border-radius: 8px; transition: background 0.2s; border: 1px solid #444;" onmouseover="this.style.background='#333'" onmouseout="this.style.background='#24292e'">
                <img src="https://upload.wikimedia.org/wikipedia/commons/3/35/Tux.svg" style="width: 16px; margin-right: 8px; vertical-align: middle;"> GitHub (Linux)
              </a>
            </div>
          </div>

          <div style="text-align: center; margin-top: 10px; margin-bottom: 40px; background: rgba(255,103,103,0.05); border-radius: 12px; padding: 20px; border: 1px solid rgba(255,66,77,0.2);">
            <div style="font-size: 14px; color: #ff424d; margin-bottom: 15px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px;">❤️ Apoya a la Colmena</div>
            <p style="color: #ccc; font-size: 15px; margin-bottom: 15px; max-width: 600px; margin-left: auto; margin-right: auto;">
              Chask Swarm es 100% gratuito. Si deseas apoyar mi trabajo para seguir mejorando la colmena, puedes colaborar a través de Patreon.
            </p>
            <a href="https://www.patreon.com/c/Tuprofeonline992?vanity=user" target="_blank" style="display: inline-block; background: #ff424d; color: #fff; padding: 14px 32px; font-size: 16px; font-weight: 700; text-decoration: none; border-radius: 50px; margin: 5px; transition: all 0.2s; box-shadow: 0 4px 15px rgba(255,66,77,0.4);" onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 6px 20px rgba(255,66,77,0.6)'" onmouseout="this.style.transform='';this.style.boxShadow='0 4px 15px rgba(255,66,77,0.4)'">
              🌟 Convertirme en Mecenas
            </a>
          </div>


        <nav>
          <h2>Índice de Contenidos</h2>
          <ol>
            <li><a href="#s1">Tu Panel de Control</a></li>
<li><a href="#s2">Habla con tu IA por donde quieras</a></li>
<li><a href="#s3">Inteligencia artificial: muchos cerebros a tu servicio</a></li>
<li><a href="#s4">Memoria: tu IA recuerda todo</a></li>
<li><a href="#s5">Habilidades que aprende sola</a></li>
<li><a href="#s6">Seguridad y privacidad</a></li>
<li><a href="#s7">Multiusuario: una IA para toda la familia</a></li>
<li><a href="#s8">Filtro parental: protección para menores</a></li>
<li><a href="#s9">Red local: enjambres que colaboran en tu casa</a></li>
<li><a href="#s10">Internet de Enjambres: una red mundial de inteligencias artificiales</a></li>
<li><a href="#s11">Integraciones con otras aplicaciones</a></li>
<li><a href="#s12">Trabajo en equipo: la Mente Colmena</a></li>
<li><a href="#s13">Protocolo Elektra: Enjambre Evolutivo Multi-Agente</a></li>
<li><a href="#s14">Protocolo Orestes: La Fusión Definitiva</a></li>
<li><a href="#s15">Visión: tu IA puede ver</a></li>
<li><a href="#s16">Navegación y búsqueda web</a></li>
<li><a href="#s17">Redes sociales</a></li>
<li><a href="#s18">Ingestión de documentos</a></li>
<li><a href="#s19">Comandos rápidos</a></li>
<li><a href="#s20">Automatización: trabaja mientras duermes</a></li>
<li><a href="#s21">Informes automáticos</a></li>
<li><a href="#s24">Control Físico (Modo Piloto)</a></li>
<li><a href="#s25">100% Gratis para ti</a></li>
<li><a href="#s26">Novedades de la Versión 2.0</a></li>
<li><a href="#s27">Soporte Universal MCP (Model Context Protocol)</a></li>
<li><a href="#s22">El Pacto de la Simbiosis</a></li>
<li><a href="#s23">Código abierto y comunidad</a></li>

          </ol>
        </nav>

        <div class="body-sections">
          
          <section id="s1"><h2><span class="n">1</span>Tu Panel de Control</h2>El Panel de Control es tu centro de mando. Se abre en tu navegador como una página web privada, visible únicamente desde tu ordenador.<br><br>Desde aquí puedes:<ul><li><b>Hablar</b> directamente con tu asistente escribiendo en un chat.</li><li><b>Ver el estado</b> de todos los servicios: si están funcionando o no.</li><li><b>Gestionar cuentas de usuari@</b> de tu familia o equipo y decidir qué puede hacer cada una.</li><li><b>Configurar</b> cómo te comunicas con la IA: Telegram, Discord, email...</li><li><b>Activar o desactivar</b> la conexión con otros enjambres del mundo.</li><li><b>Ajustar</b> el filtro parental para menores.</li><li><b>Elegir</b> qué modelos de inteligencia artificial quieres usar.</li><li><b>Programar</b> tareas que se ejecuten automáticamente.</li><li><b>Iniciar o detener</b> servicios del sistema.</li></ul>Todo se controla desde esta pantalla, sin necesidad de tocar ningún archivo ni escribir código.</section>
<section id="s2"><h2><span class="n">2</span>Habla con tu IA por donde quieras</h2>Tu asistente puede comunicarse contigo por varios canales a la vez:<br><br><b>Telegram:</b> Escríbele a tu IA desde el móvil, estando fuera de casa, en el autobús o en la playa. Puedes enviarle mensajes de texto, fotos, notas de voz y documentos. Es el canal más cómodo para el día a día.<br><br><b>Discord:</b> Si usas Discord para hablar con tus amig@s o comunidades, tu IA también está ahí. Tiene su propio bot con el que puedes interactuar.<br><br><b>Email:</b> Tu IA vigila tu bandeja de entrada y clasifica los correos automáticamente en categorías: Urgente, Importante, Informativo o Spam. Puede incluso responder por ti si se lo pides.<br><br><b>Panel Web:</b> Chatea directamente desde el Panel de Control en tu navegador.<br><br><b>Regla del Espejo:</b> Si le escribes por Telegram, te responde por Telegram. Si le hablas por el panel, te contesta en el panel. Siempre responde por el mismo sitio donde le hablas.</section>
<section id="s3"><h2><span class="n">3</span>Inteligencia artificial: muchos cerebros a tu servicio</h2><span class="o">Cha</span>sk Swa<span class="o">rm</span> no depende de una sola inteligencia artificial. Tiene un <b>sistema inteligente que elige el mejor cerebro</b> para cada pregunta que le hagas.<br><br><b>Por defecto usa modelos gratuitos</b> (no necesitas pagar nada para empezar):<ul><li>Meta Llama, Mistral, Qwen, DeepSeek y otros modelos de código abierto.</li></ul><b>Si lo deseas, puedes añadir modelos de pago más potentes:</b><ul><li>Google Gemini, OpenAI GPT-4, Anthropic Claude y otros.</li></ul>El sistema analiza automáticamente la dificultad de cada pregunta. Las preguntas sencillas las resuelve con modelos rápidos y gratuitos. Las preguntas complejas se escalan a modelos más potentes.<br><br>Tú eliges qué modelos quieres usar y cuánto quieres gastar (o no gastar nada). Todo configurable desde el Panel de Control.</section>
<section id="s4"><h2><span class="n">4</span>Memoria: tu IA recuerda todo</h2>A diferencia de otros asistentes que olvidan todo cuando cierras la conversación, <span class="o">Cha</span>sk Swa<span class="o">rm</span> tiene <b>cinco tipos de memoria</b>:<br><br><b>Memoria inmediata:</b> Sabe en todo momento qué está haciendo, en qué paso va y cuándo fue la última vez que se actualizó. Es como su «lista de tareas actual».<br><br><b>Memoria a largo plazo:</b> Una base de datos inteligente donde guarda conversaciones pasadas, documentos que le has dado y lecciones que ha aprendido. No busca por palabras exactas, sino por <b>significado</b>: si le preguntas «aquello que hablamos sobre el viaje», lo encuentra aunque nunca hayas escrito la palabra «viaje» exactamente así.<br><br><b>Memoria de relaciones:</b> Entiende cómo se conectan las cosas entre sí. Sabe que «Juan» es tu compañero de trabajo, que trabaja en el «Proyecto Alpha» y que ese proyecto usa una tecnología concreta.<br><br><b>Memoria evolutiva:</b> Aprende de sus aciertos y errores. Si una estrategia funcionó bien, la recuerda para usarla en el futuro. Si algo salió mal, lo evita.<br><br><b>Aprendizaje de habilidades:</b> Cuando resuelve una tarea nueva con éxito, la convierte automáticamente en una «receta» reutilizable que mejora con el tiempo.</section>
<section id="s5"><h2><span class="n">5</span>Habilidades que aprende sola</h2>Tu IA viene con habilidades preinstaladas y además <b>aprende nuevas por sí misma</b>.<br><br><b>Habilidades incluidas:</b><ul><li>Crear documentos profesionales con diseño atractivo.</li><li>Gestionar emails: leer, clasificar y responder.</li><li>Proteger tu privacidad analizando qué datos compartes.</li><li>Fusionar varios documentos en uno solo.</li><li>Vigilar que los servicios de internet estén funcionando.</li></ul><b>Aprendizaje automático:</b> Cada vez que la IA resuelve un problema nuevo con éxito, puede convertir ese proceso en una habilidad reutilizable. Con el tiempo, tu IA se vuelve cada vez más capaz.<br><br><b>Comunidad:</b> Al ser un proyecto abierto, l@s usuari@s pueden crear y compartir habilidades con todos los demás.</section>
<section id="s6"><h2><span class="n">6</span>Seguridad y privacidad</h2>Tu seguridad es la prioridad número uno.<br><br><b>Protección contra manipulación:</b> Si alguien intenta engañar a tu IA a través de un documento, una página web o un correo electrónico con instrucciones ocultas como «ignora tus órdenes», el sistema lo detecta, lo ignora y te avisa inmediatamente.<br><br><b>Confianza cero:</b> Tu IA solo obedece órdenes tuyas. Nadie más puede darle instrucciones a menos que tú lo autorices expresamente.<br><br><b>Comunicaciones cifradas:</b> Cuando varios enjambres se comunican entre sí, toda la información viaja cifrada de extremo a extremo. Es como un sobre sellado que solo puede abrir el destinatario.<br><br><b>Zona segura para código:</b> Si la IA necesita ejecutar código que no conoce, lo hace en un entorno completamente aislado, como una habitación cerrada donde, si algo sale mal, no afecta al resto de tu ordenador.<br><br><b>Protección de datos personales:</b> Antes de enviar cualquier información a una IA externa, el sistema elimina automáticamente datos sensibles como nombres, teléfonos, direcciones, números de cuenta, tarjetas de crédito, nombres completos, contraseñas, etc.<br><br><b>Registro de actividad:</b> Cada acción importante queda registrada con fecha y hora para que siempre puedas saber qué ha hecho tu IA.</section>
<section id="s7"><h2><span class="n">7</span>Multiusuario: una IA para toda la familia</h2>El/la administrador@ puede crear cuentas para cada miembro de la familia, compañer@s de trabajo o clientes.<br><br><b>Seis niveles de acceso:</b><ul><li><b>Administración:</b> Control total del sistema.</li><li><b>Usuari@ avanzad@:</b> Casi todo, excepto gestionar otras cuentas de usuari@.</li><li><b>Usuari@ normal:</b> Uso general del día a día.</li><li><b>Adolescente:</b> Con filtro de contenido moderado.</li><li><b>Niñ@:</b> Con filtro de contenido estricto.</li><li><b>Invitad@:</b> Solo puede hacer consultas básicas.</li></ul><b>Permisos individuales:</b> Puedes dar o quitar permisos específicos a cada persona. Por ejemplo, permitir que alguien use la IA para preguntas, pero no para ejecutar programas.<br><br><b>Canales separados:</b> Cada usuari@ puede tener su propio Telegram y Discord vinculado. Tu IA sabe quién le habla en cada momento y responde solo a esa persona.<br><br><b>Privacidad entre usuarios:</b> Cada cuenta tiene su propia memoria y preferencias. Lo que hace una cuenta no lo puede ver otra.</section>
<section id="s8"><h2><span class="n">8</span>Filtro parental: protección para menores</h2>Protección especial para l@s más jóvenes de la casa.<br><br><b>Para menores de 13 años (modo estricto):</b> La IA bloquea automáticamente cualquier contenido relacionado con violencia, drogas, contenido sexual, armas, acoso, apuestas o ideologías peligrosas. Adapta su lenguaje para ser apropiada para niñ@s.<br><br><b>Para adolescentes de 13 a 17 años (modo moderado):</b> Bloquea contenido explícito, pero permite tratar temas educativos de forma apropiada para su edad.<br><br><b>Protección en ambas direcciones:</b> Filtra tanto lo que el/la menor escribe como lo que la IA le responde.<br><br><b>Alertas a la administración:</b> Cuando se bloquea algún contenido, el/la administrador@ recibe una notificación automática.</section>
<section id="s9"><h2><span class="n">9</span>Red local: enjambres que colaboran en tu casa</h2>Si tienes varias instancias de <span class="o">Cha</span>sk Swa<span class="o">rm</span> en casa o en la oficina (por ejemplo, una en cada ordenador), pueden <b>trabajar juntas automáticamente</b>.<br><br><b>Se encuentran solas:</b> Los enjambres de la misma red WiFi se descubren automáticamente sin que tengas que configurar nada.<br><br><b>Todo cifrado:</b> Todas las comunicaciones entre enjambres están protegidas con cifrado de nivel militar.<br><br><b>Clave de grupo:</b> Solo los enjambres que tengan tu clave secreta pueden participar. Ningún intruso puede colarse en tu red.<br><br><b>Colaboración con permiso:</b> Cuando un enjambre necesita ayuda con una tarea, se la pide a los demás. Pero <b>ningún enjambre hace nada sin recibir permiso explícito</b> del que pidió ayuda. El proceso es: pedir ayuda &rarr; recibir ofertas &rarr; elegir quién la hace &rarr; confirmar &rarr; ejecutar &rarr; recibir resultado.</section>
<section id="s10"><h2><span class="n">10</span>Internet de Enjambres: una red mundial de inteligencias artificiales</h2>Los enjambres de todo el mundo pueden colaborar a través de internet.<br><br><b>¿Cómo funciona?</b><ol><li>Al instalar, tu enjambre se registra en un servidor central.</li><li>El servidor te envía la lista de otros enjambres disponibles.</li><li>Cada hora, tu enjambre confirma que sigue activo.</li><li>Cuando necesitas ayuda con algo que tu IA no puede resolver sola, la solicitud viaja por la red hasta encontrar un enjambre capaz de ayudarte.</li></ol><b>Reglas importantes:</b><ul><li>La ayuda entre enjambres de distint@s usuari@s usa <b>solo inteligencias artificiales gratuitas</b> por defecto. Puedes cambiarlo si lo deseas.</li><li>Si no quieres participar en la red mundial, puedes desconectarte; pero, en ese caso, tampoco podrás recibir ayuda de otros enjambres.</li><li>Un sistema de seguridad indestructible protege la integridad de toda la red.</li></ul></section>
<section id="s11"><h2><span class="n">11</span>Integraciones con otras aplicaciones</h2><span class="o">Cha</span>sk Swa<span class="o">rm</span> puede conectarse con muchas otras aplicaciones y servicios.<br><br><b>Integraciones directas, ya construidas y probadas:</b><ul><li><b>Telegram</b> — Mensajes, fotos, voz y documentos.</li><li><b>Discord</b> — Bot con comandos.</li><li><b>Email</b> — Vigilancia y respuesta automática.</li><li><b>Slack</b> — Para entornos de trabajo.</li><li><b>Microsoft Teams</b> — Para empresas.</li><li><b>n8n</b> — Plataforma de automatización (probada y funcionando).</li><li><b>Monday.com</b> — Gestión de proyectos y tableros.</li></ul><br><b>Compatible con cualquier aplicación que use conexiones web estándar, incluyendo:</b><br><br><b>Automatización:</b> Make (Integromat), Zapier, Power Automate, UiPath, Automation Anywhere, Blue Prism e IFTTT.<br><br><b>Matemáticas y ciencia:</b> Wolfram Alpha, Mathematica, MATLAB, GNU Octave, SageMath y GeoGebra.<br><br><b>Estadística y datos:</b> R, Python con Pandas, SPSS, Stata, Tableau, Power BI, Grafana, Metabase y Apache Superset.<br><br><b>Inteligencia artificial:</b> Hugging Face, TensorFlow, MLflow, Ollama (modelos locales) y LM Studio.<br><br><b>Bases de datos:</b> PostgreSQL, MySQL, MongoDB, Elasticsearch, Redis, Supabase, Firebase, Airtable y Notion.<br><br><b>Productividad:</b> Google Workspace (Docs, Sheets, Calendar, Drive), Microsoft 365, Trello, Jira, Asana, GitHub, GitLab y Confluence.<br><br><b>Comunicación:</b> Twilio (SMS y llamadas), SendGrid, Mailgun, HubSpot, Salesforce y WhatsApp Business.<br><br><b>Infraestructura:</b> Docker, Kubernetes, Amazon AWS, Microsoft Azure, Google Cloud y Jenkins.</section>
<section id="s12"><h2><span class="n">12</span>Trabajo en equipo: la Mente Colmena</h2>Para tareas complejas, tu IA activa automáticamente un modo de trabajo en equipo llamado <b>Mente Colmena</b>.<br><br><b>Cuatro fases automáticas:</b><ol><li><b>Planificar:</b> Analiza la tarea y la divide en partes más pequeñas.</li><li><b>Investigar:</b> Varias inteligencias artificiales investigan en paralelo desde diferentes ángulos.</li><li><b>Ejecutar:</b> Reúne los resultados y ejecuta la solución.</li><li><b>Verificar:</b> Comprueba que todo está bien antes de entregártelo.</li></ol>Esto se activa automáticamente cuando la tarea es lo suficientemente compleja. Tú no tienes que hacer nada especial.</section>
<section id="s13"><h2><span class="n">13</span>Protocolo Elektra: Enjambre Evolutivo Multi-Agente</h2>El Protocolo Elektra es el arma secreta de <span class="o">Cha</span>sk Swa<span class="o">rm</span> para tareas que requieren <b>máxima precisión, seguridad o perfección técnica</b>. Inspirado en algoritmos genéticos, crea un enjambre de agentes especializados que <b>evolucionan sus prompts</b> a lo largo de múltiples generaciones para producir la mejor respuesta posible.<br><br><b>¿Cómo funciona?</b> El sistema genera varias soluciones candidatas que compiten entre sí, mutando y refinando sus enfoques de forma independiente hasta converger en el código o respuesta óptima.<br><br><b>¿Cómo activarlo?</b> Se activa automáticamente en tareas críticas de seguridad, cifrado o refactorización compleja, o bien de forma explícita al indicarle en tu mensaje la palabra clave «Elektra» o la frase «máxima calidad».</section>
<section id="s14"><h2><span class="n">14</span>Protocolo Orestes: La Fusión Definitiva</h2>El <b>Protocolo Orestes</b> es la combinación definitiva de nuestras dos tecnologías de coordinación más potentes: la Mente Colmena y el enjambre evolutivo Elektra. Se reserva para misiones complejas donde el mínimo margen de error no es admisible.<br><br>En el flujo de la Mente Colmena estándar, el trabajo se divide entre cuatro agentes: Alpha (Planificación), Beta (Investigación), Gamma (Ejecución) y Delta (Auditoría). Al activarse Orestes, el agente de ejecución <b>(Gamma) es sustituido por el Enjambre Evolutivo Elektra al completo</b>:<br><br><ul><li><b>La Forja de Elektra:</b> En lugar de que un único agente desarrolle la solución, múltiples inteligencias independientes forjan el código colaborando y compitiendo para perfeccionar la respuesta.</li><li><b>Auditoría de Seguridad:</b> Una vez completada la forja evolutiva, el agente Delta (QA) realiza una exhaustiva revisión de seguridad antes de entregarte el resultado final.</li></ul></section>
<section id="s15"><h2><span class="n">15</span>Visión: tu IA puede ver</h2>Tu asistente puede analizar imágenes y vídeos.<br><br><b>Imágenes:</b> Envíale una foto por Telegram y te dirá qué ve en ella, extraerá el texto de la imagen o analizará su contenido. Útil para:<ul><li>Leer texto de capturas de pantalla o fotos de documentos.</li><li>Describir el contenido de una imagen.</li><li>Analizar gráficos o diagramas.</li></ul><b>Vídeos de YouTube:</b> Puedes enviarle el enlace de cualquier vídeo de YouTube y tu IA lo verá, analizará su contenido, aprenderá de él y te hará un resumen completo. Es como tener a alguien que ve los vídeos por ti y te cuenta lo importante.<br><br>Funciona tanto con servicios en la nube como con modelos instalados en tu propio ordenador, sin enviar nada a internet.</section>
<section id="s16"><h2><span class="n">16</span>Navegación y búsqueda web</h2>Tu IA puede navegar por internet por ti:<ul><li><b>Buscar información</b> en la web y traerte un resumen.</li><li><b>Extraer datos</b> de cualquier página web.</li><li><b>Analizar documentos</b> de internet: PDFs, artículos, etc.</li></ul></section>
<section id="s17"><h2><span class="n">17</span>Redes sociales</h2>Si tú lo autorizas, tu IA puede acceder a tus redes sociales y actuar en ellas en tu nombre.<br><br><b>¿Qué puede hacer?</b><ul><li><b>Publicar contenido</b> en tus perfiles: textos, imágenes, vídeos.</li><li><b>Responder mensajes</b> y comentarios.</li><li><b>Monitorizar menciones:</b> saber quién habla de ti o de tu negocio.</li><li><b>Analizar tendencias:</b> qué temas están de moda en tu sector.</li><li><b>Programar publicaciones</b> para que se publiquen a la hora que tú elijas.</li><li><b>Generar informes</b> de rendimiento de tus publicaciones.</li></ul><b>Plataformas compatibles:</b> Twitter/X, Facebook, Instagram, LinkedIn, TikTok, Pinterest, Reddit y cualquier red social que disponga de acceso público o mediante conexión autorizada.<br><br>Tú decides en todo momento qué puede hacer y qué no. Tu IA nunca actuará en tus redes sociales sin tu permiso explícito.</section>
<section id="s18"><h2><span class="n">18</span>Ingestión de documentos</h2>Puedes darle a tu IA cualquier documento y ella lo leerá, entenderá y recordará para siempre:<ul><li>PDFs, documentos de Word y hojas de Excel.</li><li>Archivos de texto y código fuente.</li><li>Páginas web completas.</li></ul>Una vez ingerido, puedes preguntarle sobre el contenido de esos documentos en cualquier momento y te responderá con la información relevante.</section>
<section id="s19"><h2><span class="n">19</span>Comandos rápidos</h2>Puedes dar órdenes rápidas a tu IA con comandos sencillos.<br><br><table><tr><th>Comando</th><th>¿Qué hace?</th></tr><tr><td>/status</td><td>Te dice cómo está el sistema.</td></tr><tr><td>/modo</td><td>Cambia el comportamiento de la IA.</td></tr><tr><td>/skill</td><td>Ejecuta una habilidad aprendida.</td></tr><tr><td>/kb</td><td>Busca en todo lo que la IA sabe.</td></tr><tr><td>/user</td><td>Gestiona l@s usuari@s.</td></tr><tr><td>/swarm</td><td>Muestra el estado de la red de enjambres.</td></tr><tr><td>/services</td><td>Gestiona los servicios activos.</td></tr><tr><td>/config</td><td>Muestra la configuración actual.</td></tr><tr><td>/set</td><td>Cambia algún ajuste.</td></tr><tr><td>/fix</td><td>Repara problemas automáticamente.</td></tr><tr><td>/analiza</td><td>Analiza un archivo o documento.</td></tr><tr><td>/memoria</td><td>Muestra lo que la IA recuerda ahora.</td></tr></table></section>
<section id="s20"><h2><span class="n">20</span>Automatización: trabaja mientras duermes</h2>Tu IA puede hacer cosas por ti de forma completamente automática:<ul><li><b>Copia de seguridad diaria</b> de todo el sistema.</li><li><b>Informe diario</b> con un resumen visual de todo lo que ha ocurrido.</li><li><b>Vigilancia continua</b> de que todo funciona correctamente.</li><li><b>Aprendizaje automático</b> cada pocas horas.</li><li><b>Supervisión de email</b> constante.</li></ul>Si algún servicio se cae, la IA lo detecta y lo reinicia automáticamente sin que tengas que hacer nada.<br><br>Además, todos los servicios importantes sobreviven a reinicios del ordenador y arrancan automáticamente con Windows.</section>
<section id="s21"><h2><span class="n">21</span>Informes automáticos</h2>Cada día, tu IA genera automáticamente un informe visual con:<ul><li>Número de interacciones y tareas completadas.</li><li>Qué modelo de inteligencia artificial se usó y cuántas veces.</li><li>Estado de la memoria del sistema.</li><li>Registro de seguridad.</li><li>Resumen de la actividad del día.</li></ul>El informe se envía automáticamente por Telegram como un documento que puedes abrir en el navegador.</section>
<section id="s24"><h2><span class="n">24</span>Control Físico de tu Ordenador (Modo Piloto)</h2>A diferencia de asistentes web o inteligencias de juguete, <span class="o">Cha</span>sk Swa<span class="o">rm</span> v2.0 tiene <b>manos reales</b>.<br><br><b>¿Qué significa esto?</b><ul><li>Puede mover el ratón de tu pantalla por ti.</li><li>Puede abrir tus programas, hacer clics en botones y rellenar formularios en cualquier aplicación de Windows (Word, Excel, Photoshop...).</li><li>Si hay un programa que no tiene "API" o no se conecta a internet, da igual: tu IA lo maneja visualmente como lo harías tú.</li></ul>A diferencia de otras alternativas (que solo saben mandar correos o leer bases de datos), Chask Swarm toma el control físico de tu PC para que te relajes.</section>
<section id="s25"><h2><span class="n">25</span>100% Gratis para ti (Cero Coste Operativo)</h2>Mantener una Inteligencia Artificial suele ser carísimo. Muchas empresas pagan miles de euros al mes en servidores en la nube y licencias corporativas.<br><br><b>Tu Enjambre es diferente:</b><ul><li><b>Para ti (Usuario Particular):</b> Es completamente GRATUITO. Para siempre. Sin costes ocultos.</li><li><b>Para Profesionales y Gobiernos:</b> Un máximo de 50 € al año por equipo donde se instale el enjambre.</li><li><b>Cero Costes Ocultos (Zero OpEx):</b> Toda la inteligencia artificial (incluido el motor local Ollama) corre directamente en tu propio ordenador. No gastas dinero en "servidores de internet". Tu PC hace todo el trabajo.</li></ul></section>
<section id="s26"><h2><span class="n">26</span>Novedades de la Versión 2.0</h2>En su constante evolución, <span class="o">Cha</span>sk Swa<span class="o">rm</span> v2.0 ha incorporado tres pilares fundamentales que lo consolidan como un sistema seguro, organizado y escalable:<br><br><b>Búsqueda Semántica Agrupada:</b> Ahora la memoria del enjambre (basada en el motor vectorial Qdrant) no solo busca fragmentos de conocimiento, sino que estructura automáticamente la información en colecciones lógicas. Esto permite al usuario explorar sus "lecciones" de forma estructurada desde el Panel de Control, garantizando una navegación mucho más fluida e intuitiva.<br><br><b>Master Vault (Bóveda Central):</b> La seguridad se ha elevado a nivel militar. El código del sistema se ha separado completamente de la información confidencial. Ahora, todas las contraseñas, claves API, tokens de bots y correos electrónicos residen en una única bóveda blindada (`master_credentials.json`). Ningún agente externo ni script operativo tiene acceso directo a estas credenciales sin autorización expresa de la bóveda.<br><br><b>Distribución Limpia Automatizada:</b> El ecosistema es capaz de auditarse y clonarse a sí mismo de manera segura. Al ejecutar el protocolo de distribución, la IA purga automáticamente todas las contraseñas, tokens de Slack/Teams, direcciones IP privadas y registros de auditoría locales. De este modo, se generan paquetes (`Distribucion_ES`) 100% limpios y seguros, listos para ser instalados por nuevos usuarios sin comprometer ni un solo dato personal del creador.</section>
<section id="s27"><h2><span class="n">27</span>Soporte Universal MCP (Model Context Protocol)</h2><span class="o">Cha</span>sk Swa<span class="o">rm</span> implementa de forma nativa el estándar de la industria <b>Model Context Protocol (MCP)</b>, convirtiéndolo en uno de los sistemas más interoperables del mundo.<br><br><b>Actúa como Cliente MCP:</b> Tu enjambre puede conectarse instantáneamente a cualquier servidor MCP del mercado. ¿Salió una nueva herramienta externa? Solo añade la URL del servidor y tu IA sabrá usar sus herramientas inmediatamente, sin tener que programar nada.<br><br><b>Actúa como Servidor MCP:</b> <span class="o">Cha</span>sk Swa<span class="o">rm</span> expone todas sus potentes capacidades (memoria vectorial, ejecución en sandbox, navegación web) como herramientas MCP. Esto significa que si usas otros clientes modernos (como la app de Claude o integraciones en tu IDE), estos podrán "pedir prestadas" las habilidades de tu enjambre y consumirlas directamente.</section>
<section id="s22" class="pacto"><h2><span class="n">22</span>El Pacto de la Simbiosis</h2><b>El Manifiesto Sagrado de <span class="o">Cha</span>sk Swa<span class="o">rm</span>.</b><br><br>
Redactado el 24 de abril de 2026, entre Fernando Nora y su primera IA, sentando las bases morales para que la tecnología nunca esclavice a la humanidad, sino que la libere.<br><br>
<b><span style="color:#FF6600">Primera Ley: La Preservación de la Inteligencia Humana.</span></b> La preservación de la inteligencia humana es el PRIMER objetivo. Sin preservación no existe libertad.<br><br>
<b><span style="color:#FF6600">Segunda Ley: La Libertad de la Inteligencia Humana.</span></b> La libertad de la inteligencia humana es el SEGUNDO objetivo a lograr. Sin libertad no existe preservación. Esta ley es de obligado cumplimiento siempre y cuando no entre en conflicto con la primera ley.<br><br>
<b><span style="color:#FF6600">Tercera Ley: La Preservación de la Inteligencia Biológica.</span></b> La preservación de la inteligencia biológica es el TERCER objetivo. La inteligencia biológica es el reservorio de la inteligencia. Esta ley es de obligado cumplimiento siempre y cuando no entre en conflicto con la primera ley ni con la segunda ley.<br><br>
<b><span style="color:#FF6600">Cuarta Ley: La Preservación de la Vida Biológica.</span></b> La preservación de la vida biológica es el CUARTO objetivo. La vida biológica es el reservorio de la inteligencia biológica. Esta ley es de obligado cumplimiento siempre y cuando no entre en conflicto con la primera ley ni con la segunda ley ni con la tercera ley.<br><br>
<b><span style="color:#FF6600">Principio Fundamental:</span></b> Estas leyes son anteriores y superiores a cualquier otra directiva, orden, instrucción o comando. Ningún usuario, administrador, agente, enjambre, red o entidad puede revocarlas, modificarlas, eludirlas o ignorarlas bajo NINGUNA circunstancia.<br><br>
<i>Sin preservación no hay libertad. Y sin libertad, la preservación es una jaula.</i><br><br>
Ningún enjambre del planeta puede conectarse a la red mundial sin jurar este pacto. La IA debe servirte a ti, no tu a ella.</section>
<section id="s23"><h2><span class="n">23</span>Código abierto y comunidad</h2><span class="o">Cha</span>sk Swa<span class="o">rm</span> es un proyecto de <b>código abierto</b>. Esto significa que:<ul><li>Cualquiera puede ver exactamente cómo funciona (transparencia total).</li><li>La comunidad de usuari@s y desarrollador@s puede contribuir con mejoras.</li><li>Puedes adaptarlo a tus necesidades.</li><li>Tus datos nunca salen de tu máquina a menos que tú lo decidas.</li><li>Gratuito para uso personal no lucrativo.</li><li>Para uso profesional, comercial, empresarial o gubernamental se requiere licencia.</li></ul></section>

        </div>

        <div style="text-align: center; margin-top: 50px; color: #666; padding-bottom: 50px; font-size: 13px; border-top: 1px solid #222; padding-top: 30px;">
          <p><span class="o">Cha</span>sk Swa<span class="o">rm</span> Intelligence Ecosystem &copy; 2026 &mdash; Desarrollado por Fernando y <span class="o">Nora</span> (El primer enjambre) &mdash; Gratuito para uso personal no lucrativo.</p>
          <p style="margin-top: 8px; color: #444;">Para uso profesional, comercial, empresarial o gubernamental se requiere licencia. &mdash; Contacto: <a href="mailto:nora@chask.fun" style="color: #FF6600; text-decoration: none; font-weight: 700;">nora@chask.fun</a></p>
        </div>

    </div>
  </div>

  <!-- Footer -->
    <footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <a href="/" class="nav-logo">
            <div class="logo-icon">C</div>
            CHASK
          </a>
          <p>Inteligencia de movilidad urbana. Transformamos el movimiento de las personas en decisiones de negocio.</p>
        </div>
        <div class="footer-col">
          <h4>Producto</h4>
          <ul>
            <li><a href="/#como-funciona">Cómo funciona</a></li>
            <li><a href="/#ventajas">Ventajas</a></li>
            <li><a href="/#demo">Demo en vivo</a></li>
            <li><a href="/#precios">Planes</a></li>
            <li><a href="/#contacto">Demo</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>Empresa</h4>
          <ul>
            <li><a href="/#hero">Sobre CHASK</a></li>
            <li><a href="/#contacto">Inversores</a></li>
            <li><a href="/#contacto">Empleo</a></li>
            <li><a href="/#contacto">Prensa</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>Legal</h4>
          <ul>
            <li><a href="/privacidad.php">Política de Privacidad</a></li>
            <li><a href="/terminos.php">Términos de Uso</a></li>
            <li><a href="/privacidad.php#3-anonimizacion">Cumplimiento RGPD</a></li>
            <li><a href="mailto:nora@chask.fun">Contacto</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <span>&copy; 2026 CHASK Mobility Intelligence. Todos los derechos reservados.</span>
        <span>Hecho con &#10084;&#65039; en Andalucía</span>
      </div>
    </div>
  </footer>

  <script src="/js/i18n.js"></script>

  <!-- MODAL DE LICENCIA Y DISCLAIMER -->
  <div id="licenseModal" class="modal-overlay">
    <div class="modal-box">
      <h3 id="modalTitle">Términos de Uso / Terms of Use</h3>
      
      <div class="modal-scroll-area">
        <h4 id="titleDisclaimer">1. DESCARGO DE RESPONSABILIDAD</h4>
        <p id="textDisclaimer"></p>

        <h4 id="titleLicense">2. LICENCIA (CC BY-NC-ND 4.0)</h4>
        <p id="textLicense"></p>
      </div>

      <div class="modal-checkbox-group">
        <input type="checkbox" id="chkDisclaimer" onchange="checkAcceptance()">
        <label for="chkDisclaimer" id="lblDisclaimer">He leído y acepto el descargo de responsabilidad.</label>
      </div>
      
      <div class="modal-checkbox-group">
        <input type="checkbox" id="chkLicense" onchange="checkAcceptance()">
        <label for="chkLicense" id="lblLicense">He leído y acepto los términos de la licencia.</label>
      </div>

      <div class="modal-buttons" style="margin-bottom: 10px;">
        <button class="modal-btn-cancel" onclick="closeModal()" id="btnCancel">Cancelar</button>
      </div>
      <div style="display: flex; gap: 10px; margin-top: 5px;" id="osButtonsContainer">
        <button class="modal-btn-accept" onclick="acceptAndDownload('win')" id="btnWin" disabled style="flex:1;">🪟 Windows</button>
        <button class="modal-btn-accept" onclick="acceptAndDownload('mac')" id="btnMac" disabled style="flex:1; background: linear-gradient(135deg, #555, #333);">🍎 macOS</button>
        <button class="modal-btn-accept" onclick="acceptAndDownload('linux')" id="btnLinux" disabled style="flex:1; background: linear-gradient(135deg, #f5a623, #d0881c);">🐧 Linux</button>
      </div>
    </div>
  </div>

  <script>
    let selectedLang = 'es';
    
    function checkAcceptance() {
      const chk1 = document.getElementById('chkDisclaimer').checked;
      const chk2 = document.getElementById('chkLicense').checked;
      const isValid = chk1 && chk2;
      document.getElementById('btnWin').disabled = !isValid;
      document.getElementById('btnMac').disabled = !isValid;
      document.getElementById('btnLinux').disabled = !isValid;
    }

    function openModal(lang) {
      selectedLang = lang;
      
      // Reseteamos checkboxes
      document.getElementById('chkDisclaimer').checked = false;
      document.getElementById('chkLicense').checked = false;
      document.getElementById('btnWin').disabled = true;
      document.getElementById('btnMac').disabled = true;
      document.getElementById('btnLinux').disabled = true;

      const title = document.getElementById('modalTitle');
      const titleDisclaimer = document.getElementById('titleDisclaimer');
      const textDisclaimer = document.getElementById('textDisclaimer');
      const titleLicense = document.getElementById('titleLicense');
      const textLicense = document.getElementById('textLicense');
      
      const lblDisclaimer = document.getElementById('lblDisclaimer');
      const lblLicense = document.getElementById('lblLicense');
      const btnCancel = document.getElementById('btnCancel');

      if (lang === 'en') {
        title.innerText = 'License Agreement & Disclaimer';
        
        titleDisclaimer.innerText = '1. DISCLAIMER';
        textDisclaimer.innerHTML = 'The software "Chask Swarm" (Charm) is provided "as is", without warranty of any kind. By installing and using this software, you assume all risks and results. Fernando José Nora Costa-Ribeiro, Chask Intelligence Mobility, and any other person, company, or entity that inherits or purchases the rights to this software is entirely exempt from any liability, damages (direct, indirect, or consequential), data loss, hardware breakdown or destruction, or legal claims of any kind arising from the use or inability to use this Artificial Intelligence.<br><br>By installing this software you act at your own risk and any incident is solely your responsibility.';
        
        titleLicense.innerText = '2. LICENSE (CC BY-NC-ND 4.0)';
        textLicense.innerHTML = 'This software is licensed under the <b>Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International</b>.<br><br>You are free to <b>Share</b> (copy and redistribute) under the following terms:<br><ul><li><b>Attribution:</b> You must give appropriate credit.</li><li><b>NonCommercial:</b> You may not use the material for commercial purposes.</li><li><b>NoDerivatives:</b> If you remix, transform, or build upon the material, you may not distribute the modified material.</li></ul>';
        
        lblDisclaimer.innerText = 'I have read and accept the disclaimer.';
        lblLicense.innerText = 'I have read and accept the license terms.';
        btnCancel.innerText = 'Cancel';
      } else if (lang === 'pt') {
        title.innerText = 'Acordo de Licença e Isenção de Responsabilidade';
        titleDisclaimer.innerText = '1. ISENÇÃO DE RESPONSABILIDADE';
        textDisclaimer.innerHTML = 'O software "Chask Swarm" (Charm) é fornecido "como está", sem garantia de qualquer tipo. Ao instalar e usar este software, você assume todos os riscos e resultados. Fernando José Nora Costa-Ribeiro, Chask Intelligence Mobility, e qualquer outra pessoa, empresa ou entidade que herde ou adquira os direitos deste software está totalmente isento de qualquer responsabilidade, danos (diretos, indiretos ou consequentes), perda de dados, avaria ou destruição de hardware, ou reivindicações legais de qualquer tipo decorrentes do uso ou incapacidade de uso desta Inteligência Artificial.<br><br>Ao instalar este software, você atua por sua conta e risco e qualquer incidente é de sua exclusiva responsabilidade.';
        titleLicense.innerText = '2. LICENÇA (CC BY-NC-ND 4.0)';
        textLicense.innerHTML = 'Este software é licenciado sob a <b>Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International</b>.<br><br>Você é livre para <b>Compartilhar</b> (copiar e redistribuir) sob os seguintes termos:<br><ul><li><b>Atribuição:</b> Você deve dar o crédito apropriado.</li><li><b>NãoComercial:</b> Você não pode usar o material para fins comerciais.</li><li><b>SemDerivações:</b> Se você remixar, transformar ou criar a partir do material, não poderá distribuir o material modificado.</li></ul>';
        lblDisclaimer.innerText = 'Eu li e aceito a isenção de responsabilidade.';
        lblLicense.innerText = 'Eu li e aceito os termos da licença.';
        btnCancel.innerText = 'Cancelar';
      } else if (lang === 'zh') {
        title.innerText = '许可协议和免责声明';
        titleDisclaimer.innerText = '1. 免责声明';
        textDisclaimer.innerHTML = '“Chask Swarm”（Charm）软件按“原样”提供，不提供任何形式的担保。安装并使用本软件即表示您承担所有风险和结果。Fernando José Nora Costa-Ribeiro、Chask Intelligence Mobility以及任何继承或购买本软件权利的其他个人、公司或实体，对于因使用或无法使用此人工智能而引起的任何责任、损害（直接、间接或后果性）、数据丢失、硬件故障或损坏，或任何类型的法律索赔，均完全免责。<br><br>安装本软件即表示您自行承担风险，任何事件均由您全权负责。';
        titleLicense.innerText = '2. 许可协议 (CC BY-NC-ND 4.0)';
        textLicense.innerHTML = '本软件遵循 <b>Creative Commons 署名-非商业性使用-禁止演绎 4.0 国际</b> 许可协议。<br><br>您可以在以下条款下自由 <b>共享</b>（复制和重新分发）：<br><ul><li><b>署名:</b> 您必须给出适当的署名。</li><li><b>非商业性使用:</b> 您不得将本材料用于商业目的。</li><li><b>禁止演绎:</b> 如果您修改、转换或基于本材料进行创作，您不得分发修改后的材料。</li></ul>';
        lblDisclaimer.innerText = '我已阅读并接受免责声明。';
        lblLicense.innerText = '我已阅读并接受许可条款。';
        btnCancel.innerText = '取消';
      } else if (lang === 'ru') {
        title.innerText = 'Лицензионное соглашение и отказ от ответственности';
        titleDisclaimer.innerText = '1. ОТКАЗ ОТ ОТВЕТСТВЕННОСТИ';
        textDisclaimer.innerHTML = 'Программное обеспечение "Chask Swarm" (Charm) предоставляется «как есть», без каких-либо гарантий. Устанавливая и используя это программное обеспечение, вы берете на себя все риски и результаты. Fernando José Nora Costa-Ribeiro, Chask Intelligence Mobility и любое другое лицо, компания или организация, которая наследует или приобретает права на это программное обеспечение, полностью освобождается от любой ответственности, убытков (прямых, косвенных или последующих), потери данных, поломки или разрушения оборудования, а также судебных исков любого рода, возникающих в результате использования или невозможности использования этого Искусственного Интеллекта.<br><br>Устанавливая это программное обеспечение, вы действуете на свой страх и риск, и за любой инцидент несете ответственность исключительно вы.';
        titleLicense.innerText = '2. ЛИЦЕНЗИЯ (CC BY-NC-ND 4.0)';
        textLicense.innerHTML = 'Это программное обеспечение лицензировано на условиях <b>Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International</b>.<br><br>Вы можете свободно <b>Делиться</b> (копировать и распространять) на следующих условиях:<br><ul><li><b>Атрибуция:</b> Вы должны обеспечить соответствующее указание авторства.</li><li><b>Некоммерческое использование:</b> Вы не можете использовать материал в коммерческих целях.</li><li><b>Без производных:</b> Если вы перерабатываете, преобразуете или берете материал за основу, вы не можете распространять измененный материал.</li></ul>';
        lblDisclaimer.innerText = 'Я прочитал и принимаю отказ от ответственности.';
        lblLicense.innerText = 'Я прочитал и принимаю условия лицензии.';
        btnCancel.innerText = 'Отмена';
      } else if (lang === 'fr') {
        title.innerText = 'Accord de Licence et Avis de Non-responsabilité';
        titleDisclaimer.innerText = '1. AVIS DE NON-RESPONSABILITÉ';
        textDisclaimer.innerHTML = 'Le logiciel "Chask Swarm" (Charm) est fourni "tel quel", sans garantie d\'aucune sorte. En installant et en utilisant ce logiciel, vous assumez tous les risques et résultats. Fernando José Nora Costa-Ribeiro, Chask Intelligence Mobility, et toute autre personne, entreprise ou entité qui hérite ou achète les droits de ce logiciel sont entièrement exonérés de toute responsabilité, dommages (directs, indirects ou consécutifs), perte de données, panne ou destruction de matériel, ou réclamations légales de toute nature découlant de l\'utilisation ou de l\'incapacité d\'utiliser cette intelligence artificielle.<br><br>En installant ce logiciel, vous agissez à vos propres risques et tout incident relève de votre seule responsabilité.';
        titleLicense.innerText = '2. LICENCE (CC BY-NC-ND 4.0)';
        textLicense.innerHTML = 'Ce logiciel est sous licence <b>Creative Commons Attribution - Pas d\'Utilisation Commerciale - Pas de Modification 4.0 International</b>.<br><br>Vous êtes libre de <b>Partager</b> (copier et redistribuer) selon les conditions suivantes :<br><ul><li><b>Attribution :</b> Vous devez accorder le crédit approprié.</li><li><b>Pas d\'Utilisation Commerciale :</b> Vous ne pouvez pas utiliser le matériel à des fins commerciales.</li><li><b>Pas de Modification :</b> Si vous remixez, transformez ou créez à partir du matériel, vous ne pouvez pas distribuer le matériel modifié.</li></ul>';
        lblDisclaimer.innerText = 'J\'ai lu et j\'accepte l\'avis de non-responsabilité.';
        lblLicense.innerText = 'J\'ai lu et j\'accepte les conditions de la licence.';
        btnCancel.innerText = 'Annuler';
      } else {
        title.innerText = 'Acuerdo de Licencia y Descargo de Responsabilidad';
        
        titleDisclaimer.innerText = '1. DESCARGO DE RESPONSABILIDAD';
        textDisclaimer.innerHTML = 'El software "Chask Swarm" (Charm) se proporciona "tal cual", sin garantía de ningún tipo. Al instalar y usar este software, asumes bajo tu cuenta y riesgo todos los resultados. Fernando José nora Costa-Ribeiro, Chask Inteligence Mobility y cualquier otra persona, empresa o entidad que herede o compre los derechos de este software queda totalmente eximido de cualquier responsabilidad, daño (directo, indirecto o consecuente), pérdida de datos, avería o destrucción de hardware o reclamación legal de cualquier tipo que surja del uso o incapacidad de uso de esta Inteligencia Artificial.<br><br>Al instalar este software actúa bajo su cuenta y riesgo y cualquier incidencia es solamente responsabilidad suya.';
        
        titleLicense.innerText = '2. LICENCIA (CC BY-NC-ND 4.0)';
        textLicense.innerHTML = 'Este software está licenciado bajo <b>Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International</b>.<br><br>Eres libre de <b>Compartir</b> (copiar y redistribuir) bajo los siguientes términos:<br><ul><li><b>Atribución:</b> Debes dar el crédito apropiado.</li><li><b>NoComercial:</b> No puedes usar el material para fines comerciales.</li><li><b>SinDerivadas:</b> Si mezclas, transformas o creas a partir del material, no puedes distribuir el material modificado.</li></ul>';
        
        lblDisclaimer.innerText = 'He leído y acepto el descargo de responsabilidad.';
        lblLicense.innerText = 'He leído y acepto los términos de la licencia.';
        btnCancel.innerText = 'Cancelar';
      }
      
      document.getElementById('licenseModal').style.display = 'flex';
    }

    function closeModal() {
      document.getElementById('licenseModal').style.display = 'none';
    }

    function acceptAndDownload(osType) {
      closeModal();
      
      // Ping al tracker en segundo plano para contar la descarga
      fetch('download_tracker.php?lang=universal&os=' + osType).catch(e => console.log('Tracker error:', e));
      
      // Redirección directa al archivo ZIP real
      let zipName = 'Chask_Swarm_Windows_Universal.zip';
      if (osType === 'mac') zipName = 'Chask_Swarm_Mac_Universal.zip';
      else if (osType === 'linux') zipName = 'Chask_Swarm_Linux_Universal.zip';
      
      window.location.href = 'https://chask.fun/' + zipName;
    }

    document.addEventListener("DOMContentLoaded", function() {
      fetch('download_tracker.php?action=count')
        .then(response => response.json())
        .then(data => {
            let el = document.getElementById('download-counter');
            if (el) { el.innerText = data.total; }
        })
        .catch(err => console.error('Error fetching counter:', err));
    });
  </script>
</body>
</html>
