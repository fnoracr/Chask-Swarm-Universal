import os
import sys
import importlib
import inspect
import random
import traceback

class ChaosMonkey:
    """
    Fuzzer preventivo para probar la resiliencia del ecosistema Chask Swarm.
    Inyecta inputs inválidos, nulos o excesivos a las funciones públicas de los módulos.
    Mantiene un aislamiento estricto de los módulos de comunicación.
    """
    
    BLACKLIST = [
        "telegram_listener", "telegram_sender", "universal_sender",
        "queue_sentinel", "queue_monitor_bg", "queue_mark_done", "chaos_monkey"
    ]
    
    def __init__(self, target_dir):
        self.target_dir = target_dir
        self.fuzz_inputs = [
            None,
            "",
            "A" * 10000,  # Buffer overflow tentativo
            -1,
            999999999,
            {"nested": {"dict": True}},
            ["list", "of", "strings"],
            b"\x00\xff",
            object()
        ]

    def run(self):
        print(f"[ChaosMonkey] Iniciando cacería de bugs en {self.target_dir}")
        sys.path.insert(0, self.target_dir)
        
        for root, _, files in os.walk(self.target_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    module_name = file[:-3]
                    if module_name in self.BLACKLIST:
                        print(f"  [Skipping] {module_name} (En lista negra de comunicaciones/seguridad)")
                        continue
                        
                    self._fuzz_module(module_name)

    def _fuzz_module(self, module_name):
        try:
            module = importlib.import_module(module_name)
            functions = inspect.getmembers(module, inspect.isfunction)
            for func_name, func in functions:
                # Fuzzing superficial de argumentos posicionales
                sig = inspect.signature(func)
                num_params = len(sig.parameters)
                if num_params > 0:
                    args = [random.choice(self.fuzz_inputs) for _ in range(num_params)]
                    try:
                        func(*args)
                    except TypeError:
                        # Excepciones controladas por Python son pasables
                        pass
                    except Exception as e:
                        print(f"  [CRASH DETECTADO] {module_name}.{func_name}() no maneja bien inputs corruptos: {e}")
                        # En un entorno real, aquí notificaría a Elektra para que genere un parche TDD
        except Exception as e:
            print(f"  [Carga Fallida] No se pudo fuzzeear {module_name}: {e}")

if __name__ == "__main__":
    target = r"C:\Program Files\Chask_Swarm\Advanced_Tools"
    monkey = ChaosMonkey(target)
    monkey.run()
