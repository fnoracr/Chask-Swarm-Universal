import ftplib
import json
import os

with open(r'C:\Program Files\Chask_Swarm\Configuration\master_credentials.json', 'r') as f:
    creds = json.load(f)['credentials']

FTP_HOST = creds['ftp_host']
FTP_USER = creds['ftp_user']
FTP_PASS = creds['ftp_pass']
LOCAL_DIR = r"C:\Program Files\Chask_Swarm\Local_Web"

files_to_upload = ['charm.php', 'visit_tracker.php']

try:
    ftp = ftplib.FTP(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    
    for filename in files_to_upload:
        local_path = os.path.join(LOCAL_DIR, filename)
        with open(local_path, "rb") as f:
            print(f"Subiendo {filename}...")
            ftp.storbinary(f"STOR {filename}", f)
            
    print("Archivos subidos correctamente.")
    ftp.quit()
except Exception as e:
    print(f"Error al subir: {e}")
