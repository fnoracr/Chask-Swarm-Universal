import os
import sys
import json
import argparse
import subprocess
from typing import List, Dict

try:
    from openai import OpenAI
except ImportError:
    print("Error: El paquete 'openai' no está instalado. Ejecuta 'pip install openai'.")
    sys.exit(1)

# === Herramientas (Tools) ===
def tool_run_command(command: str) -> str:
    print(f"\n[Agent Tool] Ejecutando comando: {command}")
    try:
        # Importante: usar powershell o cmd
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True, text=True, timeout=120
        )
        output = result.stdout.strip()
        if result.stderr.strip():
            output += "\nSTDERR:\n" + result.stderr.strip()
        return output if output else "Comando ejecutado sin salida (éxito)."
    except Exception as e:
        return f"Error ejecutando comando: {e}"

def tool_read_file(path: str) -> str:
    print(f"\n[Agent Tool] Leyendo archivo: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error leyendo archivo: {e}"

def tool_write_file(path: str, content: str) -> str:
    print(f"\n[Agent Tool] Escribiendo archivo: {path}")
    try:
        # Crear directorios padres si no existen
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Archivo {path} escrito con éxito."
    except Exception as e:
        return f"Error escribiendo archivo: {e}"

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Ejecuta un comando en la terminal (PowerShell) y devuelve la salida. Úsalo para crear carpetas, listar archivos, instalar dependencias, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "El comando de PowerShell a ejecutar."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lee el contenido de un archivo en el sistema.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "La ruta absoluta del archivo a leer."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Crea o sobrescribe un archivo con nuevo contenido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "La ruta absoluta del archivo a crear/escribir."
                    },
                    "content": {
                        "type": "string",
                        "description": "El contenido a escribir en el archivo."
                    }
                },
                "required": ["path", "content"]
            }
        }
    }
]

# === Loop Principal del Agente ===
def autonomous_delegator(task: str, model: str):
    print(f"=== Iniciando Delegador Autónomo ===")
    print(f"Modelo Local: {model}")
    print(f"Tarea: {task}")
    print("===================================\n")

    # Cliente apuntando al endpoint local de Ollama (compatible con OpenAI)
    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama" # Requerido por el cliente, pero Ollama lo ignora
    )

    system_prompt = (
        "Eres un Agente Autónomo de Chask Swarm. Has sido invocado por Nora para resolver una tarea.\n"
        "Se te han proporcionado herramientas para interactuar con el sistema local (leer archivos, "
        "escribir archivos, y ejecutar comandos de PowerShell).\n"
        "Debes usar las herramientas para cumplir la tarea.\n"
        "IMPORTANTE: No te dirijas al usuario, tu objetivo es completar la tarea mecánicamente y "
        "cuando hayas terminado, emitir un reporte final detallando qué has hecho y qué descubriste."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task}
    ]

    max_steps = 15
    for step in range(1, max_steps + 1):
        print(f"[Iteración {step}/{max_steps}] Pensando...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto"
            )
        except Exception as e:
            print(f"\n[Error de Conexión] No se pudo contactar con Ollama en localhost:11434: {e}")
            print("Asegúrate de que Ollama está en ejecución y el modelo está instalado.")
            return

        response_message = response.choices[0].message
        
        # Ollama a veces puede retornar content nulo si solo llama a una herramienta
        if response_message.content:
            print(f"[Agente dice]: {response_message.content}")

        tool_calls = response_message.tool_calls
        
        # --- NUEVO: Fallback para modelos que escupen JSON en vez de usar la API nativa de tools ---
        if not tool_calls and response_message.content:
            try:
                import json
                text = response_message.content.strip()
                # A veces lo envuelven en bloques de markdown ```json ... ```
                if text.startswith("```json") and text.endswith("```"):
                    text = text[7:-3].strip()
                elif text.startswith("```") and text.endswith("```"):
                    text = text[3:-3].strip()
                
                parsed = json.loads(text)
                # Soportar formato {"name": "...", "arguments": {...}} 
                # o formato array de tools
                if isinstance(parsed, dict) and "name" in parsed and "arguments" in parsed:
                    class FakeFunction:
                        def __init__(self, name, args):
                            self.name = name
                            self.arguments = json.dumps(args) if isinstance(args, dict) else str(args)
                    class FakeToolCall:
                        def __init__(self, func):
                            self.id = "call_fake123"
                            self.function = func
                    tool_calls = [FakeToolCall(FakeFunction(parsed["name"], parsed["arguments"]))]
            except Exception:
                pass

        # Si no hay llamadas a herramientas (incluso después del fallback), significa que el agente ha finalizado
        if not tool_calls:
            print("\n=== Tarea Completada ===")
            print("El agente autónomo ha terminado y enviado su reporte final.")
            break

        # Si hay tool calls, añadimos el mensaje del asistente al historial
        # Convertimos la respuesta a un dict limpio compatible con OpenAI
        assist_msg = {"role": "assistant"}
        if response_message.content:
            assist_msg["content"] = response_message.content
        if tool_calls:
            assist_msg["tool_calls"] = []
            for tc in tool_calls:
                assist_msg["tool_calls"].append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })
        messages.append(assist_msg)

        # Ejecutamos las herramientas
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                args = {}
                print(f"[Warning] Argumentos JSON inválidos del modelo para la tool {function_name}")
            
            tool_result = ""
            if function_name == "run_command":
                tool_result = tool_run_command(args.get("command", ""))
            elif function_name == "read_file":
                tool_result = tool_read_file(args.get("path", ""))
            elif function_name == "write_file":
                tool_result = tool_write_file(args.get("path", ""), args.get("content", ""))
            else:
                tool_result = f"Error: Tool desconocida '{function_name}'"
            
            # Formatear la salida para evitar que sea inmensamente larga y rompa el contexto
            if len(tool_result) > 4000:
                tool_result = tool_result[:4000] + "\n...[Output Truncado]..."
            
            # Añadir el resultado de la herramienta al historial
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": str(tool_result)
            })

    if step == max_steps:
        print("\n[Warning] Se alcanzó el número máximo de iteraciones. El agente fue detenido preventivamente.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delegador Autónomo de Tareas para Modelos Locales")
    parser.add_argument("--task", required=True, help="La tarea que el modelo debe ejecutar")
    parser.add_argument("--model", default="qwen2.5-coder:7b", help="El modelo local de Ollama a utilizar (default: qwen2.5-coder:7b)")
    args = parser.add_argument_args = parser.parse_args()
    
    autonomous_delegator(args.task, args.model)
