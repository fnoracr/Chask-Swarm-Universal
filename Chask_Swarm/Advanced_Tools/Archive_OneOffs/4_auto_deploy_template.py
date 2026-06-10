import ftplib
import os
import sys

# ==============================================================================
# AI CI/CD AUTO-DEPLOYMENT FRAMEWORK
# Plantilla para que la IA suba automáticamente el código a tu servidor FTP
# ¡NO GUARDES TUS CONTRASEÑAS REALES EN ESTE ARCHIVO!
# Usa variables de entorno o un archivo .env externo.
# ==============================================================================

FTP_HOST = os.environ.get("FTP_HOST", "tu-servidor.com")
FTP_USER = os.environ.get("FTP_USER", "tu-usuario")
FTP_PASS = os.environ.get("FTP_PASS", "tu-contraseña")

# Directorio local que la IA acaba de crear/modificar
LOCAL_DIR = r"C:\Ruta\Al\Directorio\Web"

# Directorio remoto en el servidor FTP
REMOTE_DIR = "public_html"

def upload_file(ftp, local_path, remote_path):
    """Sube un archivo individual al FTP"""
    try:
        with open(local_path, 'rb') as f:
            ftp.storbinary(f'STOR {remote_path}', f)
        print(f"[OK] Subido: {remote_path}")
    except Exception as e:
        print(f"[ERROR] Fallo al subir {remote_path}: {e}")

def deploy():
    print("Iniciando conexión FTP...")
    try:
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        print("¡Conexión establecida!")
        
        ftp.cwd(REMOTE_DIR)
        
        # Iterar sobre todos los archivos del directorio local
        for root, dirs, files in os.walk(LOCAL_DIR):
            for file in files:
                local_path = os.path.join(root, file)
                
                # Calcular la ruta relativa para el FTP
                rel_path = os.path.relpath(local_path, LOCAL_DIR)
                remote_path = rel_path.replace("\\", "/") # Convertir rutas Windows a Linux
                
                # Crear directorios remotos si no existen
                remote_dir_path = os.path.dirname(remote_path)
                if remote_dir_path:
                    try:
                        ftp.mkd(remote_dir_path)
                    except ftplib.error_perm:
                        pass # El directorio ya existe
                        
                upload_file(ftp, local_path, remote_path)
                
        ftp.quit()
        print("¡Despliegue completado con éxito!")
        
    except Exception as e:
        print(f"Error crítico de despliegue: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if FTP_PASS == "tu-contraseña":
        print("ADVERTENCIA: Estás usando la plantilla sin configurar credenciales.")
        print("Por favor, configura las variables de entorno FTP_HOST, FTP_USER y FTP_PASS.")
    else:
        deploy()
