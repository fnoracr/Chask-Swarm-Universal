"""
CHASK HIVE — CONFIG DE CONEXIÓN Y CREDENCIALES
================================================
Este script se ejecuta automáticamente en la primera instalación
o cuando el usuario quiere reconfigurar el sistema.

Qué hace:
1. Pide o actualiza el Token del bot de Telegram y el Admin ID.
2. Escribe master_credentials.json con los valores correctos.
3. Verifica la conexión con Telegram.
4. Guarda la configuración base en Qdrant (colección charm_memory).
5. Ejecuta diagnostics.py para confirmar que todo está OK.
"""
import os, sys, json, requests

BASE_DIR    = os.path.dirname(os.path.dirname(__file__))  # Telegram_Bot_Scripts/
CONFIG_PATH = os.path.join(BASE_DIR, "Configuration", "master_credentials.json")
FFMPEG_PATH = os.path.join(BASE_DIR, "Binaries", "ffmpeg.exe")

QDRANT_HOST       = "localhost"
QDRANT_PORT       = 6333
QDRANT_COLLECTION = "charm_memory"   # nombre fijo de la colección

def load_existing():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

def save_config(token, admin_id, ffmpeg):
    cfg = {"telegram_bot": token, "telegram_admin": admin_id, "ffmpeg_path": ffmpeg}
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
    print("[OK] master_credentials.json guardado.")

def verify_telegram(token):
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5).json()
        if r.get("ok"):
            print(f"[OK] Bot Telegram verificado: @{r['result']['username']}")
            return True
        print(f"[FALLO] Token inválido: {r}")
    except Exception as e:
        print(f"[FALLO] Sin conexión a Telegram: {e}")
    return False

def save_to_qdrant(token, admin_id):
    """Guarda la configuración del sistema en Qdrant (sin datos sensibles reales)."""
    try:
        sys.path.insert(0, BASE_DIR)
        from Advanced_Tools.qdrant_memory_manager import init_db, index_memory
        init_db()
        index_memory(
            text=(
                f"CONFIGURACION DEL SISTEMA CHASK HIVE. "
                f"Qdrant: {QDRANT_HOST}:{QDRANT_PORT}, coleccion '{QDRANT_COLLECTION}'. "
                f"Telegram bot configurado y verificado. "
                f"FFmpeg disponible: {os.path.exists(FFMPEG_PATH)}. "
                f"Instalacion completada."
            ),
            keywords=["config","sistema","qdrant","telegram","instalacion","setup"],
            project_name="Chask_Hive_Core"
        )
        print("[OK] Configuración guardada en Qdrant.")
    except Exception as e:
        print(f"[AVISO] No se pudo guardar en Qdrant: {e}")

def main():
    print("\n" + "="*55)
    print("  CHASK HIVE — ASISTENTE DE CONFIGURACIÓN INICIAL")
    print("="*55 + "\n")

    existing = load_existing()
    has_config = (
        existing.get("telegram_bot","").strip() not in ("", "AQUI_VA_EL_TOKEN_DE_TU_BOT") and
        existing.get("telegram_admin","").strip() not in ("", "AQUI_VA_TU_ID_DE_USUARIO")
    )

    if has_config:
        print("Ya existe una configuración previa. ¿Deseas reconfigurar? (s/N): ", end="")
        if input().strip().lower() != "s":
            print("Configuración sin cambios.")
            save_to_qdrant(existing["telegram_bot"], existing["telegram_admin"])
            return

    print("Paso 1/3: Token del bot de Telegram")
    print("  (Obtén uno en @BotFather con /newbot)")
    token = input("  Token: ").strip()
    if not token:
        print("[ABORTADO] Token vacío.")
        return

    print("\nPaso 2/3: Tu ID numérico de Telegram")
    print("  (Consúltalo en @userinfobot)")
    admin_id = input("  ID: ").strip()
    if not admin_id:
        print("[ABORTADO] ID vacío.")
        return

    ffmpeg = FFMPEG_PATH if os.path.exists(FFMPEG_PATH) else input(
        "\nPaso 2b: Ruta a ffmpeg.exe (o ENTER para omitir audios): "
    ).strip() or FFMPEG_PATH

    print("\nPaso 3/3: Verificando conexión con Telegram...")
    ok = verify_telegram(token)

    save_config(token, admin_id, ffmpeg)
    if ok:
        save_to_qdrant(token, admin_id)

    print("\nEjecutando diagnóstico del sistema...")
    import subprocess
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "Advanced_Tools", "diagnostics.py")])

    print("\n" + "="*55)
    print("  CONFIGURACIÓN COMPLETADA")
    print(f"  Inicia el sistema con: python telegram_daemon.py")
    print("="*55 + "\n")

if __name__ == "__main__":
    main()
