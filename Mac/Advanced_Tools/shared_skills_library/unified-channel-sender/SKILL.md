---
name: unified-channel-sender
description: >-
  Permite a los agentes enviar mensajes directamente al panel de control Web local
  o a un canal de Discord de Chask Swarm usando un script unificado CLI.
---

# Unified Channel Sender

## Overview
Esta skill proporciona una interfaz CLI segura para que el agente inyecte mensajes asíncronos en los canales de comunicación integrados de Chask Swarm (Web y Discord). 
En Discord utiliza un Webhook configurado, y en Web envía los mensajes mediante HTTP POST al puerto local 7860. No contiene claves ni tokens harcodeados, leyendo todo directamente de `C:\Program Files\Chask_Swarm\Configuracion\channels_config.json`.

## Dependencies
Ninguna dependencia externa. Usa bibliotecas nativas de Python (`urllib`, `argparse`, `json`).

## Quick Start
```bash
python scripts/send_channel.py web --message "Mensaje de prueba" --limit 1 --output result.json
```

## Utility Scripts

El script `send_channel.py` implementa el patrón CLI obligatorio para integraciones con APIs externas y redes. Escribe su salida estructurada en archivos en vez de usar stdout.

### Enviar mensaje a Web Dashboard
Inyecta un mensaje en la cola interna del panel web de Chask Swarm.

```bash
python scripts/send_channel.py web --message "¡Hola desde la web!" --limit 1 --output web_result.json
```

### Enviar mensaje a Discord
Lee la URL del webhook de la configuración maestra y envía el mensaje a Discord.

```bash
python scripts/send_channel.py discord --message "¡Hola Discord!" --limit 1 --output discord_result.json
```

## Rate Limiting
La skill implementa un retardo estricto interno de **1 segundo** (`time.sleep(1)`) antes de cada petición HTTP. Este límite obedece al rate limit estándar de Discord para webhooks (5 peticiones por cada 5 segundos) y es suficiente para el dashboard local.

## Common Mistakes
- **No usar el argumento --output**: El script requiere siempre `--output` para guardar el resultado del envío en lugar de escupir JSON crudo a la consola.
- **Caracteres especiales en Windows**: Al ejecutar desde PowerShell o CMD, asegúrate de escapar las comillas o usar llamadas robustas si el mensaje contiene secuencias complejas.
