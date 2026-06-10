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
    if err: print('ERR:', err[:400])
    return out, err

t = paramiko.Transport((HOST, 22))
t.connect()
t.auth_interactive('root', handler)
ssh = paramiko.SSHClient()
ssh._transport = t

print("=== ERROR DEL HUB ===")
run(ssh, "python3 /opt/chask/swarm_hub_server.py &")
time.sleep(3)
run(ssh, "python3 /opt/chask/swarm_hub_server.py 2>&1 | head -30")

print("\n=== INSTALACION FLASK CORRECTA? ===")
run(ssh, "python3 -c 'from flask import Flask; print(\"Flask OK\")'")

print("\n=== DEPENDENCIAS FALTANTES? ===")
run(ssh, "python3 -c 'import flask, json, time, threading, uuid, pathlib; print(\"Todas OK\")'")

t.close()
