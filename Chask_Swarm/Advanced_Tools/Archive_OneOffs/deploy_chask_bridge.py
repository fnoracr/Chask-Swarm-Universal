import paramiko, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PASSWORD = 'AQUI_VA_TU_FTP_PASS'
HOST = '31.97.152.240'
BOT_TOKEN = 'AQUI_VA_TU_TOKEN_TELEGRAM'
ADMIN_ID = 5034994867

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

# 1. Subir el bridge via SFTP
print("=== [1/4] Subiendo norameet_chask_bridge.py ===")
sftp = t.open_sftp_client()
sftp.put(
    r'C:\Program Files\Chask_Swarm\Advanced_Tools\norameet_chask_bridge.py',
    '/usr/local/bin/norameet_chask_bridge.py'
)
sftp.close()
run(ssh, "chmod +x /usr/local/bin/norameet_chask_bridge.py", wait=2)
print("Bridge subido OK")

# 2. Crear el config del enjambre con token y usuarios autorizados
print("\n=== [2/4] Creando /opt/chask/norameet_config.json ===")
config = {
    "trusted_users": ["Fernando", "fnora", "Fernando Enjambre", "fNora"],
    "bot_name": "Chask_AI",
    "llm_model": "claude-sonnet-4-5",
    "tts_enabled": True,
    "tts_model": "aura-2-carina-es",
    "telegram_bot_token": BOT_TOKEN,
    "telegram_admin_id": ADMIN_ID,
    "relay_pc_commands": True,
}
config_json = json.dumps(config, indent=2, ensure_ascii=False)
stdin, stdout, stderr = ssh.exec_command("tee /opt/chask/norameet_config.json")
stdin.write(config_json)
stdin.channel.shutdown_write()
stdout.read()
print("Config creado")

# 3. Actualizar norameet_start.sh para usar el nuevo bridge
print("\n=== [3/4] Actualizando norameet_start.sh ===")
new_start_sh = """#!/bin/bash
ROOM=${1:?Uso: norameet_start.sh <room_id>}

# Solo matar procesos de ESTA sala
pkill -f "norameet_ws_bot.py $ROOM" 2>/dev/null
pkill -f "NORAMEET_ROOM=$ROOM" 2>/dev/null
sleep 1

# Bot WebSocket (transporte puro)
nohup python3 /usr/local/bin/norameet_ws_bot.py $ROOM --name Chask_AI > /var/log/MeetCharm-bot-$ROOM.log 2>&1 &
echo "Bot PID: $!"

# Bridge Chask (con filtro de usuarios y acceso completo a Enjambre)
DEEPGRAM_API_KEY=1bcef9dc8679c467bee61d26175ad853916899e2 \\
ABACUS_API_KEY=s2_1ad675ad01b84132882258da83e2a40b \\
NORAMEET_ROOM=$ROOM \\
nohup python3 /usr/local/bin/norameet_chask_bridge.py $ROOM > /var/log/MeetCharm-bridge-$ROOM.log 2>&1 &
echo "Bridge Chask PID: $!"
"""
stdin, stdout, stderr = ssh.exec_command("tee /usr/local/bin/norameet_start.sh")
stdin.write(new_start_sh)
stdin.channel.shutdown_write()
stdout.read()
run(ssh, "chmod +x /usr/local/bin/norameet_start.sh", wait=2)
print("norameet_start.sh actualizado")

# 4. Verificar sintaxis del bridge
print("\n=== [4/4] Verificando sintaxis del bridge ===")
run(ssh, "python3 -m py_compile /usr/local/bin/norameet_chask_bridge.py && echo 'Sintaxis OK'", wait=5)

# Estado final
print("\n=== CONFIGURACION ACTIVA ===")
run(ssh, "cat /opt/chask/norameet_config.json | python3 -c \"import json,sys; c=json.load(sys.stdin); print('Usuarios autorizados:', c['trusted_users']); print('Modelo:', c['llm_model']); print('TTS:', c['tts_model']); print('Relay PC:', c['relay_pc_commands'])\"", wait=5)

t.close()
print("\n=== DESPLIEGUE COMPLETO ===")
