import json, requests
cfg = json.load(open(r"C:\Program Files\Chask_Swarm\telegram_config.json"))
url = f"https://api.telegram.org/bot{cfg['telegram_bot']}/sendDocument"
with open(r"C:\Users\fnora\Desktop\plan_implementacion_nora.html", "rb") as f:
    r = requests.post(url, data={
        "chat_id": cfg["telegram_admin"],
        "caption": "Plan de Implementacion - 8 Capacidades Faltantes\n4 fases | 8 ficheros nuevos | 14-20h | Coste: 0 euros\nTodas implementables con Antigravity. Esperando tu OK."
    }, files={"document": ("plan_implementacion_nora.html", f)})
print("OK" if r.status_code == 200 else r.text[:200])
