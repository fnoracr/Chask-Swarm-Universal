import time
import os
paths = [r'C:\Program Files\Chask_Swarm\memory.md', r'C:\Users\fnora\Desktop\Nora Datos\memory.md']
for p in paths:
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f: lines = f.readlines()
        for i, l in enumerate(lines):
            if l.startswith('Paso actual:'): lines[i] = 'Paso actual: Gateway Unificado y SDK Charm completados.\n'
            elif l.startswith('Hora de última actualización:'): lines[i] = f'Hora de última actualización: {time.strftime("%Y-%m-%d %H:%M:%S")}\n'
        with open(p, 'w', encoding='utf-8') as f: f.writelines(lines)
