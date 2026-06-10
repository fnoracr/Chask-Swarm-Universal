import paramiko, sys, time, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PASSWORD = 'AQUI_VA_TU_FTP_PASS'
HOST = '31.97.152.240'

def handler(title, instructions, fields):
    return [PASSWORD] * len(fields)

def run(ssh, cmd, wait=5):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    if out: print(out[:800])
    if err and 'warning' not in err.lower()[:20]: print('!', err[:200])
    return out

t = paramiko.Transport((HOST, 22))
t.connect()
t.auth_interactive('root', handler)
ssh = paramiko.SSHClient()
ssh._transport = t

# 1. Buscar openclaw en todo el VPS
print("=== BUSCANDO OPENCLAW EN EL VPS ===")
run(ssh, "find / -maxdepth 8 -name '*openclaw*' -o -name '*open_claw*' 2>/dev/null | grep -v proc | grep -v sys", wait=15)

# 2. Buscar MeetCharm
print("\n=== BUSCANDO MeetCharm EN EL VPS ===")
run(ssh, "find / -maxdepth 8 -name '*MeetCharm*' -o -name '*chask_meet*' -o -name '*meet*' 2>/dev/null | grep -v proc | grep -v sys | grep -v '/usr/share' | head -30", wait=15)

# 3. Ver servicios y contenedores docker relacionados
print("\n=== CONTENEDORES DOCKER ===")
run(ssh, "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || echo 'docker no accesible'", wait=8)

# 4. Ver procesos python en el VPS
print("\n=== PROCESOS PYTHON ACTIVOS ===")
run(ssh, "ps aux | grep python | grep -v grep", wait=3)

# 5. Ver puertos activos con nombres de servicio
print("\n=== SERVICIOS EN PUERTOS CLAVE ===")
run(ssh, "ss -tlnp | awk '{print $4}' | sort -u", wait=3)

t.close()
