<?php header('Content-Type: text/html; charset=UTF-8'); ?>
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CHASK Traffic App &mdash; Mapea la ciudad y gana dinero</title>
  <meta name="description" content="Descarga la App de Tráfico de CHASK, enciende el mapa mientras conduces y recibe recompensas por mapear el tráfico en tiempo real.">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#x1F697;</text></svg>">
  <link rel="stylesheet" href="css/styles.css">
  <style>
    .gallery {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 20px;
      margin-top: 40px;
    }
    .gallery img {
      width: 100%;
      border-radius: 16px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
      border: 1px solid rgba(99,102,241,0.2);
      transition: transform 0.3s;
    }
    .gallery img:hover {
      transform: translateY(-5px);
    }
    .dl-buttons {
      display: flex;
      gap: 15px;
      justify-content: center;
      margin-top: 30px;
      flex-wrap: wrap;
    }
  </style>
</head>
<body>

  <!-- Background Effects -->
  <div class="bg-grid"></div>
  <div class="bg-orbs">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
  </div>

  <!-- Navigation -->
  <?php include 'header.php'; ?>

  <!-- Hero Section for Traffic App -->
  <section class="hero" style="padding-top: 140px; padding-bottom: 60px;">
    <div class="container">
      <div class="hero-content" style="text-align: center; max-width: 800px; margin: 0 auto;">
        <div class="hero-badge" style="margin: 0 auto 20px auto;">
          <span class="pulse"></span>
          Versión Beta Abierta
        </div>
        <h1>Conduce. Mapea. <span class="text-gradient">Gana.</span></h1>
        <p style="font-size: 1.2rem; margin-top: 20px;">Únete a la red descentralizada de tráfico de CHASK. Activa la app mientras conduces y ayúdanos a mapear los patrones de movilidad urbana de tu ciudad.</p>
        
        <div class="dl-buttons" id="descargar">
          <a href="swarm.php" class="btn-primary" style="background: linear-gradient(135deg, #f97316, #ea580c); margin-bottom: 10px;">
            &#x1F41D; Chask Swarm &rarr;
          </a>
          <a href="/downloads/chask_traffik.apk" class="btn-primary" download>
            &#x1F4F1; Descargar para Android (.apk)
          </a>
          <a href="#" class="btn-secondary" onclick="alert('La versión para iPhone estará disponible pronto.'); return false;">
            &#x1F34E; Descargar para iPhone (.ipa)
          </a>
        </div>
      </div>
    </div>
  </section>

  <!-- Features & User Manual -->
  <section class="section" style="background: rgba(99,102,241,0.02); border-top: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05);">
    <div class="container">
      
      <div class="section-header reveal">
        <span class="section-label">Transparencia Total</span>
        <h2>Privacidad y <span class="text-gradient">Recogida de Datos</span></h2>
      </div>
      <div class="reveal" style="max-width: 800px; margin: 0 auto 60px auto; color: #94a3b8; line-height: 1.8;">
        <p>En CHASK Traffik, tu privacidad es nuestra prioridad absoluta. Hemos diseñado un sistema que aporta gran valor a la comunidad sin comprometer tu identidad:</p>
        <ul style="margin-top: 15px; padding-left: 20px;">
          <li style="margin-bottom: 10px;"><strong>Recogida en Segundo Plano (Cada 15 min):</strong> Para minimizar el consumo de batería y proteger tu rutina, la aplicación recoge una posición silenciosa cada 15 minutos cuando la llevas cerrada en el bolsillo.</li>
          <li style="margin-bottom: 10px;"><strong>Estadísticas Anonimizadas:</strong> No guardamos tu nombre ni datos que te identifiquen con una posición exacta. Únicamente se almacena el rango de edad y género para crear reportes estadísticos macroscópicos.</li>
          <li style="margin-bottom: 10px;"><strong>Retención de Datos:</strong> La información analítica se almacena por un periodo estricto de <strong>un año</strong>, tras el cual se purga automáticamente de nuestros servidores.</li>
        </ul>
      </div>

      <div class="section-header reveal">
        <span class="section-label">Aprende a usarla</span>
        <h2>Manual de <span class="text-gradient">Usuario</span></h2>
      </div>
      
      <div class="features-grid reveal" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; max-width: 1000px; margin: 0 auto;">
        
        <div class="feature-card" style="background: #111116; padding: 30px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05);">
          <div class="feature-icon" style="font-size: 2rem; margin-bottom: 15px;">&#x1F6A6;</div>
          <h3 style="color: #fff; margin-bottom: 10px;">Leyenda de Velocidad (Colores)</h3>
          <p style="color: #94a3b8; font-size: 0.95rem; line-height: 1.6;">
            El color de los puntos en el mapa indica la <strong>velocidad media</strong> del tráfico en esa calle en tiempo real. 
            El servidor da prioridad a los usuarios activos para el cálculo de la velocidad.
          </p>
          <ul style="margin-top: 10px; padding-left: 20px; color: #94a3b8; font-size: 0.9rem;">
            <li><span style="color: lightgreen; font-weight: bold;">Verde:</span> Fluido (> 30 km/h)</li>
            <li><span style="color: yellow; font-weight: bold;">Amarillo:</span> Lento (> 15 km/h)</li>
            <li><span style="color: orange; font-weight: bold;">Naranja:</span> Retención (> 5 km/h)</li>
            <li><span style="color: red; font-weight: bold;">Rojo:</span> Atasco / Parado (0-5 km/h)</li>
          </ul>
        </div>

        <div class="feature-card" style="background: #111116; padding: 30px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05);">
          <div class="feature-icon" style="font-size: 2rem; margin-bottom: 15px;">&#x1F310;</div>
          <h3 style="color: #fff; margin-bottom: 10px;">Densidad de Tráfico (Tamaño)</h3>
          <p style="color: #94a3b8; font-size: 0.95rem; line-height: 1.6;">
            El <strong>tamaño</strong> del punto no significa que haya un coche muy grande. El tamaño indica el volumen de reportes en esa cuadrícula. Miden entre 5.0m y 7.5m reales para no tapar calles adyacentes. A mayor tamaño de punto, mayor número de usuarios concentrados en ese punto del mapa.
          </p>
        </div>

        <div class="feature-card" style="background: #111116; padding: 30px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05);">
          <div class="feature-icon" style="font-size: 2rem; margin-bottom: 15px;">&#x1F698;</div>
          <h3 style="color: #fff; margin-bottom: 10px;">Modo Conductor (GPS Activo)</h3>
          <p style="color: #94a3b8; font-size: 0.95rem; line-height: 1.6;">
            Si pones el teléfono en el salpicadero, puedes activar el <strong>Modo Conductor</strong> pulsando el botón flotante verde con forma de coche en la esquina superior derecha.<br><br>
            Esto activa el <em>Wakelock</em> (evita que la pantalla de tu móvil se apague sola por inactividad) y centra la cámara en tu posición, funcionando como un navegador tradicional.
          </p>
        </div>

      </div>
    </div>
  </section>

  <!-- Screenshots Gallery -->
  <section class="section">
    <div class="container">
      <div class="section-header reveal">
        <span class="section-label">Interfaz Simple y Oscura</span>
        <h2>Así se ve la <span class="text-gradient">App de Tráfico</span></h2>
      </div>
      <div class="gallery reveal">
        <img src="img/trafico/shot1.jpeg" alt="Captura 1" loading="lazy">
        <img src="img/trafico/shot2.jpeg" alt="Captura 2" loading="lazy">
        <img src="img/trafico/shot3.jpeg" alt="Captura 3" loading="lazy">
        <img src="img/trafico/shot4.jpeg" alt="Captura 4" loading="lazy">
      </div>
    </div>
  </section>

  <!-- Live Simulation Map -->
  <section class="section" style="background:rgba(99,102,241,0.03);">
    <div class="container">
      <div class="section-header reveal">
        <span class="section-label">&#x1F4CD; Simulación Activa</span>
        <h2>Mapa Base de <span class="text-gradient">Sevilla</span></h2>
        <p>A continuación se muestra el simulador de mapa de calor que utiliza la misma tecnología que desplegaremos cuando la aplicación de tráfico alcance una base suficiente de conductores activos.</p>
      </div>

      <!-- Map frames -->
      <div class="reveal" style="position:relative;border-radius:20px;overflow:hidden;
           border:1px solid rgba(99,102,241,0.2);box-shadow:0 24px 80px rgba(0,0,0,.5);
           background:#0a0a10;">
        <div style="position:absolute;top:16px;left:16px;z-index:10;
             display:flex;align-items:center;gap:7px;
             padding:6px 14px;border-radius:20px;
             background:rgba(245,158,11,.12);color:#f59e0b;
             border:1px solid rgba(245,158,11,.2);font-size:12px;font-weight:600;
             backdrop-filter:blur(8px);">
          SIMULACIÓN
        </div>
        <a id="demo-fullscreen" href="/trafico.php" target="_blank"
           style="position:absolute;top:16px;right:16px;z-index:10;
                  padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600;
                  text-decoration:none;background:rgba(99,102,241,0.15);color:#a5b4fc;
                  border:1px solid rgba(99,102,241,0.25);backdrop-filter:blur(8px);
                  transition:all .2s;">
          &#x26F6; Pantalla completa
        </a>
        <iframe id="demo-iframe-trafico"
          src="/trafico.php"
          style="width:100%;height:600px;border:none;display:block;"
          loading="lazy" title="CHASK Traffic — Simulación Tráfico Sevilla"></iframe>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <?php include 'footer.php'; ?>

  <script src="js/main.js"></script>
</body>
</html>
