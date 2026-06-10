import os

print("Programando el inicio automatico...")
res = os.system(r'schtasks /Create /TN "ChaskEmailMonitor" /TR "pythonw \"C:\Program Files\Chask_Swarm\Advanced_Tools\email_monitor.py\" daemon" /SC ONLOGON /F')
print(f"Resultado schtasks: {res}")

print("Iniciando el demonio ahora mismo...")
os.system(r'start /B pythonw "C:\Program Files\Chask_Swarm\Advanced_Tools\email_monitor.py" daemon')
print("Hecho.")
