"""
slack_adapter.py — Bot Slack Bidireccional para Chask Swarm
=============================================================
Bot Slack completo con:
- Envío de mensajes via API y webhook
- Recepción de mensajes via Socket Mode (sin servidor público)
- Slash commands (/enjambre status, /enjambre ask, etc.)
- Formato rich (Blocks API)

Requiere: pip install slack-sdk slack-bolt

Uso:
  python slack_adapter.py send "#general" "Mensaje"
  python slack_adapter.py listen   (inicia Socket Mode)
  python slack_adapter.py status
"""
import os
import sys
import io
import json
from datetime import datetime

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "Configuracion", "channels_config.json")

# Cargar config
def _get_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return cfg.get("channels", {}).get("slack", {})
        except Exception:
            pass
    return {}


class SlackBot:
    """Bot Slack con API completa."""

    def __init__(self):
        self.config = _get_config()
        self.bot_token = self.config.get("bot_token", "")
        self.app_token = self.config.get("app_token", "")
        self.webhook_url = self.config.get("webhook_url", "")
        self.default_channel = self.config.get("default_channel", "#general")
        self.client = None
        self._init_client()

    def _init_client(self):
        if not self.bot_token:
            return
        try:
            from slack_sdk import WebClient
            self.client = WebClient(token=self.bot_token)
        except ImportError:
            print("[Slack] slack-sdk no instalado. Usa: pip install slack-sdk")

    def send(self, channel: str = None, text: str = "", blocks: list = None) -> bool:
        """Envía mensaje via API (preferido) o webhook (fallback)."""
        channel = channel or self.default_channel

        # Intentar API primero
        if self.client:
            try:
                result = self.client.chat_postMessage(
                    channel=channel,
                    text=text,
                    blocks=blocks
                )
                return result["ok"]
            except Exception as e:
                print(f"[Slack] Error API: {e}")

        # Fallback webhook
        if self.webhook_url:
            try:
                import requests
                payload = {"text": text, "channel": channel}
                if blocks:
                    payload["blocks"] = blocks
                resp = requests.post(self.webhook_url, json=payload, timeout=10)
                return resp.status_code == 200
            except Exception as e:
                print(f"[Slack] Error webhook: {e}")

        print("[Slack] No configurado (falta bot_token o webhook_url)")
        return False

    def send_rich(self, channel: str = None, title: str = "", text: str = "",
                  color: str = "#00f5d4", fields: dict = None) -> bool:
        """Envía mensaje rich con blocks de Slack."""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": title}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": text}
            }
        ]
        if fields:
            field_blocks = [
                {"type": "mrkdwn", "text": f"*{k}*\n{v}"}
                for k, v in fields.items()
            ]
            blocks.append({"type": "section", "fields": field_blocks})

        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"_Nora · {datetime.now().strftime('%H:%M')}_"}]
        })

        return self.send(channel, text=title, blocks=blocks)

    def listen(self):
        """Inicia escucha via Socket Mode (requiere app_token)."""
        if not self.app_token:
            print("[Slack] Socket Mode requiere app_token (xapp-...).")
            print("[Slack] Configura en channels_config.json > slack > app_token")
            return

        try:
            from slack_bolt import App
            from slack_bolt.adapter.socket_mode import SocketModeHandler
        except ImportError:
            print("[Slack] Instala: pip install slack-bolt")
            return

        app = App(token=self.bot_token)

        @app.message("")
        def handle_message(message, say):
            """Procesa mensajes entrantes."""
            text = message.get("text", "")
            user = message.get("user", "unknown")
            print(f"[Slack] Mensaje de {user}: {text}")

            # Encolar para procesamiento
            self._enqueue_message(text, user, message.get("channel", ""))

            # Respuesta automática simple
            say(f"Recibido. Procesando... _{datetime.now().strftime('%H:%M')}_")

        @app.command("/enjambre")
        def handle_chask_command(ack, command, respond):
            """Maneja el slash command /enjambre."""
            ack()
            cmd_text = command.get("text", "").strip()
            user = command.get("user_name", "unknown")
            print(f"[Slack] /enjambre {cmd_text} de {user}")

            if cmd_text == "status":
                respond("🟢 Enjambre online. Chask Swarm operativo.")
            elif cmd_text.startswith("ask "):
                question = cmd_text[4:]
                respond(f"Procesando pregunta: _{question}_")
                self._enqueue_message(question, user, command.get("channel_id", ""))
            else:
                respond(f"Comandos: `/enjambre status`, `/enjambre ask <pregunta>`")

        print("[Slack] Iniciando Socket Mode...")
        handler = SocketModeHandler(app, self.app_token)
        handler.start()

    def _enqueue_message(self, text: str, user: str, channel: str):
        """Encola mensaje para procesamiento."""
        queue_path = os.path.join(BASE_DIR, "Advanced_Tools", "Colas_Mensajes", "input_queue.json")
        queue = []
        if os.path.exists(queue_path):
            try:
                with open(queue_path, "r", encoding="utf-8") as f:
                    queue = json.load(f)
            except Exception:
                pass
        queue.append({
            "timestamp": datetime.now().isoformat(),
            "source": "slack",
            "user": user,
            "channel": channel,
            "text": text
        })
        with open(queue_path, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)

    def get_status(self) -> dict:
        """Estado de la conexión Slack."""
        status = {
            "configured": bool(self.bot_token or self.webhook_url),
            "api_available": self.client is not None,
            "webhook_available": bool(self.webhook_url),
            "socket_mode": bool(self.app_token),
            "default_channel": self.default_channel
        }
        if self.client:
            try:
                result = self.client.auth_test()
                status["bot_name"] = result.get("bot_id", "unknown")
                status["team"] = result.get("team", "unknown")
                status["connected"] = True
            except Exception:
                status["connected"] = False
        return status


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python slack_adapter.py send [#channel] \"mensaje\"")
        print("  python slack_adapter.py listen")
        print("  python slack_adapter.py status")
        sys.exit(1)

    bot = SlackBot()
    cmd = sys.argv[1]

    if cmd == "send" and len(sys.argv) >= 3:
        if sys.argv[2].startswith("#"):
            channel = sys.argv[2]
            msg = " ".join(sys.argv[3:])
        else:
            channel = None
            msg = " ".join(sys.argv[2:])
        ok = bot.send(channel, msg)
        print(f"{'OK' if ok else 'FAIL'}")

    elif cmd == "listen":
        bot.listen()

    elif cmd == "status":
        status = bot.get_status()
        print("\nSLACK STATUS:")
        for k, v in status.items():
            print(f"  {k}: {v}")

    else:
        print(f"Comando desconocido: {cmd}")
