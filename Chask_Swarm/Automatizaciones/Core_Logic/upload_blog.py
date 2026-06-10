import ftplib

def upload():
    try:
        ftp = ftplib.FTP('46.202.172.31')
        ftp.login('u336848474.chask.fun', 'AQUI_VA_TU_FTP_PASS')
        ftp.cwd('/public_html')
        
        # Ensure charm directory exists
        try:
            ftp.mkd('charm')
        except Exception:
            pass # Probably exists
            
        ftp.cwd('charm')
        
        with open(r'C:\Program Files\Chask_Swarm\Charm\blog.html', 'rb') as f:
            ftp.storbinary('STOR Charm_Blog.php', f)
        ftp.quit()
        print("Upload exitoso")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    upload()
