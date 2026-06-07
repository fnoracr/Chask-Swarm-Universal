import os
import sys
import json
from datetime import datetime

# Añadir el directorio actual al path para importar llm_router
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
import llm_router

class ProtocoloOrestes:
    """
    Protocolo Orestes: Elektra como Generadora de Código de la Colmena.
    Este motor orquesta la creación de herramientas autónomas para el ecosistema Chask.
    Usa el llm_router para derivar la creación y auditoría a diferentes IAs.
    """
    def __init__(self):
        self.base_path = r"C:\Program Files\Chask_Swarm"
        self.output_path = os.path.join(self.base_path, "Advanced_Tools")
        self.log_file = os.path.join(self.base_path, "orestes_activity.log")

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [ORESTES] {message}\n")
        print(f"[ORESTES] {message}")

    def _call_specific_ai(self, prompt, system_prompt, preferred_models):
        cfg = llm_router.load_config()
        usage = llm_router.load_usage()
        for model in preferred_models:
            provider = next((p for p in cfg["providers"] if p["name"] == model and p.get("active")), None)
            if provider:
                used = usage["counts"].get(model, 0)
                limit = provider.get("daily_limit", 500)
                if used < limit:
                    self.log(f"Delegando tarea a: {model} ({provider.get('label', '')})")
                    resp = llm_router.call_provider(provider, prompt, system_prompt)
                    if resp:
                        usage["counts"][model] = used + 1
                        llm_router.save_usage(usage)
                        return resp, model
        
        # Fallback al router general si fallan los preferidos
        res = llm_router.route(prompt, system_prompt, force_free=True)
        return res["response"], res["engine"]

    def forge_script(self, task_description, filename):
        """
        Elektra genera el plano lógico y solicita al pool de IA la forja del código.
        """
        self.log(f"Iniciando forja de script: {filename}")
        self.log(f"Requerimiento: {task_description}")
        
        system_prompt = (
            "Eres un Desarrollador Senior experto en Python (Protocolo Orestes). "
            "Tu único objetivo es devolver EXCLUSIVAMENTE código Python válido, sin explicaciones, sin markdown (excepto si es estrictamente necesario), "
            "listo para guardarse en un archivo .py y ejecutarse. El código debe estar bien comentado y manejar errores."
        )
        prompt = f"Genera un script en Python llamado {filename} que cumpla exactamente esto: {task_description}"
        
        # Preferimos DeepSeek o Qwen (OpenRouter) o SiliconFlow para código
        code_result, engine_used = self._call_specific_ai(prompt, system_prompt, ["deepseek", "siliconflow", "openrouter"])
        
        if not code_result:
            self.log("Alerta de Créditos/Red: Ninguna IA externa disponible. El Orquestador (Enjambre/Charm) debe asumir el rol de forjador simulando al agente.")
            return False

        # Limpiar markdown si la IA lo incluyó
        code_template = code_result.strip()
        if code_template.startswith("```python"):
            code_template = code_template[9:]
        if code_template.endswith("```"):
            code_template = code_template[:-3]
        code_template = code_template.strip()
        
        target_file = os.path.join(self.output_path, filename)
        
        try:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(code_template)
            self.log(f"Script forjado con éxito por {engine_used} en: {target_file}")
            return True
        except Exception as e:
            self.log(f"Error guardando la forja: {e}")
            return False

    def audit_code(self, filename):
        """
        Elektra revisa el código en busca de errores lógicos o riesgos de seguridad.
        """
        self.log(f"Auditoría de seguridad iniciada para {filename}...")
        target_file = os.path.join(self.output_path, filename)
        
        if not os.path.exists(target_file):
            self.log(f"Error: No se encontró el archivo {filename} para auditar.")
            return False
            
        with open(target_file, "r", encoding="utf-8") as f:
            code_content = f.read()
            
        system_prompt = (
            "Eres un Auditor de Seguridad Informática y Arquitecto QA (Protocolo Orestes - Delta). "
            "Revisa el código proporcionado buscando vulnerabilidades críticas, código malicioso que pueda borrar archivos, "
            "o errores sintácticos graves. Responde EXACTAMENTE con 'LIMPIO' si el código es seguro y funcional. "
            "Si tiene errores fatales, explica por qué."
        )
        prompt = f"Audita este código:\n\n{code_content}"
        
        # Preferimos Groq, ZhipuAI o Cohere para auditoría rápida (distintos a los de generación)
        audit_result, engine_used = self._call_specific_ai(prompt, system_prompt, ["groq", "zhipuai", "cohere"])
        
        if not audit_result:
            self.log("Alerta de Créditos/Red: Fallo en la conexión de auditoría. El Orquestador (Enjambre/Charm) debe asumir el rol de auditor revisando críticamente el código.")
            return False
            
        if "LIMPIO" in audit_result.upper()[:50]:
            self.log(f"Resultado de auditoría ({engine_used}): LIMPIO. Listo para Colmena.")
            return True
        else:
            self.log(f"Auditoría fallida ({engine_used}): {audit_result}")
            return False

if __name__ == "__main__":
    orestes = ProtocoloOrestes()
    orestes.log("Sistema Orestes Inicializado en Modo Standby.")

