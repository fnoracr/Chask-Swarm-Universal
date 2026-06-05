# Chask Hive — Credenciales y Configuración

Esta carpeta contiene los scripts de configuración inicial de Chask Hive.

## Contenido

| Archivo | Descripción |
|---|---|
| `setup_inicial.py` | Asistente de primera configuración: pide Token y Admin ID de Telegram, verifica la conexión y guarda la config en Qdrant |

## Valores de conexión del sistema (no sensibles)

| Parámetro | Valor |
|---|---|
| **Qdrant host** | `localhost` |
| **Qdrant puerto** | `6333` |
| **Colección Qdrant** | `charm_memory` |
| **Volumen Docker** | `qdrant_storage` |
| **Config Telegram** | `../telegram_config.json` |

## Cómo usar en una instalación nueva

1. Instalar dependencias: `pip install requests pydub SpeechRecognition pygetwindow pyautogui pyperclip gtts qdrant-client plyer`
2. Asegurarse de que Docker Desktop está corriendo
3. Lanzar Qdrant: `docker run -d --name qdrant --restart=always -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant`
4. Ejecutar este asistente: `python Chask_Hive_Credenciales_y_Config/setup_inicial.py`
5. Iniciar el daemon: `python telegram_daemon.py`

> **Nota de seguridad:** El archivo `telegram_config.json` contiene el Token del bot y el Admin ID.
> No lo compartas ni lo subas a repositorios públicos.
