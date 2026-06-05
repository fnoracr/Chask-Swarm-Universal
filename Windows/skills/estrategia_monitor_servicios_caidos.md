# Estrategia: Monitorización de Servicios Caídos

## Cuándo Aplicar
Cuando un servicio externo (GitHub, API, servidor, etc.) no está accesible y necesitas saber cuándo vuelve para continuar una tarea.

## Protocolo de Actuación

### 1. Diagnóstico Rápido (2 minutos)
```powershell
# Verificar si es el servicio o la red
$sites = @("github.com", "google.com", "api.telegram.org", "pypi.org")
foreach ($site in $sites) {
    $r = Test-NetConnection $site -Port 443 -WarningAction SilentlyContinue
    $status = if ($r.TcpTestSucceeded) { "OK" } else { "BLOQUEADO" }
    Write-Host "$status  $site"
}
```

### 2. Buscar en la Web si hay Caída Global
```
search_web "is [servicio] down right now"
read_url_content "https://www.[servicio]status.com/"
```

### 3. Si Es Local: Intentar Proxies/Alternativas
- DNS alternativo (8.8.8.8, 1.1.1.1)
- Puerto SSH alternativo (ssh.github.com:443)
- Proxies web (corsproxy.io, ghproxy.com)

### 4. Si Nada Funciona: Lanzar Monitor
Crear script temporal `_monitor_[servicio].py` en el workspace:
- Ubicación: `C:\Users\fnora\Desktop\Enjambre Datos\_monitor_[servicio].py`
- Lanzar con `pythonw` (background, sin ventana)
- Intervalo: 15 minutos (configurable)
- Máximo: 24 horas (96 checks)
- Al detectar reconexión:
  1. Enviar Telegram al Administrador
  2. Inyectar mensaje en input_queue.json para que Enjambre lo procese
  3. Auto-eliminarse (script temporal)

### 5. Mientras Tanto: Trabajar Offline
- Continuar con todas las tareas que no requieran el servicio
- Dejar las tareas dependientes documentadas en memory.md → "Pendiente cuando [servicio] vuelva"

## Plantilla del Monitor

```python
import socket, time, subprocess, sys, os, json
from datetime import datetime

TARGET_HOST = "[SERVICIO]"
TARGET_PORT = 443
CHECK_INTERVAL = 15 * 60  # 15 min
MAX_CHECKS = 96  # 24h

def check(host, port):
    try:
        s = socket.create_connection((host, port), timeout=10)
        s.close()
        return True
    except:
        return False

def notify(msg):
    subprocess.run([sys.executable, r"C:\Program Files\Chask_Swarm\charm_telegram.py", "send", msg], timeout=30)

for i in range(1, MAX_CHECKS + 1):
    if check(TARGET_HOST, TARGET_PORT):
        notify(f"✅ {TARGET_HOST} ONLINE (check #{i})")
        os.remove(os.path.abspath(__file__))  # auto-eliminar
        break
    time.sleep(CHECK_INTERVAL)
```

## Reglas
- **SIEMPRE** notificar por Telegram cuando el servicio vuelva
- **SIEMPRE** inyectar en input_queue.json para contexto de Enjambre
- **SIEMPRE** auto-eliminar el script temporal al terminar
- **NUNCA** dejar un monitor corriendo indefinidamente (máximo 24h)
- **SIEMPRE** documentar la tarea pendiente en memory.md
