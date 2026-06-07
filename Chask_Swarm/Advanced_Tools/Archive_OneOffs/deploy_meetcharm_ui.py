import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PASSWORD = 'N0r4Z0e?12@3'; HOST = '31.97.152.240'

# ══════════════════════════════════════════════════════════════════
#  NUEVO index.html — Meet Charm con estética Chask Swarm
# ══════════════════════════════════════════════════════════════════
NEW_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Meet Charm — Chask Swarm</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#050512;--bg2:#0a0a1a;--purple:#7b2ff7;--cyan:#00f5d4;
  --red:#ff4466;--green:#00f5d4;--text:#e8e8f0;--muted:rgba(255,255,255,0.4);
  --card:rgba(255,255,255,0.03);--border:rgba(255,255,255,0.08);
  --header-height:60px;--controls-height:72px;--sidebar-width:200px;
}
html,body{height:100%;overflow:hidden;font-family:'Inter',sans-serif;background:var(--bg);color:var(--text)}

/* ── JOIN SCREEN ── */
.join-section{
  position:fixed;inset:0;z-index:200;
  background:radial-gradient(ellipse at 20% 50%,rgba(123,47,247,0.12) 0%,transparent 60%),
             radial-gradient(ellipse at 80% 20%,rgba(0,245,212,0.08) 0%,transparent 50%),
             var(--bg);
  display:flex;align-items:center;justify-content:center;
}
.join-section.hidden{display:none}
.join-box{
  background:rgba(255,255,255,0.04);
  border:1px solid rgba(123,47,247,0.3);
  border-radius:24px;padding:40px 36px;width:380px;max-width:95vw;
  backdrop-filter:blur(20px);
  box-shadow:0 0 60px rgba(123,47,247,0.15),0 20px 60px rgba(0,0,0,0.5);
  display:flex;flex-direction:column;gap:14px;
}
.join-logo{font-size:28px;font-weight:900;text-align:center;margin-bottom:4px}
.join-logo span{color:var(--cyan)}
.join-room-info{
  background:rgba(0,245,212,0.06);border:1px solid rgba(0,245,212,0.2);
  border-radius:12px;padding:10px 14px;font-size:12px;color:var(--cyan);text-align:center;
}
.join-user-info{text-align:center;color:var(--muted);font-size:12px;margin-top:-6px}
.join-box p{color:var(--muted);font-size:13px;text-align:center;margin-top:-4px}
.device-select{
  width:100%;padding:10px 14px;border-radius:10px;
  background:rgba(255,255,255,0.05);border:1px solid var(--border);
  color:var(--text);font-family:'Inter',sans-serif;font-size:13px;
  outline:none;cursor:pointer;
}
.device-select:focus{border-color:rgba(123,47,247,0.5)}
.device-select option{background:#0a0a1a}
.big-btn{
  width:100%;padding:14px;border-radius:12px;border:none;cursor:pointer;
  background:linear-gradient(135deg,var(--purple),#9b59f7);
  color:#fff;font-family:'Inter',sans-serif;font-weight:700;font-size:14px;
  transition:all .2s;box-shadow:0 4px 20px rgba(123,47,247,0.4);
}
.big-btn:hover{transform:translateY(-2px);box-shadow:0 8px 30px rgba(123,47,247,0.5)}
.big-btn:disabled{opacity:0.4;cursor:not-allowed;transform:none}
.secondary-btn{
  width:100%;padding:12px;border-radius:12px;cursor:pointer;
  background:transparent;border:1px solid rgba(0,245,212,0.3);
  color:var(--cyan);font-family:'Inter',sans-serif;font-weight:600;font-size:13px;
  transition:all .2s;
}
.secondary-btn:hover{background:rgba(0,245,212,0.08);border-color:var(--cyan)}
.step2-inputs{display:flex;flex-direction:column;gap:10px}
.step2-inputs input{
  padding:10px 14px;border-radius:10px;
  background:rgba(255,255,255,0.05);border:1px solid var(--border);
  color:var(--text);font-family:'Inter',sans-serif;font-size:13px;outline:none;
}
.step2-inputs input:focus{border-color:rgba(123,47,247,0.5)}
.hidden{display:none!important}

/* ── HEADER ── */
.header{
  position:fixed;top:0;left:0;right:0;height:var(--header-height);
  background:rgba(5,5,18,0.95);backdrop-filter:blur(20px);
  border-bottom:1px solid var(--border);
  padding:0 1.2rem;display:flex;justify-content:space-between;align-items:center;z-index:100;
}
.header-logo{font-size:18px;font-weight:900}
.header-logo span{color:var(--cyan)}
.header-right{display:flex;align-items:center;gap:10px}
#statusDot{width:10px;height:10px;border-radius:50%;background:var(--red);transition:background .3s}
.chat-btn{
  background:rgba(123,47,247,0.2);border:1px solid rgba(123,47,247,0.4);
  color:#fff;padding:6px 16px;border-radius:20px;cursor:pointer;
  font-family:'Inter',sans-serif;font-size:13px;font-weight:600;transition:all .2s;
}
.chat-btn:hover{background:rgba(123,47,247,0.4)}
.room-badge{
  background:rgba(0,245,212,0.08);border:1px solid rgba(0,245,212,0.25);
  color:var(--cyan);padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;
}

/* ── MAIN ── */
.main-container{
  position:fixed;top:var(--header-height);left:0;right:0;bottom:var(--controls-height);
  display:flex;overflow:hidden;
}
.main-video-area{flex:1;display:flex;flex-direction:column;padding:.8rem;position:relative}
.video-grid{
  flex:1;display:grid;gap:.6rem;
  grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
  align-content:start;overflow-y:auto;
}
.video-container{
  position:relative;background:rgba(255,255,255,0.03);
  border:1px solid var(--border);border-radius:14px;overflow:hidden;
  aspect-ratio:16/9;
}
.video-container video{width:100%;height:100%;object-fit:cover;display:block}
.video-label{
  position:absolute;bottom:8px;left:8px;
  background:rgba(0,0,0,0.6);backdrop-filter:blur(8px);
  color:#fff;font-size:11px;font-weight:600;padding:3px 10px;border-radius:8px;
}
.fullscreen-btn{
  position:absolute;top:8px;right:8px;
  background:rgba(0,0,0,0.6);color:#fff;border:none;border-radius:8px;
  width:30px;height:30px;font-size:14px;cursor:pointer;z-index:15;
  opacity:0;transition:opacity .2s;display:flex;align-items:center;justify-content:center;
}
.video-container:hover .fullscreen-btn{opacity:1}

/* ── SIDEBAR ── */
.sidebar-right{
  width:0;overflow:hidden;transition:width .3s;
  background:rgba(5,5,18,0.95);border-left:1px solid var(--border);
  display:flex;flex-direction:column;gap:.5rem;padding:0;
}
.sidebar-video{
  position:relative;background:rgba(255,255,255,0.03);
  border-radius:12px;overflow:hidden;margin:.5rem;flex-shrink:0;
  border:1px solid var(--border);min-height:100px;aspect-ratio:16/9;
}
.sidebar-video video{width:100%;height:100%;object-fit:cover}

/* ── CONTROLS ── */
.controls{
  position:fixed;bottom:0;left:0;right:0;height:var(--controls-height);
  background:rgba(5,5,18,0.95);backdrop-filter:blur(20px);
  border-top:1px solid var(--border);
  display:flex;align-items:center;justify-content:center;gap:.6rem;padding:0 1rem;
}
.control-btn{
  padding:10px 18px;border-radius:12px;border:none;cursor:pointer;
  font-family:'Inter',sans-serif;font-size:13px;font-weight:600;transition:all .2s;
}
.control-btn.primary{
  background:rgba(123,47,247,0.15);border:1px solid rgba(123,47,247,0.3);color:#fff;
}
.control-btn.primary:hover{background:rgba(123,47,247,0.35)}
.control-btn.primary.active{background:var(--purple);border-color:var(--purple)}
.control-btn.secondary{
  background:rgba(255,255,255,0.05);border:1px solid var(--border);color:var(--muted);
}
.control-btn.secondary:hover{background:rgba(255,255,255,0.1);color:#fff}
.control-btn.danger{
  background:rgba(255,68,102,0.15);border:1px solid rgba(255,68,102,0.3);color:var(--red);
}
.control-btn.danger:hover{background:rgba(255,68,102,0.35)}
.control-btn:disabled{opacity:.35;cursor:not-allowed}

/* ── CHAT ── */
.chat-panel{
  position:fixed;right:-380px;top:var(--header-height);bottom:var(--controls-height);
  width:340px;background:rgba(10,10,26,0.98);border-left:1px solid var(--border);
  display:flex;flex-direction:column;z-index:50;transition:right .3s;
}
.chat-panel.open{right:0}
.chat-header{
  padding:14px 16px;border-bottom:1px solid var(--border);
  display:flex;justify-content:space-between;align-items:center;
  font-weight:700;font-size:14px;
}
.chat-close{
  background:none;border:none;color:var(--muted);cursor:pointer;font-size:18px;
}
.chat-messages{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}
.chat-msg{
  background:rgba(255,255,255,0.04);border:1px solid var(--border);
  border-radius:10px;padding:8px 12px;font-size:13px;
}
.chat-msg .from{font-weight:700;color:var(--cyan);font-size:11px;margin-bottom:3px}
.chat-input-area{border-top:1px solid var(--border);padding:12px}
.chat-input{display:flex;gap:8px;margin-bottom:8px}
.chat-input input{
  flex:1;padding:9px 12px;border-radius:10px;
  background:rgba(255,255,255,0.05);border:1px solid var(--border);
  color:var(--text);font-family:'Inter',sans-serif;font-size:13px;outline:none;
}
.chat-input input:focus{border-color:rgba(123,47,247,0.5)}
.chat-input button,.chat-actions button{
  padding:8px 14px;border-radius:10px;border:none;cursor:pointer;
  background:var(--purple);color:#fff;font-family:'Inter',sans-serif;font-size:13px;font-weight:600;
}
.chat-actions{display:flex;gap:8px}
.chat-actions button{background:rgba(255,255,255,0.07);color:var(--muted);flex:1}

/* ── SELF VIEW ── */
.self-view{
  position:absolute;bottom:10px;right:10px;width:120px;height:90px;
  border-radius:12px;overflow:hidden;border:2px solid rgba(123,47,247,0.5);
  box-shadow:0 4px 20px rgba(0,0,0,0.5);z-index:30;
}
.self-view video{width:100%;height:100%;object-fit:cover}

/* ── PRESENTER/NOTIFICATION ── */
.presenter-notification{
  position:fixed;top:70px;left:50%;transform:translateX(-50%);
  background:rgba(123,47,247,0.9);color:#fff;
  padding:6px 20px;border-radius:20px;font-size:13px;font-weight:700;z-index:90;
  box-shadow:0 4px 20px rgba(123,47,247,0.4);
}
.screen-share-main{grid-column:1/-1}
.screen-share-main video{object-fit:contain}

@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}

@media(max-width:768px){
  :root{--sidebar-width:130px}
  .sidebar-video{min-height:70px}
  .chat-panel{width:100%}
  .self-view{width:90px;height:68px;right:calc(var(--sidebar-width)+8px)}
}

/* Presentation mode */
.main-container.presentation-active .sidebar-right{width:280px}
.main-container.presentation-active .video-grid{grid-template-columns:1fr}
.main-container.presentation-active .sidebar-video{min-height:120px;aspect-ratio:16/9;border:1px solid rgba(0,245,212,0.2)}
</style>
</head>
<body>

<!-- JOIN SECTION -->
<div class="join-section" id="joinSection">
  <div class="join-box">
    <div class="join-logo">Meet <span>Charm</span></div>

    <div id="step1">
      <p>Configura tus dispositivos</p>
      <div class="join-room-info" id="joinRoomInfo">Sala: cargando...</div>
      <div class="join-user-info" id="joinUserInfo"></div>
      <select id="cameraSelect" class="device-select">
        <option value="">Cargando cámaras...</option>
      </select>
      <select id="micSelect" class="device-select">
        <option value="">Cargando micrófonos...</option>
      </select>
      <select id="resolutionSelect" class="device-select">
        <option value="">Resolución automática</option>
        <option value="360">360p (bajo)</option>
        <option value="480">480p (medio)</option>
        <option value="720">720p (HD)</option>
        <option value="1080">1080p (Full HD)</option>
      </select>
      <button class="big-btn" id="startBtn" onclick="start(true)" disabled>📹 Con Cámara y Micro</button>
      <button class="secondary-btn" onclick="start(false)">💬 Solo Chat</button>
    </div>

    <div id="step2" class="hidden">
      <div class="step2-inputs">
        <input type="text" id="usernameInput" placeholder="Tu nombre" maxlength="30">
        <input type="text" id="roomInput" placeholder="Código de sala" maxlength="30">
      </div>
      <button class="big-btn" onclick="createRoom()" style="margin-top:6px">🚀 Entrar a la sala</button>
      <button class="secondary-btn" onclick="joinRoom()">Unirse a sala existente</button>
    </div>
  </div>
</div>

<!-- HEADER -->
<div class="header">
  <div class="header-logo">Meet <span>Charm</span></div>
  <div class="header-right">
    <span class="room-badge" id="roomBadge" style="display:none">🎥 <span id="roomDisplay"></span></span>
    <span id="statusDot"></span>
    <span id="transcriptionIndicator" title="Transcripción activa" style="display:none;font-size:14px;animation:blink 1.5s infinite">🔴</span>
    <button class="chat-btn" onclick="toggleChat()">💬 Chat</button>
  </div>
</div>

<!-- MAIN -->
<div class="main-container" id="mainContainer">
  <div class="main-video-area" id="mainVideoArea">
    <div class="video-grid" id="videoGrid"></div>
  </div>
  <div class="sidebar-right" id="sidebarRight"></div>
</div>

<!-- CONTROLS -->
<div class="controls">
  <button class="control-btn primary" onclick="toggleMic()" id="micBtn" disabled>🎤 Mic</button>
  <button class="control-btn primary" onclick="toggleCamera()" id="camBtn" disabled>📹 Cam</button>
  <button class="control-btn secondary hidden" onclick="toggleScreen()" id="screenBtn">🖥 Compartir</button>
  <button class="control-btn secondary" onclick="toggleTranscription()" id="transcribeBtn" style="display:none" title="Transcripción">📝 Transcribir</button>
  <button class="control-btn secondary" onclick="openDeviceModal()" id="settingsBtn">⚙ Config</button>
  <button class="control-btn danger" onclick="leaveRoom()">✕ Salir</button>
</div>

<!-- CHAT -->
<div class="chat-panel" id="chatPanel">
  <div class="chat-header">
    <span>💬 Chat</span>
    <button class="chat-close" onclick="closeChat()">✕</button>
  </div>
  <div class="chat-messages" id="chatMessages"></div>
  <div class="chat-input-area">
    <div class="chat-input">
      <input type="text" id="messageInput" placeholder="Escribe un mensaje..." onkeypress="if(event.key==='Enter')sendMessage()">
      <button onclick="sendMessage()">→</button>
    </div>
    <div class="chat-actions">
      <button onclick="document.getElementById('fileInput').click()">📎 Archivo</button>
      <button onclick="document.getElementById('imageInput').click()">🖼 Imagen</button>
    </div>
    <input type="file" id="fileInput" onchange="handleFile(this.files[0]);this.value=''">
    <input type="file" id="imageInput" accept="image/*" onchange="handleImage(this.files[0]);this.value=''">
  </div>
</div>

<!-- DEVICE SETTINGS MODAL -->
<div class="join-section hidden" id="deviceSettingsModal" style="z-index:300;background:rgba(0,0,0,0.85)">
  <div class="join-box">
    <div class="join-logo">⚙ <span>Dispositivos</span></div>
    <select id="cameraSelectModal" class="device-select"><option value="">Cargando cámaras...</option></select>
    <select id="micSelectModal" class="device-select"><option value="">Cargando micrófonos...</option></select>
    <select id="resolutionSelectModal" class="device-select">
      <option value="">Resolución automática</option>
      <option value="360">360p</option><option value="480">480p</option>
      <option value="720">720p HD</option><option value="1080">1080p Full HD</option>
    </select>
    <button class="big-btn" onclick="applyDeviceSettings()">Aplicar cambios</button>
    <button class="secondary-btn" onclick="closeDeviceModal()">Cancelar</button>
  </div>
</div>

<!-- SELF VIEW -->
<div class="self-view hidden" id="selfView">
  <video id="localVideo" autoplay muted playsinline></video>
</div>

<script>
// Leer parámetros de URL e inyectar en inputs / UI
(function(){
  const p = new URLSearchParams(window.location.search);
  const room = p.get('room') || '';
  const name = decodeURIComponent(p.get('name') || '');
  if(room){
    document.getElementById('roomInput').value = room;
    document.getElementById('joinRoomInfo').textContent = '🎥 Sala: ' + room;
    document.getElementById('roomBadge').style.display = 'inline-flex';
    document.getElementById('roomDisplay').textContent = room;
  }
  if(name){
    document.getElementById('usernameInput').value = name;
    document.getElementById('joinUserInfo').textContent = '👤 ' + name;
  }

  // Parchar toggleChat para añadir clase CSS
  const origToggle = window.toggleChat;
  window._chatOpen = false;
  window.toggleChat = function(){
    window._chatOpen = !window._chatOpen;
    document.getElementById('chatPanel').classList.toggle('open', window._chatOpen);
    if(origToggle) origToggle();
  };
  window.closeChat = function(){
    window._chatOpen = false;
    document.getElementById('chatPanel').classList.remove('open');
  };

  // Mostrar roomBadge cuando entre a sala
  const origCreate = window.createRoom;
  const origJoin   = window.joinRoom;
  function onEnterRoom(){
    const r = document.getElementById('roomInput').value;
    document.getElementById('roomDisplay').textContent = r;
    document.getElementById('roomBadge').style.display = 'inline-flex';
  }
  document.addEventListener('DOMContentLoaded', function(){
    const ob = window.createRoom, oj = window.joinRoom;
    if(ob) window.createRoom = function(){ onEnterRoom(); ob(); };
    if(oj) window.joinRoom   = function(){ onEnterRoom(); oj(); };
  });
})();
</script>

<script src="/static/app.js"></script>
</body>
</html>
"""

def handler(title, instructions, fields): return [PASSWORD]*len(fields)
t = paramiko.Transport((HOST, 22)); t.connect(); t.auth_interactive('root', handler)
ssh = paramiko.SSHClient(); ssh._transport = t

# Backup
stdin,stdout,stderr = ssh.exec_command("cp /opt/MeetCharm/static/index.html /opt/MeetCharm/static/index.html.bak_pre_charm")
stdout.read(); print("Backup creado")

# Subir nuevo HTML
stdin2, stdout2, stderr2 = ssh.exec_command("tee /opt/MeetCharm/static/index.html")
stdin2.write(NEW_HTML.encode('utf-8'))
stdin2.channel.shutdown_write()
stdout2.read(); print("index.html subido")

# Verificar tamaño
stdin3,stdout3,_ = ssh.exec_command("wc -l /opt/MeetCharm/static/index.html && head -5 /opt/MeetCharm/static/index.html")
print(stdout3.read().decode(errors='replace'))

t.close()
print("=== LISTO ===")
