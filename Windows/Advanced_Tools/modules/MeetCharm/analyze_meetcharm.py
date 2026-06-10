import paramiko, sys, time, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PASSWORD = 'AQUI_VA_TU_FTP_PASS'
HOST = '31.97.152.240'

def handler(title, instructions, fields):
    return [PASSWORD] * len(fields)

def run(ssh, cmd, wait=6):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    if out: print(out[:2000])
    if err and 'warning' not in err.lower()[:20]: print('!', err[:300])
    return out

t = paramiko.Transport((HOST, 22))
t.connect()
t.auth_interactive('root', handler)
ssh = paramiko.SSHClient()
ssh._transport = t

# 1. Ver docker-compose de Meet[Nombre_IA]
print("=== docker-compose.yml de Meet[Nombre_IA] ===")
run(ssh, "cat /opt/Meet[Nombre_IA]/docker-compose.yml 2>/dev/null || cat /root/proyecto_norameet/docker/docker-compose.yml 2>/dev/null", wait=5)

# 2. Ver el .env de Meet[Nombre_IA] (ICE config)
print("\n=== .env de Meet[Nombre_IA] ===")
run(ssh, "find /root/proyecto_norameet /opt/Meet[Nombre_IA] -name '.env' -o -name '*.env' 2>/dev/null | xargs cat 2>/dev/null | head -60", wait=8)

# 3. Buscar donde configura los ICE servers
print("\n=== ICE servers en el codigo fuente ===")
run(ssh, "grep -r 'iceServer\\|TURN\\|STUN\\|turn:\\|stun:\\|coturn\\|peerConfig\\|RTCPeerConfig' /root/proyecto_norameet/ 2>/dev/null | grep -v '.pyc' | head -30", wait=10)

# 4. Ver el main.py de la API de Meet[Nombre_IA]
print("\n=== main.py de Meet[Nombre_IA] API ===")
run(ssh, "find /root/proyecto_norameet -name 'main.py' | head -3 | xargs cat 2>/dev/null | head -80", wait=8)

# 5. Ver archivos JS/TS del frontend (donde se configura ICE)
print("\n=== Frontend WebRTC config ===")
run(ssh, "find /root/proyecto_norameet -name '*.js' -o -name '*.ts' -o -name '*.vue' 2>/dev/null | xargs grep -l 'iceServer\\|RTCPeer\\|TURN\\|STUN' 2>/dev/null | head -5", wait=10)
run(ssh, "find /root/proyecto_norameet -name '*.js' -o -name '*.ts' -o -name '*.vue' 2>/dev/null | xargs grep -l 'iceServer\\|RTCPeer\\|TURN\\|STUN' 2>/dev/null | head -3 | xargs cat 2>/dev/null | grep -A5 -B5 'iceServer\\|TURN\\|STUN' | head -60", wait=10)

# 6. Verificar si el firewall bloquea puertos TURN (49152-65535)
print("\n=== Firewall - puertos TURN (UDP 49152-65535) ===")
run(ssh, "ufw status 2>/dev/null || iptables -L INPUT -n --line-numbers 2>/dev/null | head -20", wait=5)

# 7. Estructura completa del proyecto
print("\n=== Estructura /root/proyecto_norameet ===")
run(ssh, "find /root/proyecto_norameet -maxdepth 3 -type f | grep -v '__pycache__\\|.git\\|node_modules' | sort | head -50", wait=8)

t.close()
print("\n=== ANALISIS COMPLETO ===")
