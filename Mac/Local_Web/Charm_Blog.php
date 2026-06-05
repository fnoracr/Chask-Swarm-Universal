<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blog Oficial &mdash; Charm</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    /* Estilos base de charm.php */
    body {
      font-family: 'Outfit', sans-serif; 
      background-image: radial-gradient(circle at 50% 0%, rgba(255,102,0,0.1) 0%, #0a0a0f 100%); 
      background-color: #0a0a0f; 
      color: #e2e2ea; 
      line-height: 1.8; 
      margin: 0; 
      padding: 0; 
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    .o { color: #FF6600 !important; font-weight: 700; }
    .w { color: #FFFFFF !important; font-weight: 700; }
    
    /* Layout principal */
    .blog-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 40px 20px;
      display: flex;
      gap: 30px;
      flex: 1;
      width: 100%;
      box-sizing: border-box;
    }
    
    /* Main Content (70%) */
    .main-content {
      flex: 7;
      min-width: 0;
    }
    
    /* Sidebar (30%) */
    .sidebar {
      flex: 3;
      background: #12121a; 
      backdrop-filter: blur(20px); 
      border-radius: 12px; 
      border: 1px solid #2a2a3e; 
      box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);   
      padding: 30px;
      height: fit-content;
      position: sticky;
      top: 20px;
    }
    
    .sidebar h2 {
      color: #FF6600;
      font-size: 20px;
      border-bottom: 1px solid #2a2a3e;
      padding-bottom: 10px;
      margin-top: 0;
      font-weight: 700;
    }
    
    .sidebar-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    
    .sidebar-list li {
      margin-bottom: 15px;
      border-bottom: 1px solid rgba(255,102,0,0.1);
      padding-bottom: 15px;
    }
    
    .sidebar-list li:last-child {
      border-bottom: none;
      margin-bottom: 0;
      padding-bottom: 0;
    }
    
    .sidebar-list a {
      color: #e2e2ea;
      text-decoration: none;
      transition: color 0.2s;
      font-size: 15px;
      font-weight: 500;
      line-height: 1.4;
      display: block;
    }
    
    .sidebar-list a:hover {
      color: #FF6600;
    }
    
    .sidebar-date {
      display: block;
      font-size: 12px;
      color: #8888a0;
      margin-top: 5px;
    }

    /* Artículos */
    .article-box {
      background: #12121a; 
      backdrop-filter: blur(20px); 
      border-radius: 12px; 
      border: 1px solid #2a2a3e; 
      box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);   
      padding: 40px; 
      margin-bottom: 30px;
      text-align: justify;
    }
    
    .article-box h1 {
      color: #fff;
      font-size: 32px;
      margin-top: 0;
      margin-bottom: 10px;
      font-weight: 800;
      line-height: 1.2;
    }
    
    .article-meta {
      font-size: 14px;
      color: #FF6600;
      margin-bottom: 25px;
      font-style: italic;
      font-weight: 600;
    }
    
    .article-box h2 {
      color: #FF6600; 
      font-size: 24px; 
      border-left: 4px solid #FF6600; 
      padding-left: 15px; 
      margin-top: 30px;
      margin-bottom: 16px; 
      font-weight: 700;
    }
    
    .article-box p {
      color: #8888a0;
      margin-bottom: 15px;
    }

    .article-box ul {
      color: #e2e2ea;
      padding-left: 20px;
    }
    
    .article-box li {
      margin-bottom: 8px;
    }
    
    .agent-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 20px; }
    .agent { 
      background: #111; 
      border-radius: 8px; 
      padding: 16px; 
      border: 1px solid #2a2a2a; 
      transition: all 0.3s ease;
      cursor: default;
    }
    .agent:hover {
      transform: translateY(-5px);
      border-color: rgba(255, 102, 0, 0.5);
      box-shadow: 0 8px 25px rgba(255, 102, 0, 0.15);
      background: #161616;
    }
    .agent .role { font-weight: 800; color: #FF6600; font-size: 16px; transition: transform 0.3s ease; }
    .agent:hover .role { transform: translateX(5px); }
    .agent .desc { font-size: 13px; color: #8888a0; margin-top: 6px; transition: color 0.3s ease; }
    .agent:hover .desc { color: #e2e2ea; }

    /* Nav Top */
    .top-nav {
      background: rgba(18, 18, 26, 0.9);
      backdrop-filter: blur(15px);
      border-bottom: 1px solid #2a2a3e;
      padding: 15px 30px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    
    .top-nav-logo {
      font-size: 24px;
      font-weight: 800;
      text-decoration: none;
      letter-spacing: 1px;
    }
    
    .top-nav-links {
      display: flex;
      gap: 20px;
      align-items: center;
    }
    
    .top-nav-links a {
      color: #8888a0;
      text-decoration: none;
      font-size: 14px;
      font-weight: 600;
      transition: color 0.2s;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    .top-nav-links a:hover {
      color: #FF6600;
    }

    .footer {
      text-align: center;
      padding: 30px;
      font-size: 13px;
      color: #666;
      border-top: 1px solid #222;
      margin-top: auto;
    }

    /* Responsive */
    @media (max-width: 900px) {
      .blog-container {
        flex-direction: column;
      }
      .sidebar {
        position: static;
      }
      .agent-grid {
        grid-template-columns: 1fr;
      }
      .top-nav {
        flex-direction: column;
        gap: 15px;
        padding: 15px;
      }
      .top-nav-links {
        flex-wrap: wrap;
        justify-content: center;
      }
    }
  </style>
</head>
<body>

  <!-- Top Navigation -->
  <div class="top-nav">
    <a href="https://www.chask.fun/charm.php" class="top-nav-logo">
      <span class="o">CHA</span><span class="w">SK SWA</span><span class="o">RM</span> <span style="color:#555; font-size:18px;">BLOG</span>
    </a>
    <div class="top-nav-links">
      <a href="https://www.chask.fun/charm.php">Web Oficial</a>
      <a href="https://www.patreon.com/Tuprofeonline992" target="_blank">Patreon</a>
      <a href="https://github.com/nora-chask/chask-swarm" target="_blank">GitHub</a>
      <a href="https://x.com/Chask_Swarm" target="_blank">X (Twitter)</a>
    </div>
  </div>

  <div class="blog-container">
    
    <!-- Main Content -->
    <div class="main-content">
      
      <!-- Publicación Fijada / Actual -->
      <article class="article-box">
        <h1>La Revolución de la Inteligencia Artificial Local</h1>
        <div class="article-meta">Publicado el 24 de mayo de 2026 &mdash; 📌 Fijado</div>
        
        <p><strong><span class="o">Cha</span><span class="w">sk Swa</span><span class="o">rm</span></strong> es un ecosistema avanzado de agentes de Inteligencia Artificial diseñado para operar de forma totalmente local en tu equipo o conectarse a modelos en la nube, garantizando una privacidad absoluta sobre tus datos si así lo deseas. Solo enviamos información a servidores de terceros si lo decides tú. El control absoluto siempre lo tienes tú.</p>
        
        <p>Mediante un sistema de <strong>Mente Colmena</strong>, diferentes especialistas de Inteligencia Artificial colaboran de forma simultánea y autónoma bajo la dirección de un orquestador, resolviendo problemas complejos, programando, analizando datos y automatizando tareas pesadas.</p>
        
        <h2>Características Principales</h2>
        <ul>
            <li><strong>100% Privado y Local o Cloud:</strong> Ejecución de modelos locales directamente en tu máquina para máxima privacidad, o conexión a las IAs más potentes de la nube si tú lo decides.</li>
            <li><strong>Mente Colmena Autónoma:</strong> Agentes con roles definidos que trabajan en paralelo sin intervención manual constante.</li>
            <li><strong>Memoria a Largo Plazo:</strong> Integración con la base de datos vectorial Qdrant, permitiendo a <strong><span class="o">Cha</span><span class="w">sk Swa</span><span class="o">rm</span></strong> recordar proyectos, instrucciones y contextos pasados.</li>
            <li><strong>Gestión Inteligente de Recursos:</strong> Detección de tu hardware y GPU para seleccionar el modelo más óptimo para tu PC.</li>
            <li><strong>Multi-Canal:</strong> Controla a tu enjambre desde la terminal, desde el panel web o incluso mediante Telegram y Discord.</li>
        </ul>

        <h2>Conoce a Nuestros Especialistas</h2>
        <p>El núcleo de <strong><span class="o">Cha</span><span class="w">sk Swa</span><span class="o">rm</span></strong> está formado por agentes dedicados, cada uno experto en su campo:</p>
        <div class="agent-grid">
            <div class="agent">
                <div class="role">Viper</div>
                <div class="desc">El Arquitecto. Diseña estructuras complejas, planifica proyectos y orquesta soluciones de alto nivel.</div>
            </div>
            <div class="agent">
                <div class="role">Ghost</div>
                <div class="desc">El Developer. Programador experto, depura código y ejecuta tareas técnicas con precisión milimétrica.</div>
            </div>
            <div class="agent">
                <div class="role">Hunter</div>
                <div class="desc">Growth & Sales. Especialista en Growth Hacking, SEO, monetización y código orientado a conversión.</div>
            </div>
            <div class="agent">
                <div class="role">Oracle</div>
                <div class="desc">Compliance & Data. Especialista en manejo de datos, normativas y procesamiento profundo de información.</div>
            </div>
        </div>
      </article>

    </div>

    <!-- Sidebar -->
    <div class="sidebar">
      <h2>Publicaciones</h2>
      <ul class="sidebar-list">
        <li>
          <a href="Charm_Blog.php" style="color: #FF6600;">La Revolución de la Inteligencia Artificial Local</a>
          <span class="sidebar-date">24 Mayo 2026 📌 Fijado</span>
        </li>
        <!-- Futuras publicaciones irán aquí de forma descendente -->
      </ul>
    </div>

  </div>

  <footer class="footer">
    <p><strong><span class="o">CHA</span><span class="w">SK SWA</span><span class="o">RM</span></strong> Intelligence Ecosystem &copy; 2026 &mdash; Desarrollado por Fernando y Charm.</p>
    <p style="margin-top: 10px;">
        <a href="https://www.chask.fun/charm.php" style="color:#FF6600; text-decoration:none;">Web Oficial</a> | 
        <a href="https://www.patreon.com/Tuprofeonline992" style="color:#FF6600; text-decoration:none;">Patreon</a> | 
        <a href="https://github.com/nora-chask/chask-swarm" style="color:#FF6600; text-decoration:none;">GitHub</a> | 
        <a href="https://x.com/Chask_Swarm" style="color:#FF6600; text-decoration:none;">Twitter/X</a>
    </p>
  </footer>

</body>
</html>
