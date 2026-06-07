#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
synthesis_reporter.py — Centinela de Reportes de Síntesis Académica
=================================================================
Monitorea en segundo plano el progreso del motor de compilación de lecciones.
Envía un reporte detallado a Telegram cada 30 minutos indicando la cantidad procesada,
el restante, y el tiempo de GPU estimado, hasta confirmar la finalización.

Diseñado por Enjambre para el ecosistema Chask Swarm de Fernando Enjambre.
"""

import os
import sys
import time
from datetime import datetime
import subprocess
from qdrant_client import QdrantClient

# Forzar codificación UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

EXPORT_DIR = r"C:\Users\fnora\Desktop\Enjambre Datos\Lecciones_Sintetizadas"
TELEGRAM_SCRIPT = r"C:\Program Files\Chask_Swarm\charm_telegram.py"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "synthesized_academic_lessons"
TOTAL_LESSONS = 31
ESTIMATED_SEC_PER_LESSON = 50

def get_compiled_count() -> int:
    """Cuenta cuántas lecciones granulares estructuradas (01 a 31) existen en disco."""
    if not os.path.exists(EXPORT_DIR):
        return 0
    count = 0
    for f in os.listdir(EXPORT_DIR):
        if f.endswith(".md") and f[:2].isdigit():
            val = int(f[:2])
            if 1 <= val <= TOTAL_LESSONS:
                count += 1
    return count

def get_qdrant_count() -> int:
    """Obtiene la cantidad de lecciones indexadas en la colección de Qdrant."""
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        if client.collection_exists(COLLECTION_NAME):
            return client.get_collection(COLLECTION_NAME).points_count
    except Exception:
        pass
    return 0

def send_telegram(msg: str):
    """Llama a charm_telegram.py para enviar el mensaje."""
    try:
        subprocess.run(
            ["python", TELEGRAM_SCRIPT, "send", msg],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
    except Exception:
        pass

def main():
    # Enviar reporte inicial de inmediato
    send_report(is_initial=True)
    
    # Bucle periódico de 30 minutos (1800 segundos)
    while True:
        time.sleep(1800)
        send_report()

def send_report(is_initial=False):
    processed = get_compiled_count()
    qdrant_indexed = get_qdrant_count()
    
    remaining = TOTAL_LESSONS - processed
    if remaining < 0:
        remaining = 0
        
    percentage = (processed / TOTAL_LESSONS) * 100
    
    # Calcular tiempo estimado restante
    est_seconds_left = remaining * ESTIMATED_SEC_PER_LESSON
    if est_seconds_left > 0:
        minutes = est_seconds_left // 60
        seconds = est_seconds_left % 60
        time_str = f"{minutes}m {seconds}s"
    else:
        time_str = "0s (Completado)"
        
    status_emoji = "⏳"
    if processed >= TOTAL_LESSONS:
        status_emoji = "✅"
        
    tag = "[REPORTE INICIAL]" if is_initial else "[REPORTE PERIÓDICO]"
    
    msg = (
        f"{status_emoji} {tag} **Estado de la Síntesis Curricular**\n"
        f"• **Procesadas:** {processed}/{TOTAL_LESSONS} lecciones ({percentage:.1f}%)\n"
        f"• **Faltantes:** {remaining} lecciones\n"
        f"• **Indexadas en Qdrant:** {qdrant_indexed}/{TOTAL_LESSONS} puntos\n"
        f"• **Tiempo estimado restante:** {time_str}\n"
        f"• **Estado del motor:** {'En ejecución' if remaining > 0 else 'Finalizado con éxito'}\n"
        f"• **Fecha/Hora:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    )
    
    send_telegram(msg)

if __name__ == "__main__":
    main()
