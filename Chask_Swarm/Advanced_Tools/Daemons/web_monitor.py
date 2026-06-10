"""
web_monitor.py — Agente de monitorización web autónoma
Vigila URLs en background y alerta por Telegram si se cumplen condiciones.
Config en: Advanced_Tools/Daemons/web_monitor_config.json
"""
import os, json, time, re, requests, schedule, subprocess
from datetime import datetime

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_FILE = os.path.join(BASE_DIR, "Advanced_Tools", "web_monitor_config.json")
TG_SCRIPT   = os.path.join(BASE_DIR, "charm_telegram.py")

DEFAULT_CONFIG = {
    "monitors": [
        {
            "name": "Ejemplo — precio Amazon",
            "url": "https://www.amazon.es/dp/ASIN",
            "condition": "precio_menor",
            "threshold": 40.0,
            "keyword": None,
            "interval_hours": 6,
            "active": False
        }
    ]
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)

def send_telegram(message: str):
    try:
        subprocess.run(
            [__import__("sys").executable, TG_SCRIPT, "send", message],
            capture_output=True, timeout=15
        )
    except Exception as e:
        print(f"[WebMonitor] Error Telegram: {e}")

def check_monitor(monitor: dict):
    if not monitor.get("active", False):
        return
    name = monitor["name"]
    url  = monitor["url"]
    try:
        r = requests.get(url, timeout=15,
                         headers={"User-Agent": "Mozilla/5.0"})
        html = r.text

        # Condición: keyword presente
        if monitor.get("keyword"):
            if monitor["keyword"].lower() in html.lower():
                send_telegram(
                    f"🔔 [{name}] Keyword '{monitor['keyword']}' detectada en {url}"
                )

        # Condición: precio menor que umbral
        elif monitor.get("condition") == "precio_menor":
            prices = re.findall(r'[\d]+[.,][\d]{2}', html)
            if prices:
                price = float(prices[0].replace(",", "."))
                if price < monitor.get("threshold", 9999):
                    send_telegram(
                        f"💰 [{name}] Precio {price}€ < umbral {monitor['threshold']}€\n{url}"
                    )

        print(f"[WebMonitor] {datetime.now().strftime('%H:%M')} — Revisado: {name}")
    except Exception as e:
        print(f"[WebMonitor] Error revisando {name}: {e}")

def run_all():
    config = load_config()
    for m in config.get("monitors", []):
        check_monitor(m)

def run_daemon():
    config = load_config()
    print(f"[WebMonitor] Daemon iniciado. {len(config['monitors'])} monitores cargados.")
    # Programar según interval_hours de cada monitor
    for m in config.get("monitors", []):
        if m.get("active"):
            h = m.get("interval_hours", 6)
            schedule.every(h).hours.do(check_monitor, m)
            print(f"  ✓ {m['name']} — cada {h}h")
    # Primera comprobación inmediata
    run_all()
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        run_all()
    else:
        run_daemon()
