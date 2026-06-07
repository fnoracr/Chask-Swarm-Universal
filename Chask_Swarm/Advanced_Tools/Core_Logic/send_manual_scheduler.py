"""
send_manual_scheduler.py — Programador en segundo plano para el envío del Manual Técnico.
Calcula el objetivo (las 07:00:00 del 20 de Mayo de 2026) y ejecuta una espera de alta precisión.
A la hora exacta, envía el Manual compilado premium en formato HTML a Fernando vía Telegram.
"""
import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta

CONFIG_PATH = r"C:\Program Files\Chask_Swarm\Configuracion\master_credentials.json"
MANUAL_PATH = r"C:\Users\fnora\Desktop\Enjambre Datos\Manual_Enjambre_Chask_Swarm.html"
LOG_PATH = r"C:\Program Files\Chask_Swarm\Advanced_Tools\scheduler.log"


def log_status(message: str):
    """Escribe un mensaje de log con timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")


def load_telegram_credentials() -> tuple[str, str]:
    """Carga el token del bot y el chat_id del administrador de master_credentials.json."""
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Configuración no encontrada en {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    creds = data["credentials"]
    return creds["telegram_bot"], creds["telegram_admin"]


def send_manual_document():
    """Envía el archivo HTML del manual al administrador vía Telegram."""
    try:
        token, admin_id = load_telegram_credentials()
        
        # 1. Enviar mensaje de introducción
        url_text = f"https://api.telegram.org/bot{token}/sendMessage"
        intro_text = (
            "📖 *[SISTEMA DE AGENTES AUTÓNOMOS]*\n\n"
            "Buenos días. Son las *07:00 AM*. Conforme a las directivas operativas programadas, "
            "he finalizado y compilado el *Manual General de Ingeniería de Sistemas: Enjambre de Agentes & Core Engine*.\n\n"
            "Este documento exhaustivo abarca 6 capítulos detallados (50 secciones) "
            "con toda la arquitectura conceptual, daemons centinela, bases de datos vectoriales y biblioteca de habilidades. "
            "Ha sido renderizado de forma automatizada aplicando el estilo *Midnight Purple*.\n\n"
            "Adjunto el manual en formato HTML interactivo a continuación. ¡Que tenga una excelente jornada de control y desarrollo!"
        )
        payload = {"chat_id": admin_id, "text": intro_text, "parse_mode": "Markdown"}
        requests.post(url_text, json=payload)
        log_status("Mensaje introductorio enviado a Telegram con éxito.")

        # 2. Enviar el archivo HTML adjunto
        url_doc = f"https://api.telegram.org/bot{token}/sendDocument"
        if os.path.exists(MANUAL_PATH):
            with open(MANUAL_PATH, "rb") as f:
                files = {"document": f}
                data = {
                    "chat_id": admin_id,
                    "caption": "📖 Manual Técnico Chask Swarm & Enjambre Core",
                    "parse_mode": "Markdown"
                }
                resp = requests.post(url_doc, data=data, files=files)
                if resp.status_code == 200:
                    log_status("Documento HTML del Manual enviado a Telegram con éxito.")
                else:
                    log_status(f"Error al enviar documento (HTTP {resp.status_code}): {resp.text}")
        else:
            log_status(f"Error: El archivo del manual no se encuentra en {MANUAL_PATH}")
            
    except Exception as e:
        log_status(f"EXCEPCIÓN CRÍTICA en el envío de Telegram: {e}")


def main():
    log_status("PROGRAMADOR DE MANUAL INICIADO EN SEGUNDO PLANO SILENCIOSO.")
    
    # Calcular el datetime objetivo: hoy a las 07:00:00
    now = datetime.now()
    target_time = datetime(now.year, now.month, now.day, 7, 0, 0)
    
    # Si por algún retraso ya son pasadas las 07:00, programar para mañana a las 7:00
    if now >= target_time:
        target_time = target_time + timedelta(days=1)
        
    wait_seconds = (target_time - now).total_seconds()
    log_status(f"Objetivo de tiempo fijado: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_status(f"Tiempo de espera calculado: {wait_seconds:.1f} segundos (~{wait_seconds / 3600:.2f} horas)")
    
    # Espera inteligente en bucle para permitir lecturas del watchdog
    sent = False
    while not sent:
        now_check = datetime.now()
        if now_check >= target_time:
            log_status("ALCANZADA LA HORA OBJETIVO (07:00:00). Lanzando envío síncrono del manual...")
            send_manual_document()
            sent = True
            log_status("Envío completado. Finalizando servicio programador.")
            break
        
        # Dormir 15 segundos antes de re-comprobar
        time.sleep(15)


if __name__ == "__main__":
    main()
