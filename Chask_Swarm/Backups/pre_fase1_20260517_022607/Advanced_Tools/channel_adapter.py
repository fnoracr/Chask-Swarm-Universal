"""
channel_adapter.py — Framework Base para Comunicación Multicanal
=================================================================
Clase base abstracta que define la interfaz para todos los adaptadores
de canal (Telegram, Discord, Slack, Teams, etc.).

Cada adaptador implementa: send, receive, listen, y format_message.
El ChannelRouter dirige mensajes al canal correcto automáticamente.

Uso:
  from channel_adapter import ChannelRouter
  router = ChannelRouter()
  router.send("telegram", "Hola Fernando")
  router.broadcast("Tarea completada")  # Envía a todos los canales activos
"""
import os
import sys
import json
import io
from datetime import datetime
from abc import ABC, abstractmethod

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADVANCED_DIR = os.path.dirname(os.path.abspath(__file__))
CHANNELS_CONFIG = os.path.join(BASE_DIR, "Configuracion", "channels_config.json")
MESSAGE_LOG = os.path.join(BASE_DIR, "Colas_Mensajes", "channel_messages.json")


class ChannelAdapter(ABC):
    """Clase base para todos los adaptadores de canal."""

    def __init__(self, name: str, config: dict = None):
        self.name = name
        self.config = config or {}
        self.active = True
        self.message_count = 0

    @abstractmethod
    def send(self, message: str, **kwargs) -> bool:
        """Envía un mensaje por este canal."""
        pass

    @abstractmethod
    def receive(self, timeout: int = 30) -> str | None:
        """Recibe un mensaje de este canal (bloqueante con timeout)."""
        pass

    def format_message(self, message: str, context: dict = None) -> str:
        """Formatea el mensaje para este canal. Override para markdown, HTML, etc."""
        return message

    def is_available(self) -> bool:
        """Verifica si el canal está disponible."""
        return self.active

    def get_stats(self) -> dict:
        return {
            "name": self.name,
            "active": self.active,
            "messages_sent": self.message_count
        }


class TelegramAdapter(ChannelAdapter):
    """Adaptador para Telegram usando antigravity_telegram.py."""

    def __init__(self, config: dict = None):
        super().__init__("telegram", config)
        self.script = os.path.join(BASE_DIR, "antigravity_telegram.py")

    def send(self, message: str, **kwargs) -> bool:
        import subprocess
        try:
            formatted = self.format_message(message)
            result = subprocess.run(
                [sys.executable, self.script, "send", formatted],
                capture_output=True, text=True, timeout=15,
                encoding="utf-8", errors="replace"
            )
            self.message_count += 1
            return result.returncode == 0
        except Exception as e:
            print(f"[Telegram] Error: {e}")
            return False

    def receive(self, timeout: int = 30) -> str | None:
        import subprocess
        try:
            result = subprocess.run(
                [sys.executable, self.script, "listen"],
                capture_output=True, text=True, timeout=timeout,
                encoding="utf-8", errors="replace"
            )
            if result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def format_message(self, message: str, context: dict = None) -> str:
        # Telegram soporta markdown básico
        return message

    def is_available(self) -> bool:
        return os.path.exists(self.script)


class DiscordAdapter(ChannelAdapter):
    """Adaptador para Discord usando webhooks o bot."""

    def __init__(self, config: dict = None):
        super().__init__("discord", config)
        self.webhook_url = (config or {}).get("webhook_url", "")
        self.bot_token = (config or {}).get("bot_token", "")

    def send(self, message: str, **kwargs) -> bool:
        if not self.webhook_url:
            print("[Discord] No configurado (falta webhook_url)")
            return False
        try:
            import requests
            formatted = self.format_message(message)
            # Discord webhook: máx 2000 chars
            chunks = [formatted[i:i+1900] for i in range(0, len(formatted), 1900)]
            for chunk in chunks:
                resp = requests.post(
                    self.webhook_url,
                    json={"content": chunk},
                    timeout=10
                )
                if resp.status_code not in (200, 204):
                    print(f"[Discord] Error HTTP {resp.status_code}")
                    return False
            self.message_count += 1
            return True
        except Exception as e:
            print(f"[Discord] Error: {e}")
            return False

    def receive(self, timeout: int = 30) -> str | None:
        # Discord receive requiere un bot con gateway (más complejo)
        # Por ahora, solo soportamos envío via webhook
        return None

    def format_message(self, message: str, context: dict = None) -> str:
        # Discord usa markdown estándar
        return message

    def is_available(self) -> bool:
        return bool(self.webhook_url)


