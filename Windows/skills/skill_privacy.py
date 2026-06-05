import os
import sys
from Advanced_Tools.privacy_engine import PrivacyEngine

# Determinar país por defecto (se puede mejorar leyendo locale del sistema)
DEFAULT_COUNTRY = "ES"

def clean_text(text, country=DEFAULT_COUNTRY, mode="redact"):
    """
    Función principal para limpiar texto de forma segura.
    """
    engine = PrivacyEngine(country_code=country)
    return engine.anonymize(text, mode=mode)

def clean_file(file_path, country=DEFAULT_COUNTRY, mode="redact"):
    """
    Lee un archivo, lo limpia y devuelve el contenido anonimizado.
    """
    if not os.path.exists(file_path):
        return f"Error: El archivo {file_path} no existe."
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        clean_content = clean_text(content, country=country, mode=mode)
        
        # Guardar una versión limpia para que el usuario pueda revisarla
        base, ext = os.path.splitext(file_path)
        clean_path = f"{base}_CLEAN{ext}"
        
        with open(clean_path, "w", encoding="utf-8") as f:
            f.write(clean_content)
            
        return f"Archivo limpiado con éxito. Guardado en: {clean_path}\n\nResumen del contenido limpio:\n{clean_content[:500]}..."
    except Exception as e:
        return f"Error al procesar el archivo: {e}"

if __name__ == "__main__":
    # Esta skill puede ser llamada por [Nombre_IA]
    if len(sys.argv) > 1:
        task = sys.argv[1]
        # Lógica de dispatching de la skill
        print(f"[Skill Privacy] Procesando tarea...")
