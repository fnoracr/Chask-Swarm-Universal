import ftplib
import os

FTP_HOST = "46.202.172.31"
FTP_USER = "u336848474.chask.fun"
FTP_PASS = "AQUI_VA_TU_FTP_PASS"

try:
    ftp = ftplib.FTP(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.cwd('public_html')
    
    print("Files in public_html:")
    files = ftp.nlst()
    for f in files:
        if 'charm' in f.lower() or 'index' in f.lower():
            print(" -", f)
            
    if 'charm.php' in files:
        with open('C:\\Users\\fnora\\Desktop\\charm_server.php', 'wb') as fp:
            ftp.retrbinary('RETR charm.php', fp.write)
        print("\ncharm.php downloaded successfully.")
    
    ftp.quit()
except Exception as e:
    print("Error:", e)
