import os

tasks = [
    ("TwitterBot_8", "08:00"),
    ("TwitterBot_14", "14:00"),
    ("TwitterBot_20", "20:00"),
]

for name, time_str in tasks:
    cmd = f'schtasks /Create /TN "{name}" /TR "python C:\\Users\\fnora\\Desktop\\twitter_bot.py both" /SC DAILY /ST {time_str} /F'
    print(f"Creando tarea {name} a las {time_str}...")
    res = os.system(cmd)
    if res == 0:
        print(f"Exito: {name}")
    else:
        print(f"Fallo: {name}")
