import os

SOURCE_DIR = r"C:\Program Files\Chask_Swarm\Core_Context"
OUTPUT_FILE = r"C:\Program Files\Chask_Swarm\master_system_prompt.md"

def build_context():
    if not os.path.exists(SOURCE_DIR):
        print(f"Error: No se encontró el directorio de origen {SOURCE_DIR}")
        return

    # Orden lógico de inyección
    files_to_merge = [
        "soul.md",
        "admin.md",
        "directives.md",
        "protocols.md",
        "security.md",
        "comunication_rules.md",
        "skills.md",
        "artifacts.md"
    ]

    master_content = []
    master_content.append("<!-- SYSTEM PROMPT MAESTRO CHASK SWARM -->\n")
    master_content.append("<!-- Este archivo es autogenerado por build_master_context.py -->\n")

    for filename in files_to_merge:
        filepath = os.path.join(SOURCE_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().strip()
                if content:
                    master_content.append(f"\n\n==================== [{filename.upper()}] ====================")
                    master_content.append(content)
        else:
            print(f"Advertencia: Archivo {filename} no encontrado en {SOURCE_DIR}")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        out.write("\n".join(master_content))
    
    print(f"Éxito: Archivo maestro generado en {OUTPUT_FILE}")

if __name__ == "__main__":
    build_context()
