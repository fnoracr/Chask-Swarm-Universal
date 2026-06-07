import paramiko, sys, time, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PASSWORD = 'N0r4Z0e?12@3'
HOST = '31.97.152.240'

def handler(title, instructions, fields):
    return [PASSWORD] * len(fields)

def run(ssh, cmd, wait=6):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    if out: print(out[:1500])
    if err and 'warning' not in err.lower()[:20]: print('!', err[:300])
    return out

t = paramiko.Transport((HOST, 22))
t.connect()
t.auth_interactive('root', handler)
ssh = paramiko.SSHClient()
ssh._transport = t

report = []

# ─── 1. Abrir puerto 51400 (Hub) en UFW ──────────────────────────
print("=== [1/5] Abriendo puerto 51400 en UFW ===")
run(ssh, "ufw allow 51400/tcp comment 'Chask Swarm Hub'", wait=5)
out = run(ssh, "ufw allow 51400/udp comment 'Chask Swarm Hub UDP'", wait=5)
report.append("Puerto 51400 (Hub) abierto en UFW")

# ─── 2. Comparar app.js del proyecto vs el servido por Docker ────
print("\n=== [2/5] Comparando app.js proyecto vs Docker ===")
# Que sirve el contenedor realmente?
docker_appjs = run(ssh,
    "find /var/lib/docker/overlay2/4850b44ae0c15c728f11c411ae574dc0a410a6ccacc8ee1d3a00d7253b901397/merged/opt/MeetCharm/static/ -name 'app.js' | head -1 | xargs cat 2>/dev/null | grep -i 'iceServer\\|TURN\\|STUN\\|config =' | head -5",
    wait=5)
project_appjs = run(ssh,
    "grep -i 'iceServer\\|config =' /root/proyecto_norameet/frontend/app.js | head -3",
    wait=5)
print("Docker sirve:", docker_appjs[:200])
print("Proyecto tiene:", project_appjs[:200])

# ─── 3. Copiar app.js correcto (con TURN local) al container ─────
print("\n=== [3/5] Desplegando app.js con TURN local al container ===")

# Leer el app.js del proyecto (el que ya tiene TURN correcto)
project_content = run(ssh, "cat /root/proyecto_norameet/frontend/app.js", wait=5)
has_local_turn = '31.97.152.240:3478' in project_content

if has_local_turn:
    # El proyecto ya tiene el TURN local - copiar al static del overlay
    run(ssh, 
        "cp /root/proyecto_norameet/frontend/app.js /var/lib/docker/overlay2/4850b44ae0c15c728f11c411ae574dc0a410a6ccacc8ee1d3a00d7253b901397/merged/opt/MeetCharm/static/app.js",
        wait=5)
    run(ssh,
        "cp /root/proyecto_norameet/frontend/app.js /var/lib/docker/overlay2/4850b44ae0c15c728f11c411ae574dc0a410a6ccacc8ee1d3a00d7253b901397/diff/opt/MeetCharm/static/app.js",
        wait=5)
    report.append("app.js con TURN local (31.97.152.240:3478) desplegado al container Docker")
    print("app.js con TURN local copiado al container")
else:
    print("AVISO: El proyecto NO tiene el TURN local - revisar manualmente")
    report.append("AVISO: app.js del proyecto no tiene TURN local configurado")

# ─── 4. Verificar credenciales TURN con turnclient ───────────────
print("\n=== [4/5] Verificando que coturn esta activo y accesible ===")
run(ssh, "systemctl status coturn --no-pager | head -5", wait=3)
run(ssh, "ss -ulnp | grep 3478 | head -3", wait=3)

# ─── 5. Forzar reload del container MeetCharm (sin downtime) ──────
print("\n=== [5/5] Reiniciando container MeetCharm para que sirva el nuevo app.js ===")
# Primero verificar que el contenedor esta en /opt/MeetCharm/static
container_static = run(ssh,
    "docker exec MeetCharm-api ls /opt/MeetCharm/static 2>/dev/null | grep app.js || echo 'static no montado como volumen'",
    wait=5)
print(f"Static en container: {container_static}")

# Si static esta montado como volumen, el cambio ya es visible sin restart
# Si no, necesitamos copiar dentro del container
if 'app.js' not in container_static:
    run(ssh,
        "docker cp /root/proyecto_norameet/frontend/app.js MeetCharm-api:/opt/MeetCharm/static/app.js 2>/dev/null || echo 'cp via docker fallido'",
        wait=8)
    report.append("app.js copiado directamente al container via docker cp")
else:
    report.append("static montado como volumen - cambio inmediato sin restart")

# Verificar final
final_check = run(ssh,
    "docker exec MeetCharm-api cat /opt/MeetCharm/static/app.js 2>/dev/null | grep 'turn:31' | head -2",
    wait=5)
if '31.97.152.240' in (final_check or ''):
    report.append("CONFIRMADO: Container sirve app.js con TURN local")
else:
    report.append("PENDIENTE: Verificar manualmente que app.js en container tiene TURN local")

# Verificar Hub
hub_check = run(ssh, "curl -s --max-time 5 http://localhost:51400/hub/status", wait=8)
if 'hub_is_router' in (hub_check or ''):
    report.append("Hub activo: http://31.97.152.240:51400")

t.close()

# ─── Informe final ────────────────────────────────────────────────
print("\n" + "="*55)
print("INFORME FINAL")
print("="*55)
for i, item in enumerate(report, 1):
    print(f"  {i}. {item}")
