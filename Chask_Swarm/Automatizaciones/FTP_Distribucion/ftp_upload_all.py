import ftplib
import os
import time

FTP_HOST = "46.202.172.31"
FTP_USER = "u336848474.chask.fun"
FTP_PASS = "AQUI_VA_TU_FTP_PASS"

print(f"Connecting to {FTP_HOST}...")
try:
    ftp = ftplib.FTP(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    print("Connected.")
    
    files_to_upload = [
        "C:\\Users\\fnora\\Desktop\\charm.php",
        "C:\\Users\\fnora\\Desktop\\download_tracker.php"
    ]
    
    for lang in ["ES", "EN", "PT", "ZH", "RU", "FR"]:
        files_to_upload.append(f"C:\\Users\\fnora\\Desktop\\Chask_Swarm_{lang}.zip")
        files_to_upload.append(f"C:\\Users\\fnora\\Desktop\\Chask_Swarm_Mac_{lang}.zip")
        files_to_upload.append(f"C:\\Users\\fnora\\Desktop\\Chask_Swarm_Linux_{lang}.zip")
    
    dirs = []
    ftp.retrlines('LIST', dirs.append)
    if any("public_html" in d for d in dirs):
        ftp.cwd("public_html")
        print("Changed to public_html")
        
    for filepath in files_to_upload:
        if os.path.exists(filepath):
            filename = os.path.basename(filepath)
            print(f"Uploading {filename}...")
            with open(filepath, "rb") as file:
                ftp.storbinary(f"STOR {filename}", file)
            print(f"Uploaded {filename} successfully.")
        else:
            print(f"File not found: {filepath}")
            
    ftp.quit()
    print("FTP transfer complete.")
except Exception as e:
    print(f"Error: {e}")
