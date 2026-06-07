"""
teams_adapter.py — Bot Microsoft Teams para Chask Swarm
=========================================================
Bot Teams con:
- Envío via Incoming Webhook (Adaptive Cards)
- Envío via Power Automate webhook
- Formato rich con Adaptive Cards
- Cola de mensajes integrada

Uso:
  python teams_adapter.py send "Mensaje"
  python teams_adapter.py send-card "Título" "Texto" 
  python teams_adapter.py status
"""
import os
import sys
import io
import json
from datetime import datetime

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "Configuracion", "channels_config.json")


def _get_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return cfg.get("channels", {}).get("teams", {})
        except Exception:
            pass
    return {}


class TeamsBot:
    """Bot Microsoft Teams via Webhooks y Adaptive Cards."""

    def __init__(self):
        self.config = _get_config()
        self.webhook_url = self.config.get("webhook_url", "")
        self.power_automate_url = self.config.get("power_automate_webhook", "")

    def send(self, text: str) -> bool:
        """Envía mensaje simple via webhook."""
        if not self.webhook_url:
            print("[Teams] No configurado (falta webhook_url)")
            return False

        try:
            import requests
            # Workflow webhook (nuevo formato)
            payload = {
                "type": "message",
                "attachments": [{
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [{
                            "type": "TextBlock",
                            "text": text,
                            "wrap": True
                        }]
                    }
                }]
            }
            resp = requests.post(self.webhook_url, json=payload, timeout=15)
            return resp.status_code in (200, 202)
        except Exception as e:
            print(f"[Teams] Error: {e}")
            return False

    def send_card(self, title: str, text: str, facts: dict = None,
                  color: str = "Good", actions: list = None) -> bool:
        """
        Envía Adaptive Card rica.
        
        Args:
            title: Título de la card
            text: Texto principal
            facts: Dict de key-value para mostrar
            color: Good|Warning|Attention
            actions: Lista de botones [{"title": "Click", "url": "https://..."}]
        """
        if not self.webhook_url:
            print("[Teams] No configurado")
            return False

        body = [
            {
                "type": "TextBlock",
                "text": title,
                "weight": "Bolder",
                "size": "Large",
                "color": color
            },
            {
                "type": "TextBlock",
                "text": text,
                "wrap": True
            }
        ]

        if facts:
            fact_set = {
                "type": "FactSet",
                "facts": [{"title": k, "value": str(v)} for k, v in facts.items()]
            }
            body.append(fact_set)

        body.append({
            "type": "TextBlock",
            "text": f"Enjambre · {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "size": "Small",
            "color": "Light",
            "isSubtle": True
        })

        card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body
        }

        if actions:
            card["actions"] = [
                {
                    "type": "Action.OpenUrl",
                    "title": a.get("title", "Link"),
                    "url": a.get("url", "")
                }
                for a in actions
            ]

        try:
            import requests
            payload = {
                "type": "message",
                "attachments": [{
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": card
                }]
            }
            resp = requests.post(self.webhook_url, json=payload, timeout=15)
            return resp.status_code in (200, 202)
        except Exception as e:
            print(f"[Teams] Error: {e}")
            return False

    def send_via_power_automate(self, data: dict) -> bool:
        """
        Envía datos a un flujo de Power Automate que notifica en Teams.
        Útil para flujos que necesitan procesamiento adicional.
        """
        if not self.power_automate_url:
            print("[Teams] Power Automate webhook no configurado")
            return False

        try:
            import requests
            resp = requests.post(
                self.power_automate_url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            return resp.status_code in (200, 202)
        except Exception as e:
            print(f"[Teams] Error PA: {e}")
            return False

    def send_alert(self, level: str, message: str, details: dict = None) -> bool:
        """Envía alerta con formato predefinido según nivel."""
        colors = {"critical": "Attention", "warning": "Warning", "info": "Good"}
        icons = {"critical": "🔴", "warning": "⚠️", "info": "ℹ️"}

        return self.send_card(
            title=f"{icons.get(level, 'ℹ️')} [{level.upper()}] Alerta Chask Swarm",
            text=message,
            facts=details,
            color=colors.get(level, "Default")
        )

    def get_status(self) -> dict:
        return {
            "configured": bool(self.webhook_url),
            "webhook_set": bool(self.webhook_url),
            "power_automate_set": bool(self.power_automate_url)
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python teams_adapter.py send \"mensaje\"")
        print("  python teams_adapter.py send-card \"titulo\" \"texto\"")
        print("  python teams_adapter.py alert critical \"Sistema caido\"")
        print("  python teams_adapter.py status")
        sys.exit(1)

    bot = TeamsBot()
    cmd = sys.argv[1]

    if cmd == "send" and len(sys.argv) >= 3:
        msg = " ".join(sys.argv[2:])
        ok = bot.send(msg)
        print(f"{'OK' if ok else 'FAIL'}")

    elif cmd == "send-card" and len(sys.argv) >= 4:
        title = sys.argv[2]
        text = " ".join(sys.argv[3:])
        ok = bot.send_card(title, text)
        print(f"{'OK' if ok else 'FAIL'}")

    elif cmd == "alert" and len(sys.argv) >= 4:
        level = sys.argv[2]
        msg = " ".join(sys.argv[3:])
        ok = bot.send_alert(level, msg)
        print(f"{'OK' if ok else 'FAIL'}")

    elif cmd == "status":
        status = bot.get_status()
        print("\nTEAMS STATUS:")
        for k, v in status.items():
            print(f"  {k}: {v}")

    else:
        print(f"Comando desconocido: {cmd}")
