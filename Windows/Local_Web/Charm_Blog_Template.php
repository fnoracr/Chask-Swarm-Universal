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
      
      <!-- NUEVA PUBLICACIÓN AQUÍ -->
      <article class="article-box">
        <h1>[TÍTULO DE LA PUBLICACIÓN]</h1>
        <div class="article-meta">Publicado el [FECHA]</div>
        
        <p>Escribe tu texto aquí. Recuerda siempre que <strong><span class="o">Cha</span><span class="w">sk Swa</span><span class="o">rm</span></strong> debe llevar este formato específico de spans.</p>
        
        <h2>Subtítulo de ejemplo</h2>
        <p>Más contenido...</p>
      </article>

    </div>

    <!-- Sidebar -->
    <div class="sidebar">
      <h2>Publicaciones</h2>
      <ul class="sidebar-list">
        <li>
          <a href="Charm_Blog_NUEVO.php" style="color: #FF6600;">[TÍTULO DE LA PUBLICACIÓN]</a>
          <span class="sidebar-date">[FECHA]</span>
        </li>
        <li>
          <a href="Charm_Blog.php">La Revolución de la Inteligencia Artificial Local</a>
          <span class="sidebar-date">24 Mayo 2026 📌 Fijado</span>
        </li>
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
