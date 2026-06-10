import os, re, sys

TARGET_FILE = r"C:\Program Files\Chask_Swarm\Advanced_Tools\web_dashboard_pro.py"

with open(TARGET_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Frontend: addMsg function
old_addmsg = r"""function addMsg(t,c){
  const d=document.createElement('div');
  d.className='msg '+c;
  d.textContent=t;
  chat.appendChild(d);
  chat.scrollTop=chat.scrollHeight;
}"""

new_addmsg = r"""function addMsg(t,c){
  const d=document.createElement('div');
  d.className='msg '+c;
  // Escapar HTML básico
  let escaped = t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  
  // Reemplazar saltos de línea
  escaped = escaped.replace(/\n/g, '<br>');
  
  // Reemplazar imágenes
  escaped = escaped.replace(/\[IMAGEN ADJUNTA:\s*(.*?)\]/gi, '<br><img src="/download?path=$1" style="max-width:100%; border-radius:8px; margin-top:8px;" onerror="this.style.display=\'none\'">');
  // Reemplazar archivos
  escaped = escaped.replace(/\[(?:ARCHIVO ADJUNTO|ARCHIVO CREADO|AUDIO TRANSCRITO):\s*(.*?)\]/gi, '<br><a href="/download?path=$1" target="_blank" style="display:inline-block; padding:6px 12px; background:var(--primary); color:#fff; text-decoration:none; border-radius:6px; margin-top:8px; font-size:12px;">⬇️ Descargar Archivo / Ver Local</a>');
  
  d.innerHTML = escaped;
  chat.appendChild(d);
  chat.scrollTop=chat.scrollHeight;
}"""

content = content.replace(old_addmsg, new_addmsg)

# 2. Frontend: HTML input area
old_input = r"""      <div class="input-area">
        <textarea id="inp" placeholder="Escribe un mensaje o comando para el orquestador..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}"></textarea>
        <button class="send-btn" onclick="send()">ENVIAR</button>
      </div>"""

new_input = r"""      <div class="input-area">
        <label for="file-inp" title="Adjuntar archivo (PDF, Imagen, Audio, DOC)" style="cursor:pointer; padding:12px; background:rgba(255,255,255,0.05); border-radius:8px; margin-right:8px; transition:0.3s; display:flex; align-items:center;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>
        </label>
        <input type="file" id="file-inp" style="display:none" onchange="document.getElementById('file-name').textContent = this.files[0] ? '📎 ' + this.files[0].name : '';">
        <div style="display:flex; flex-direction:column; flex:1; position:relative;">
          <span id="file-name" style="position:absolute; top:-20px; left:5px; font-size:11px; color:var(--accent); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;"></span>
          <textarea id="inp" placeholder="Escribe un mensaje o adjunta un archivo..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}"></textarea>
        </div>
        <button class="send-btn" onclick="send()">ENVIAR</button>
      </div>"""

content = content.replace(old_input, new_input)

# 3. Frontend: JS send function
old_send_func = r"""async function send(){
  const i=document.getElementById('inp'),t=i.value.trim();
  if(!t)return;
  i.value='';
  addMsg(t,'user');
  addMsg('Procesando...','system');
  const r=await fetch('/send',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({message:t})
  });"""

new_send_func = r"""async function send(){
  const i=document.getElementById('inp'), t=i.value.trim();
  const f=document.getElementById('file-inp');
  const file = f.files[0];
  if(!t && !file) return;
  
  i.value=''; f.value=''; document.getElementById('file-name').textContent='';
  let displayMsg = t;
  if(file) displayMsg = (t ? t + "\n" : "") + "[ARCHIVO ADJUNTO: " + file.name + "]";
  
  addMsg(displayMsg,'user');
  addMsg('Procesando...','system');
  
  const formData = new FormData();
  if(t) formData.append('message', t);
  if(file) formData.append('file', file);
  
  const r=await fetch('/send',{
    method:'POST',
    body:formData
  });"""

content = content.replace(old_send_func, new_send_func)


# 4. Backend: /send route
old_route = r"""@app.route("/send", methods=["POST"])
def send_message():
    data = request.get_json(); message = data.get("message", "").strip()
    if not message: return jsonify({"error": "Mensaje vacío"}), 400"""

new_route = r"""@app.route("/send", methods=["POST"])
def send_message():
    message = ""
    if request.is_json:
        data = request.get_json()
        message = data.get("message", "").strip()
    else:
        message = request.form.get("message", "").strip()
        file = request.files.get("file")
        if file and file.filename:
            import tempfile, PyPDF2, shutil
            # Guardar en carpeta temporal persistente para descargas
            upload_dir = os.path.join(BASE_DIR, "Advanced_Tools", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            safe_name = "".join(c for c in file.filename if c.isalnum() or c in " ._-").strip()
            tmp_path = os.path.join(upload_dir, f"{int(time.time())}_{safe_name}")
            file.save(tmp_path)
            
            ext = os.path.splitext(tmp_path)[1].lower()
            text_extracted = ""
            
            try:
                if ext == ".pdf":
                    pdf = PyPDF2.PdfReader(tmp_path)
                    text_extracted = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
                elif ext in [".mp3", ".wav", ".ogg", ".m4a"]:
                    import whisper
                    model = whisper.load_model("base")
                    result = model.transcribe(tmp_path)
                    text_extracted = result["text"]
                elif ext in [".txt", ".md", ".csv", ".json", ".py", ".js", ".html", ".css", ".php"]:
                    with open(tmp_path, "r", encoding="utf-8", errors="ignore") as tf:
                        text_extracted = tf.read()
            except Exception as e:
                text_extracted = f"Error al procesar el archivo localmente: {e}"
            
            # Incorporar el adjunto al mensaje
            if ext in [".png", ".jpg", ".jpeg", ".webp"]:
                message += f"\n[IMAGEN ADJUNTA: {tmp_path}]"
            elif text_extracted:
                message += f"\n\n--- [CONTENIDO DEL ARCHIVO: {file.filename}] ---\n{text_extracted}\n---"
            else:
                message += f"\n[ARCHIVO ADJUNTO: {tmp_path}]"
    
    if not message: return jsonify({"error": "Mensaje vacío"}), 400"""

content = content.replace(old_route, new_route)

# 5. Endpoint Download
download_route = r"""
@app.route("/download")
def download_file():
    path = request.args.get("path")
    if not path or not os.path.exists(path): return "File not found", 404
    from flask import send_file
    return send_file(path, as_attachment=True)
"""
if "@app.route(\"/download\")" not in content:
    content = content.replace('if __name__ == "__main__":', download_route + '\nif __name__ == "__main__":')


with open(TARGET_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("Parche aplicado con exito!")
