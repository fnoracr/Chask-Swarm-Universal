import ftplib
import os

def upload_to_ftp():
    ftp_host = "46.202.172.31"
    ftp_user = "u336848474.chask.fun"
    ftp_pass = "AQUI_VA_TU_FTP_PASS"
    
    files_to_upload = [
        "C:\\Users\\fnora\\Desktop\\charm.php",
        "C:\\Users\\fnora\\Desktop\\download_tracker.php",
        "C:\\Users\\fnora\\Desktop\\Chask_Swarm_Windows_Universal.zip",
        "C:\\Users\\fnora\\Desktop\\Chask_Swarm_Mac_Universal.zip",
        "C:\\Users\\fnora\\Desktop\\Chask_Swarm_Linux_Universal.zip"
    ]
    
    try:
        print(f"Connecting to {ftp_host}...")
        ftp = ftplib.FTP(ftp_host)
        ftp.login(ftp_user, ftp_pass)
        print("Connected.")
        
        dirs = []
        ftp.retrlines('LIST', dirs.append)
        if any("public_html" in d for d in dirs):
            ftp.cwd("public_html")
            print("Changed to public_html")
        
        for file_path in files_to_upload:
            if not os.path.exists(file_path):
                print(f"Skipping {file_path} (File not found)")
                continue
                
            filename = os.path.basename(file_path)
            print(f"Uploading {filename}...")
            
            with open(file_path, "rb") as file:
                ftp.storbinary(f"STOR {filename}", file)
            print(f"Uploaded {filename} successfully.")
            
        ftp.quit()
        print("FTP transfer complete.")
        
    except Exception as e:
        print(f"FTP Error: {e}")

if __name__ == "__main__":
    upload_to_ftp()
