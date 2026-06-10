import os
import shutil

base_dir = r"C:\Users\fnora\Desktop"
univ_dir = os.path.join(base_dir, "Distribucion_Universal")
langs_dir = os.path.join(univ_dir, "Langs")

os.makedirs(langs_dir, exist_ok=True)

langs = ["ES", "EN", "PT", "ZH", "RU", "FR"]
files_to_copy = [
    "Install.bat",
    "Inicio.bat",
    "Start.bat",
    "Parar_Enjambre.bat",
    "Stop_Swarm.bat",
    "recuperacion.bat",
    "recovery.bat",
    "Iniciar_Chask_Hive.bat",
    "Start_Chask_Hive.bat",
    "Documentacion/README.md",
    "Documentacion/Manual_Oficial_Charm.html",
    "Official_Charm_Manual.html"
]

for lang in langs:
    lang_src_dir = os.path.join(base_dir, f"Distribucion_{lang}")
    lang_dest_dir = os.path.join(langs_dir, lang)
    os.makedirs(lang_dest_dir, exist_ok=True)
    
    for f in files_to_copy:
        src = os.path.join(lang_src_dir, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(lang_dest_dir, f))

# Rename Install.bat inside Langs to Install_Language.bat so we don't conflict with universal Install.bat if needed,
# Actually, the universal Install.bat will just OVERWRITE the root files with the selected lang's files.
print("Languages copied to Universal Distribution.")
