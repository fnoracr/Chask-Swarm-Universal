"""
windows_service.py — Registro de daemons como Windows Services
===============================================================
Permite instalar/desinstalar los daemons de Chask Swarm como
servicios nativos de Windows (aparecen en services.msc).
Usa NSSM (Non-Sucking Service Manager) si esta disponible,
o pywin32 como fallback.
"""
import os
import sys
import subprocess
import json
from pathlib import Path

ROOT = Path(r"C:\Program Files\Chask_Swarn")
PYTHON = sys.executable
NSSM = ROOT / "nssm.exe"  # Optional NSSM binary

SERVICES = {
    "ChaskUnifiedDaemon": {
        "display": "Chask Swarm - Unified Communications Daemon",
        "description": "Daemon unificado de comunicaciones: Telegram, Discord, Slack, Teams",
        "script": str(ROOT / "unified_daemon.py"),
    },
    "ChaskProcessWatchdog": {
        "display": "Chask Swarm - Process Watchdog",
        "description": "Vigilante de procesos: reinicia daemons caidos automaticamente",
        "script": str(ROOT / "Advanced_Tools/Daemons/process_watchdog.py"),
    },
    "ChaskScheduler": {
        "display": "Chask Swarm - Task Scheduler",
        "description": "Programador de tareas con cron expressions",
        "script": str(ROOT / "Advanced_Tools" / "chask_scheduler.py"),
    },
}


def _nssm_available() -> bool:
    """Check if NSSM is available."""
    if NSSM.exists():
        return True
    try:
        result = subprocess.run(["nssm", "version"], capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def _nssm_cmd() -> str:
    return str(NSSM) if NSSM.exists() else "nssm"


def install_service(name: str) -> dict:
    """Install a daemon as a Windows Service."""
    if name not in SERVICES:
        return {"success": False, "error": f"Servicio '{name}' no definido"}
    
    svc = SERVICES[name]
    
    if _nssm_available():
        # Use NSSM (preferred)
        nssm = _nssm_cmd()
        try:
            subprocess.run([nssm, "install", name, PYTHON, svc["script"]], 
                          capture_output=True, timeout=10)
            subprocess.run([nssm, "set", name, "DisplayName", svc["display"]], 
                          capture_output=True, timeout=5)
            subprocess.run([nssm, "set", name, "Description", svc["description"]], 
                          capture_output=True, timeout=5)
            subprocess.run([nssm, "set", name, "Start", "SERVICE_AUTO_START"], 
                          capture_output=True, timeout=5)
            subprocess.run([nssm, "set", name, "AppDirectory", str(ROOT)], 
                          capture_output=True, timeout=5)
            return {"success": True, "method": "nssm", "service": name}
        except Exception as e:
            return {"success": False, "error": str(e), "method": "nssm"}
    
    else:
        # Fallback: use sc.exe (Windows built-in)
        try:
            cmd = f'sc create {name} binPath= "\"{PYTHON}\" \"{svc["script"]}\"" DisplayName= "{svc["display"]}" start= auto'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=10)
            if result.returncode == 0:
                # Set description
                subprocess.run(f'sc description {name} "{svc["description"]}"', 
                              capture_output=True, shell=True, timeout=5)
                return {"success": True, "method": "sc", "service": name}
            else:
                return {"success": False, "error": result.stderr, "method": "sc"}
        except Exception as e:
            return {"success": False, "error": str(e), "method": "sc"}


def uninstall_service(name: str) -> dict:
    """Remove a Windows Service."""
    try:
        # Stop first
        subprocess.run(f"sc stop {name}", capture_output=True, shell=True, timeout=10)
        
        if _nssm_available():
            subprocess.run([_nssm_cmd(), "remove", name, "confirm"], 
                          capture_output=True, timeout=10)
        else:
            subprocess.run(f"sc delete {name}", capture_output=True, shell=True, timeout=10)
        
        return {"success": True, "service": name}
    except Exception as e:
        return {"success": False, "error": str(e)}


def start_service(name: str) -> dict:
    """Start a Windows Service."""
    try:
        result = subprocess.run(f"sc start {name}", capture_output=True, text=True, shell=True, timeout=15)
        return {"success": result.returncode == 0, "output": result.stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}


def stop_service(name: str) -> dict:
    """Stop a Windows Service."""
    try:
        result = subprocess.run(f"sc stop {name}", capture_output=True, text=True, shell=True, timeout=15)
        return {"success": result.returncode == 0, "output": result.stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_service_status(name: str) -> dict:
    """Get status of a Windows Service."""
    try:
        result = subprocess.run(f"sc query {name}", capture_output=True, text=True, shell=True, timeout=5)
        running = "RUNNING" in result.stdout
        return {"exists": result.returncode == 0, "running": running, "output": result.stdout}
    except Exception as e:
        return {"exists": False, "running": False, "error": str(e)}


def list_services() -> list:
    """List all Chask Swarm services and their status."""
    results = []
    for name, svc in SERVICES.items():
        status = get_service_status(name)
        results.append({
            "name": name,
            "display": svc["display"],
            "installed": status.get("exists", False),
            "running": status.get("running", False)
        })
    return results


def install_all() -> list:
    """Install all defined services."""
    results = []
    for name in SERVICES:
        r = install_service(name)
        results.append({"name": name, **r})
        print(f"  {name}: {'OK' if r['success'] else 'FAIL'} ({r.get('method', '')})")
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python windows_service.py --status    (ver estado)")
        print("  python windows_service.py --install   (instalar todos)")
        print("  python windows_service.py --uninstall (desinstalar todos)")
        sys.exit(0)
    
    if sys.argv[1] == "--status":
        services = list_services()
        print("=== Chask Swarm Windows Services ===")
        for s in services:
            status = "RUNNING" if s["running"] else ("STOPPED" if s["installed"] else "NOT INSTALLED")
            print(f"  {s['name']}: {status}")
    
    elif sys.argv[1] == "--install":
        print("Instalando servicios...")
        install_all()
    
    elif sys.argv[1] == "--uninstall":
        print("Desinstalando servicios...")
        for name in SERVICES:
            r = uninstall_service(name)
            print(f"  {name}: {'OK' if r['success'] else 'FAIL'}")
