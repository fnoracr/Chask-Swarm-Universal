import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import time
import os
import sys

class SwarmWatchdogService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ChaskSwarmWatchdog"
    _svc_display_name_ = "Chask Swarm Watchdog OS-Level"
    _svc_description_ = "Mantiene los daemons principales de Nora en ejecución 24/7 de forma nativa en Windows."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        # Lógica principal del Watchdog OS-Level
        # Monitoreará scripts secundarios sin interferir con comunicaciones
        log_path = r"C:\Program Files\Chask_Swarm\Advanced_Tools\Daemons\watchdog_service.log"
        while self.is_running:
            try:
                with open(log_path, "a") as f:
                    f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Watchdog OS-Level activo.\n")
            except Exception:
                pass
            
            # Aquí iría el subprocess.Popen() de los scripts del enjambre
            # (Se omiten intencionalmente los de comunicación por directiva de contención)
            time.sleep(60)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SwarmWatchdogService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(SwarmWatchdogService)
