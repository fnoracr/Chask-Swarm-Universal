import ftplib
import json
import io

def check():
    with open(r'C:\Program Files\Chask_Swarm\Configuracion\master_credentials.json', 'r') as f:
        creds = json.load(f)['credentials']
        
    try:
        ftp = ftplib.FTP(creds['ftp_host'])
        ftp.login(creds['ftp_user'], creds['ftp_pass'])
        
        lines = []
        try:
            ftp.retrlines("RETR visits.txt", lines.append)
            # Quitar líneas vacías
            lines = [l for l in lines if l.strip()]
            print(f"VISITAS UNICAS REGISTRADAS: {len(lines)}")
        except Exception as e:
            if "550" in str(e):
                print("VISITAS UNICAS REGISTRADAS: 0 (El archivo aún no se ha creado porque no hay visitas).")
            else:
                print(f"Error al leer visits.txt: {e}")
        ftp.quit()
    except Exception as e:
        print(f"Error FTP: {e}")

if __name__ == "__main__":
    check()
