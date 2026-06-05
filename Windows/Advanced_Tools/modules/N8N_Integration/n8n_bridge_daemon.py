from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import os
import sys

os.chdir(r"C:\Program Files\Chask_Swarn")

PORT_NUMBER = 51339
BASE_DIR = r"C:\Program Files\Chask_Swarn"
LOG_FILE = os.path.join(BASE_DIR, "Advanced_Tools", "n8n_bridge.log")

def log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except:
        pass

class CommandHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/kill':
            self.send_response(200)
            self.send_header('Content-type','text/plain')
            self.end_headers()
            self.wfile.write(b"Executing Kill Script")
            log("Received /kill command from n8n. Executing kill_all.bat...")
            subprocess.Popen([r"C:\Program Files\Chask_Swarn\[Nombre_IA]\Advanced_Tools\n8n\kill_all.bat"], creationflags=subprocess.CREATE_NO_WINDOW)
            return

        if self.path == '/start':
            self.send_response(200)
            self.send_header('Content-type','text/plain')
            self.end_headers()
            self.wfile.write(b"Executing Start Script")
            log("Received /start command from n8n. Executing start_all.bat...")
            subprocess.Popen([r"C:\Program Files\Chask_Swarn\[Nombre_IA]\Advanced_Tools\n8n\start_all.bat"], creationflags=subprocess.CREATE_NO_WINDOW)
            return

        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Comprobar si el watchdog está vivo
            try:
                out = subprocess.check_output(
                    'wmic process where "name=\'python.exe\' or name=\'pythonw.exe\'" get commandline,processid',
                    shell=True, text=True
                )
                is_running = False
                for line in out.split('\n'):
                    if 'Advanced_Tools/Daemons/process_watchdog.py' in line and 'wmic' not in line.lower() and 'powershell' not in line.lower():
                        is_running = True
                        break
            except:
                is_running = False
                
            if is_running:
                self.wfile.write(b'{"running": true}')
            else:
                self.wfile.write(b'{"running": false}')
            return
            
        self.send_response(404)
        self.end_headers()

def main():
    try:
        server = HTTPServer(('0.0.0.0', PORT_NUMBER), CommandHandler)
        log(f"n8n Bridge Daemon started on port {PORT_NUMBER} (0.0.0.0)")
        server.serve_forever()
    except KeyboardInterrupt:
        log("^C received, shutting down the server")
        server.socket.close()

if __name__ == '__main__':
    main()
