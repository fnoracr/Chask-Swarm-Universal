import os
import sys
import json

def setup():
    print("========================================")
    print(" Bienvenido al Instalador de Chask Swarm ")
    print("========================================")
    ai_name = input("¿Qué nombre quieres darle a tu IA? (ej. Jarvis, HAL, etc.): ").strip()
    user_name = input("¿Cuál es tu nombre? (Serás el Usuario Avanzado): ").strip()
    
    if not ai_name or not user_name:
        print("Error: Nombres no pueden estar vacios.")
        sys.exit(1)
        
    print(f"\nConfigurando el sistema para {user_name} con IA {ai_name}...")
    
    # Update all config files to replace [NOMBRE_IA]
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for root, dirs, files in os.walk(base_dir):
        for name in files:
            if not name.endswith(('.py', '.json', '.md', '.txt', '.php', '.html')):
                continue
            file_path = os.path.join(root, name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if "[NOMBRE_IA]" in content:
                    content = content.replace("[NOMBRE_IA]", ai_name)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
            except Exception:
                pass
                
    # Configure Users: Fernando as Admin, User as Advanced
    users_config_path = os.path.join(base_dir, "Configuration", "users.json")
    if not os.path.exists(os.path.dirname(users_config_path)):
        os.makedirs(os.path.dirname(users_config_path), exist_ok=True)
        
    users_data = {
        "fernando_admin": {
            "name": "Fernando Nora",
            "role": "administrator",
            "is_creator": True
        },
        "main_user": {
            "name": user_name,
            "role": "advanced_user"
        }
    }
    with open(users_config_path, "w", encoding="utf-8") as f:
        json.dump(users_data, f, indent=4)
        
    # Create Charm Workspace
    charm_dir = os.path.join(base_dir, "Charm")
    os.makedirs(charm_dir, exist_ok=True)
    with open(os.path.join(charm_dir, "chat_history.md"), "w", encoding="utf-8") as f:
        f.write("# Historial de Conversaciones\n")
        
    print(f"\n¡Instalación completada! Tu IA {ai_name} está lista.")

if __name__ == "__main__":
    setup()