class SlackAdapter(ChannelAdapter):
    """Adaptador para Slack usando webhooks."""

    def __init__(self, config: dict = None):
        super().__init__("slack", config)
        self.webhook_url = (config or {}).get("webhook_url", "")

    def send(self, message: str, **kwargs) -> bool:
        if not self.webhook_url:
            print("[Slack] No configurado (falta webhook_url)")
            return False
        try:
            import requests
            formatted = self.format_message(message)
            resp = requests.post(
                self.webhook_url,
                json={"text": formatted},
                timeout=10
            )
            self.message_count += 1
            return resp.status_code == 200
        except Exception as e:
            print(f"[Slack] Error: {e}")
            return False

    def receive(self, timeout: int = 30) -> str | None:
        return None

    def format_message(self, message: str, context: dict = None) -> str:
        # Slack usa mrkdwn (similar a markdown pero con diferencias)
        return message

    def is_available(self) -> bool:
        return bool(self.webhook_url)


class TeamsAdapter(ChannelAdapter):
    """Adaptador para Microsoft Teams usando webhooks."""

    def __init__(self, config: dict = None):
        super().__init__("teams", config)
        self.webhook_url = (config or {}).get("webhook_url", "")

    def send(self, message: str, **kwargs) -> bool:
        if not self.webhook_url:
            print("[Teams] No configurado (falta webhook_url)")
            return False
        try:
            import requests
            formatted = self.format_message(message)
            payload = {
                "type": "message",
                "attachments": [{
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [{"type": "TextBlock", "text": formatted, "wrap": True}]
                    }
                }]
            }
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            self.message_count += 1
            return resp.status_code in (200, 202)
        except Exception as e:
            print(f"[Teams] Error: {e}")
            return False

    def receive(self, timeout: int = 30) -> str | None:
        return None

    def is_available(self) -> bool:
        return bool(self.webhook_url)


