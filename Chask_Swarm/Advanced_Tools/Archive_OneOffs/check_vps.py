import paramiko, sys, time, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PASSWORD = 'AQUI_VA_TU_FTP_PASS'
HOST = '31.97.152.240'

def handler(title, instructions, fields):
    return [PASSWORD] * len(fields)

def run(ssh, cmd, wait=4):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    if out: print(out[:600])
    if err and 'warning' not in err.lower(): print('ERR:', err[:200])
    return out

t = paramiko.Transport((HOST, 22))
t.connect()
t.auth_interactive('root', handler)
ssh = paramiko.SSHClient()
ssh._transport = t

print("=== PUERTOS EN USO (para detectar conflictos) ===")
run(ssh, "ss -tlnp | grep -E 'LISTEN' | awk '{print $4, $6}' | sort")

print("\n=== SERVICIOS SYSTEMD ACTIVOS ===")
run(ssh, "systemctl list-units --type=service --state=running --no-pager | grep -v '@'")

print("\n=== HUB STATUS (puerto 51400) ===")
run(ssh, "sleep 3 && curl -s http://localhost:51400/hub/status", wait=8)

print("\n=== LOG DEL HUB ===")
run(ssh, "journalctl -u chask-hub --no-pager -n 20")

t.close()
