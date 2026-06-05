import paramiko, sys, time, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PASSWORD = 'N0r4Z0e?12@3'
HOST = '31.97.152.240'

def handler(title, instructions, fields):
    return [PASSWORD] * len(fields)

def run(ssh, cmd, wait=8, show=True):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    if show and out: print(out[:600])
    if show and err and 'warning' not in err.lower()[:20]: print('!', err[:300])
    return out

t = paramiko.Transport((HOST, 22))
t.connect()
t.auth_interactive('root', handler)
ssh = paramiko.SSHClient()
ssh._transport = t

# 1. Crear virtualenv aislado (NO toca sistema, NO toca MariaDB/Qdrant/n8n)
print("=== [1/4] Creando virtualenv aislado ===")
run(ssh, 'python3 -m venv /opt/chask/venv', wait=15)
print("Virtualenv OK")

# 2. Instalar Flask en el venv
print("\n=== [2/4] Instalando Flask en el venv ===")
run(ssh, '/opt/chask/venv/bin/pip install flask --quiet', wait=30)
out = run(ssh, '/opt/chask/venv/bin/python -c "from flask import Flask; print(\'Flask OK\')"', wait=5)
print(out if out else "Flask instalado")

# 3. Actualizar el servicio systemd para usar el venv
print("\n=== [3/4] Actualizando servicio systemd para usar venv ===")
service_content = """[Unit]
Description=Chask Swarm Hub Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/chask
ExecStart=/opt/chask/venv/bin/python /opt/chask/swarm_hub_server.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/chask/hub.log
StandardError=append:/var/log/chask/hub.log

[Install]
WantedBy=multi-user.target
"""
# Escribir el servicio
stdin, stdout, stderr = ssh.exec_command("tee /etc/systemd/system/chask-hub.service")
stdin.write(service_content)
stdin.channel.shutdown_write()
stdout.read(); stderr.read()

run(ssh, 'systemctl daemon-reload', wait=3)
run(ssh, 'systemctl restart chask-hub', wait=5)
time.sleep(5)

# 4. Verificar
print("\n=== [4/4] Verificando Hub ===")
run(ssh, 'systemctl status chask-hub --no-pager -l', wait=3)
print()
run(ssh, 'curl -s --max-time 5 http://localhost:51400/hub/status', wait=8)

t.close()
print(f"\n=== Hub desplegado en http://{HOST}:51400 ===")