class MondayAdapter(ChannelAdapter):
    """Adaptador para Monday.com usando GraphQL API v2."""

    def __init__(self, config: dict = None):
        super().__init__("monday", config)
        self.api_token = (config or {}).get("api_token", "")
        self.board_id = (config or {}).get("board_id", "")
        self.api_url = "https://api.monday.com/v2"

    def send(self, message: str, **kwargs) -> bool:
        """Crea un nuevo item (tarea) en el tablero de Monday."""
        if not self.api_token or not self.board_id:
            print("[Monday] No configurado correctamente")
            return False
        try:
            import requests
            headers = {
                "Authorization": self.api_token,
                "Content-Type": "application/json",
                "API-Version": "2023-10"
            }
            # GraphQL Mutation para crear item
            query = "mutation ($name: String!, $board_id: ID!) { create_item (board_id: $board_id, item_name: $name) { id } }"
            variables = {
                "name": message,
                "board_id": str(self.board_id)
            }
            resp = requests.post(
                self.api_url, 
                json={"query": query, "variables": variables}, 
                headers=headers,
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                if "errors" in data:
                    print(f"[Monday] Errores GraphQL: {data['errors']}")
                    return False
                self.message_count += 1
                return True
            else:
                print(f"[Monday] Error API: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            print(f"[Monday] Error: {e}")
            return False

    def receive(self, timeout: int = 30) -> str | None:
        """Consulta los items (tareas) del tablero."""
        # Polling básico de tareas si se requiere
        return None

    def is_available(self) -> bool:
        return bool(self.api_token and self.board_id)


class N8NAdapter(ChannelAdapter):
    """Adaptador para n8n usando Webhooks de entrada."""

    def __init__(self, config: dict = None):
        super().__init__("n8n", config)
        self.webhook_url = (config or {}).get("webhook_url", "")

    def send(self, message: str, **kwargs) -> bool:
        """Envía datos a un webhook de n8n."""
        if not self.webhook_url:
            print("[n8n] No configurado (falta webhook_url)")
            return False
        try:
            import requests
            payload = {
                "ts": datetime.now().isoformat(),
                "agent": "Enjambre",
                "message": message,
                "context": kwargs.get("context", {})
            }
            resp = requests.post(self.webhook_url, json=payload, timeout=15)
            if resp.status_code in (200, 201):
                self.message_count += 1
                return True
            else:
                print(f"[n8n] Error API: {resp.status_code}")
                return False
        except Exception as e:
            print(f"[n8n] Error: {e}")
            return False

    def receive(self, timeout: int = 30) -> str | None:
        return None

    def is_available(self) -> bool:
        return bool(self.webhook_url)


# ══════════════════════════════════════════════════════════════════
#  ROUTER MULTICANAL
# ══════════════════════════════════════════════════════════════════
class ChannelRouter:
    """
    Dirige mensajes al canal correcto.
    Soporta envío a un canal específico o broadcast a todos.
    """

    def __init__(self):
        self.adapters: dict[str, ChannelAdapter] = {}
        self._load_config()

    def _load_config(self):
        """Carga configuración de canales y registra adaptadores."""
        # Telegram siempre disponible
        self.register("telegram", TelegramAdapter())

        # Cargar config adicional
        if os.path.exists(CHANNELS_CONFIG):
            try:
                with open(CHANNELS_CONFIG, "r", encoding="utf-8") as f:
                    config = json.load(f)
                for ch_name, ch_config in config.get("channels", {}).items():
                    if not ch_config.get("enabled", False):
                        continue
                    if ch_name == "discord":
                        self.register("discord", DiscordAdapter(ch_config))
                    elif ch_name == "slack":
                        self.register("slack", SlackAdapter(ch_config))
                    elif ch_name == "teams":
                        self.register("teams", TeamsAdapter(ch_config))
                    elif ch_name == "monday":
                        self.register("monday", MondayAdapter(ch_config))
                    elif ch_name == "n8n":
                        self.register("n8n", N8NAdapter(ch_config))
            except Exception as e:
                print(f"[Router] Error cargando config: {e}")

    def register(self, name: str, adapter: ChannelAdapter):
        """Registra un adaptador de canal."""
        self.adapters[name] = adapter

    def send(self, channel: str, message: str, **kwargs) -> bool:
        """Envía a un canal específico."""
        adapter = self.adapters.get(channel)
        if not adapter:
            print(f"[Router] Canal '{channel}' no registrado")
            return False
        if not adapter.is_available():
            print(f"[Router] Canal '{channel}' no disponible")
            return False
        success = adapter.send(message, **kwargs)
        self._log_message(channel, message, success)
        return success

    def broadcast(self, message: str, exclude: list[str] = None) -> dict:
        """Envía a todos los canales activos."""
        exclude = exclude or []
        results = {}
        for name, adapter in self.adapters.items():
            if name in exclude:
                continue
            if adapter.is_available():
                results[name] = adapter.send(message)
                self._log_message(name, message, results[name])
        return results

    def receive(self, channel: str, timeout: int = 30) -> str | None:
        """Recibe de un canal específico."""
        adapter = self.adapters.get(channel)
        if adapter:
            return adapter.receive(timeout)
        return None

    def get_status(self) -> dict:
        """Estado de todos los canales."""
        return {
            name: adapter.get_stats()
            for name, adapter in self.adapters.items()
        }

    def _log_message(self, channel: str, message: str, success: bool):
        """Log de mensajes enviados."""
        logs = []
        if os.path.exists(MESSAGE_LOG):
            try:
                with open(MESSAGE_LOG, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except Exception:
                pass
        logs.append({
            "ts": datetime.now().isoformat(),
            "channel": channel,
            "message": message[:200],
            "success": success
        })
        logs = logs[-100:]  # Últimos 100
        with open(MESSAGE_LOG, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)


# ── Config template ────────────────────────────────────────────────
def create_default_config():
    """Crea configuración por defecto para los canales."""
    config = {
        "channels": {
            "discord": {
                "enabled": False,
                "webhook_url": "",
                "bot_token": "",
                "description": "Discord webhook para notificaciones"
            },
            "slack": {
                "enabled": False,
                "webhook_url": "",
                "description": "Slack webhook para notificaciones"
            },
            "teams": {
                "enabled": False,
                "webhook_url": "",
                "description": "Microsoft Teams webhook"
            }
        }
    }
    with open(CHANNELS_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"[Router] Config creada: {CHANNELS_CONFIG}")
    return config


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python channel_adapter.py status")
        print("  python channel_adapter.py send telegram \"mensaje\"")
        print("  python channel_adapter.py broadcast \"mensaje\"")
        print("  python channel_adapter.py init-config")
        sys.exit(1)

    cmd = sys.argv[1]
    router = ChannelRouter()

    if cmd == "status":
        status = router.get_status()
        print(f"\nCANALES ({len(status)}):\n")
        for name, s in status.items():
            icon = "🟢" if s["active"] else "🔴"
            print(f"  {icon} {name}: {s['messages_sent']} mensajes")

    elif cmd == "send" and len(sys.argv) >= 4:
        channel = sys.argv[2]
        message = " ".join(sys.argv[3:])
        ok = router.send(channel, message)
        print(f"{'OK' if ok else 'FAIL'}: {channel}")

    elif cmd == "broadcast" and len(sys.argv) >= 3:
        message = " ".join(sys.argv[2:])
        results = router.broadcast(message)
        for ch, ok in results.items():
            print(f"  {'OK' if ok else 'FAIL'}: {ch}")

    elif cmd == "init-config":
        create_default_config()

    else:
        print(f"Comando desconocido: {cmd}")
