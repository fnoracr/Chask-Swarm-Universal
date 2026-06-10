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

print("=== norameet_ws_bot.py ===")
run(ssh, "cat /root/proyecto_norameet/bot/norameet_ws_bot.py", wait=8)

print("\n=== norameet_chask_bridge_v2.py ===")
run(ssh, "cat /root/proyecto_norameet/bot/norameet_chask_bridge_v2.py", wait=8)

print("\n=== norameet_launcher.py ===")
run(ssh, "cat /root/proyecto_norameet/backend/norameet_launcher.py", wait=5)

print("\n=== backend main.py (WS protocol) ===")
run(ssh, "cat /root/proyecto_norameet/backend/main.py", wait=5)

t.close()
