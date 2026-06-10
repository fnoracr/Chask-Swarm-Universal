import os

d1 = r"C:\Program Files\Chask_Swarm\directives.md"
d2 = r"C:\Users\fnora\Desktop\Nora Datos\directives.md"
text = "\n\n## 20. Estrategia Global de Redes Sociales\nToda publicación en redes sociales (Patreon u otras) debe ser original, emotiva y persuasiva con el objetivo primario de VENDER el ecosistema Chask Swarm. Además, en redes distintas a Patreon, es OBLIGATORIO incluir enlaces a nuestro Patreon y a charm.php.\n"

with open(d1, "a", encoding="utf-8") as f:
    f.write(text)
try:
    with open(d2, "a", encoding="utf-8") as f:
        f.write(text)
except:
    pass
print("Directives updated.")

os.system(r'schtasks /Create /TN "PatreonBot_8" /TR "python C:\Users\fnora\Desktop\patreon_bot.py" /SC DAILY /ST 08:00 /F')
os.system(r'schtasks /Create /TN "PatreonBot_14" /TR "python C:\Users\fnora\Desktop\patreon_bot.py" /SC DAILY /ST 14:00 /F')
os.system(r'schtasks /Create /TN "PatreonBot_20" /TR "python C:\Users\fnora\Desktop\patreon_bot.py" /SC DAILY /ST 20:00 /F')
print("Tasks scheduled.")
