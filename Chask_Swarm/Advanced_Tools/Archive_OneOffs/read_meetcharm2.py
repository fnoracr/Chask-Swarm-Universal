import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PASSWORD = 'AQUI_VA_TU_FTP_PASS'
HOST = '31.97.152.240'

def handler(title, instructions, fields):
    return [PASSWORD] * len(fields)

def run(ssh, cmd, wait=5):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode(errors='replace').strip()
    if out: print(out[:3000])
    return out

t = paramiko.Transport((HOST, 22))
t.connect()
t.auth_interactive('root', handler)
ssh = paramiko.SSHClient()
ssh._transport = t

print("=== norameet_start.sh ===")
run(ssh, "cat /usr/local/bin/norameet_start.sh 2>/dev/null || cat /root/proyecto_norameet/backend/norameet_start.sh", wait=5)

print("\n=== norameet_ws_bot.py COMPLETO ===")
run(ssh, "cat /usr/local/bin/norameet_ws_bot.py 2>/dev/null || cat /root/proyecto_norameet/bot/norameet_ws_bot.py", wait=5)

print("\n=== docker-compose de MeetCharm (variables de entorno) ===")
run(ssh, "cat /opt/MeetCharm/docker-compose.yml 2>/dev/null || cat /root/proyecto_norameet/docker/docker-compose.yml", wait=5)

print("\n=== Variables de entorno del launcher ===")
run(ssh, "cat /etc/systemd/system/MeetCharm-launcher.service 2>/dev/null || systemctl cat MeetCharm-launcher 2>/dev/null | head -40", wait=5)

t.close()
