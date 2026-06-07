import paramiko, sys, time, base64, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PASSWORD = 'N0r4Z0e?12@3'
HOST     = '31.97.152.240'
HUB_FILE = r'C:\Program Files\Chask_Swarm\Advanced_Tools\swarm_hub_server.py'
REMOTE   = '/opt/chask/swarm_hub_server.py'
SERVICE  = '/etc/systemd/system/chask-hub.service'

def handler(title, instructions, fields):
    return [PASSWORD] * len(fields)

def run(ssh, cmd, wait=5, show=True):
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=False)
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    if show and out: print('>', out[:400])
    if show and err: print('!', err[:200])
    return out

print(f"Conectando a {HOST}...")
t = paramiko.Transport((HOST, 22))
t.connect()
t.auth_interactive('root', handler)
ssh = paramiko.SSHClient()
ssh._transport = t
print("Conectado OK\n")

# 1. Flask
print("=== [1/5] Instalando Flask ===")
run(ssh, 'pip3 install flask --quiet --break-system-packages', wait=30)
print("Flask OK\n")

# 2. Directorio
print("=== [2/5] Creando /opt/chask ===")
run(ssh, 'mkdir -p /opt/chask && mkdir -p /var/log/chask', wait=2)

# 3. Subir hub server via SFTP
print("=== [3/5] Subiendo swarm_hub_server.py via SFTP ===")
sftp = t.open_sftp_client()
sftp.put(HUB_FILE, REMOTE)
sftp.close()
print(f"Subido a {REMOTE}\n")

# 4. Verificar
print("=== [4/5] Verificando archivo ===")
run(ssh, f'head -3 {REMOTE} && wc -l {REMOTE}', wait=2)

# 5. Crear servicio systemd
print("=== [5/5] Creando servicio systemd ===")
service_content = f"""[Unit]
Description=Chask Swarm Hub Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/chask
ExecStart=/usr/bin/python3 {REMOTE}
Restart=always
RestartSec=10
StandardOutput=append:/var/log/chask/hub.log
StandardError=append:/var/log/chask/hub.log

[Install]
WantedBy=multi-user.target
"""
run(ssh, f"cat > {SERVICE} << 'SVCEOF'\n{service_content}\nSVCEOF", wait=2)
run(ssh, 'systemctl daemon-reload', wait=3)
run(ssh, 'systemctl enable chask-hub', wait=2)
run(ssh, 'systemctl start chask-hub', wait=5)

# Estado final
print("\n=== ESTADO DEL SERVICIO ===")
run(ssh, 'systemctl status chask-hub --no-pager', wait=3)

print("\n=== TEST HTTP ===")
run(ssh, 'curl -s http://localhost:51400/hub/status 2>&1 || echo "Puerto aun iniciando..."', wait=5)

t.close()
print("\n=== DESPLIEGUE COMPLETO ===")
print(f"Hub corriendo en: http://{HOST}:51400")
