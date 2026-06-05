"""
sandbox.py — Sandbox Multi-Capa de Chask Swarm (v2.0)
=====================================================
4 capas de aislamiento para ejecucion segura de codigo:
  Capa 1: Windows Sandbox (Hyper-V nativo, max aislamiento)
  Capa 2: Docker con Hyper-V isolation
  Capa 3: Docker standard (fallback)
  Capa 4: Subprocess con restricciones (ultimo recurso)

Controles transversales:
  - Pre-scan de seguridad (AST + regex)
  - Network egress control
  - Resource limits (CPU, RAM, timeout)
  - Audit logging inmutable
  - HITL approval para operaciones destructivas
"""

import sys
import os
import subprocess
import json
import ast
import re
import hashlib
import time
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────
ROOT = Path(r"C:\Program Files\Chask_Swarn")
TOOLS = ROOT / "Advanced_Tools"
AUDIT_LOG = ROOT / "sandbox_audit.log"
SANDBOX_WORKDIR = ROOT / "scratch" / "sandbox_work"

# ─── Dangerous patterns (pre-scan) ───────────────────────
DANGEROUS_PATTERNS = [
    (r'\brm\s+-rf\b', 'rm -rf detectado'),
    (r'\bformat\s+[A-Z]:', 'format de disco detectado'),
    (r'\bdel\s+/[sfq]', 'del masivo detectado'),
    (r'\bshutil\.rmtree\b', 'rmtree detectado'),
    (r'\bos\.remove\b.*\bfor\b', 'borrado masivo en bucle'),
    (r'\bos\.system\s*\(', 'os.system (usar subprocess)'),
    (r'\bexec\s*\(', 'exec() detectado'),
    (r'\b__import__\b', '__import__ dinamico'),
    (r'\bsubprocess\.call\b.*\bshell\s*=\s*True', 'shell=True peligroso'),
    (r'\bctypes\b', 'acceso ctypes a bajo nivel'),
    (r'\bwinreg\b', 'acceso al registro de Windows'),
    (r'\bsocket\b', 'acceso a sockets de red'),
    (r'\brequests\.(get|post|put|delete)', 'peticion HTTP saliente'),
    (r'\burllib', 'acceso HTTP via urllib'),
]

DESTRUCTIVE_AST_CALLS = {
    'os.remove', 'os.unlink', 'os.rmdir', 'os.removedirs',
    'shutil.rmtree', 'shutil.move', 'subprocess.Popen',
    'subprocess.call', 'subprocess.run'
}


def audit_log(action: str, details: str, risk: str = "INFO"):
    """Append-only audit log con hash chain."""
    ts = datetime.now().isoformat()
    # Read last hash for chain
    last_hash = "0000"
    if AUDIT_LOG.exists():
        lines = AUDIT_LOG.read_text(encoding="utf-8").strip().split("\n")
        if lines:
            last_hash = lines[-1].split("|")[-1] if "|" in lines[-1] else "0000"
    
    entry = f"{ts}|{risk}|{action}|{details}"
    chain_hash = hashlib.sha256(f"{last_hash}{entry}".encode()).hexdigest()[:16]
    full_entry = f"{entry}|{chain_hash}"
    
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(full_entry + "\n")
    
    return full_entry


def pre_scan_security(script_path: str) -> dict:
    """
    Analisis de seguridad pre-ejecucion.
    Returns: {safe: bool, risks: list, severity: str}
    """
    with open(script_path, "r", encoding="utf-8") as f:
        code = f.read()
    
    risks = []
    
    # 1. Regex scan
    for pattern, desc in DANGEROUS_PATTERNS:
        matches = re.findall(pattern, code, re.IGNORECASE)
        if matches:
            risks.append({"type": "regex", "desc": desc, "count": len(matches)})
    
    # 2. AST scan
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        func_name = f"{node.func.value.id}.{node.func.attr}"
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id
                
                if func_name in DESTRUCTIVE_AST_CALLS:
                    risks.append({
                        "type": "ast",
                        "desc": f"Llamada destructiva: {func_name}",
                        "line": node.lineno
                    })
    except SyntaxError:
        risks.append({"type": "parse", "desc": "Error de sintaxis — no se pudo analizar"})
    
    # Classify severity
    if not risks:
        severity = "SAFE"
    elif any(r["type"] == "ast" for r in risks):
        severity = "HIGH"
    elif len(risks) > 3:
        severity = "HIGH"
    else:
        severity = "MEDIUM"
    
    return {"safe": severity == "SAFE", "risks": risks, "severity": severity}


def _check_windows_sandbox() -> bool:
    """Check if Windows Sandbox is available."""
    try:
        result = subprocess.run(
            ["where", "WindowsSandbox.exe"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def _check_docker() -> bool:
    """Check if Docker is available and running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def _check_docker_hyperv() -> bool:
    """Check if Docker supports Hyper-V isolation."""
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.Isolation}}"],
            capture_output=True, text=True, timeout=10
        )
        return "hyperv" in result.stdout.lower()
    except Exception:
        return False


def _generate_wsb(script_path: str, network: bool = False, timeout: int = 60) -> str:
    """Generate a Windows Sandbox .wsb configuration file."""
    SANDBOX_WORKDIR.mkdir(parents=True, exist_ok=True)
    
    # Copy script to workdir
    script_name = os.path.basename(script_path)
    dest = SANDBOX_WORKDIR / script_name
    shutil.copy2(script_path, dest)
    
    network_str = "Enable" if network else "Disable"
    
    wsb_content = f"""<Configuration>
  <Networking>{network_str}</Networking>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>{SANDBOX_WORKDIR}</HostFolder>
      <SandboxFolder>C:\\sandbox</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>cmd /c "cd C:\\sandbox &amp;&amp; python {script_name} > output.txt 2>&amp;1 &amp;&amp; timeout /t 3 &amp;&amp; shutdown /s /t 0"</Command>
  </LogonCommand>
  <MemoryInMB>1024</MemoryInMB>
</Configuration>"""
    
    wsb_path = SANDBOX_WORKDIR / "sandbox_config.wsb"
    wsb_path.write_text(wsb_content, encoding="utf-8")
    return str(wsb_path)


def run_windows_sandbox(script_path: str, network: bool = False, timeout: int = 120) -> dict:
    """
    Capa 1: Ejecucion en Windows Sandbox (Hyper-V nativo).
    Maximo aislamiento — VM efimera que se destruye al cerrar.
    """
    audit_log("SANDBOX_WIN", f"Iniciando Windows Sandbox: {script_path}", "INFO")
    
    wsb_path = _generate_wsb(script_path, network, timeout)
    
    try:
        proc = subprocess.Popen(
            ["WindowsSandbox.exe", wsb_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        proc.wait(timeout=timeout)
        
        # Read output if available
        output_file = SANDBOX_WORKDIR / "output.txt"
        output = ""
        if output_file.exists():
            output = output_file.read_text(encoding="utf-8", errors="replace")
        
        audit_log("SANDBOX_WIN", f"Completado: {len(output)} chars output", "INFO")
        return {"success": True, "output": output, "layer": "windows_sandbox"}
    
    except subprocess.TimeoutExpired:
        proc.kill()
        audit_log("SANDBOX_WIN", f"TIMEOUT ({timeout}s)", "WARN")
        return {"success": False, "error": f"Timeout ({timeout}s)", "layer": "windows_sandbox"}
    except Exception as e:
        audit_log("SANDBOX_WIN", f"Error: {e}", "ERROR")
        return {"success": False, "error": str(e), "layer": "windows_sandbox"}


def run_docker_hyperv(script_path: str, network: bool = False, 
                       timeout: int = 60, mem_limit: str = "512m",
                       cpu_limit: float = 1.0) -> dict:
    """
    Capa 2: Docker con aislamiento Hyper-V.
    Cada container tiene su propio kernel (guest OS).
    """
    audit_log("SANDBOX_DOCKER_HV", f"Iniciando Docker Hyper-V: {script_path}", "INFO")
    
    script_name = os.path.basename(script_path)
    script_dir = os.path.dirname(os.path.abspath(script_path))
    
    net_flag = "none" if not network else "bridge"
    
    cmd = [
        "docker", "run", "--rm",
        "--isolation=hyperv",
        "--network", net_flag,
        "--memory", mem_limit,
        f"--cpus={cpu_limit}",
        "--read-only",
        "--tmpfs", "/tmp:size=64m",
        "-v", f"{script_dir}:/usr/src/app:ro",
        "-w", "/usr/src/app",
        "--user", "nobody",
        "python:3.11-slim",
        "python", script_name
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        audit_log("SANDBOX_DOCKER_HV", f"Exit code: {result.returncode}", "INFO")
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "layer": "docker_hyperv"
        }
    except subprocess.TimeoutExpired:
        audit_log("SANDBOX_DOCKER_HV", f"TIMEOUT ({timeout}s)", "WARN")
        return {"success": False, "error": f"Timeout ({timeout}s)", "layer": "docker_hyperv"}
    except Exception as e:
        audit_log("SANDBOX_DOCKER_HV", f"Error: {e}", "ERROR")
        return {"success": False, "error": str(e), "layer": "docker_hyperv"}


def run_docker_standard(script_path: str, network: bool = False,
                        timeout: int = 60, mem_limit: str = "512m",
                        cpu_limit: float = 1.0) -> dict:
    """
    Capa 3: Docker standard (sin Hyper-V).
    Kernel compartido pero con restricciones estrictas.
    """
    audit_log("SANDBOX_DOCKER", f"Iniciando Docker standard: {script_path}", "INFO")
    
    script_name = os.path.basename(script_path)
    script_dir = os.path.dirname(os.path.abspath(script_path))
    
    net_flag = "none" if not network else "bridge"
    
    cmd = [
        "docker", "run", "--rm",
        "--network", net_flag,
        "--memory", mem_limit,
        f"--cpus={cpu_limit}",
        "--read-only",
        "--tmpfs", "/tmp:size=64m",
        "--security-opt", "no-new-privileges",
        "--cap-drop", "ALL",
        "-v", f"{script_dir}:/usr/src/app:ro",
        "-w", "/usr/src/app",
        "--user", "nobody",
        "python:3.11-slim",
        "python", script_name
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        audit_log("SANDBOX_DOCKER", f"Exit code: {result.returncode}", "INFO")
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "layer": "docker_standard"
        }
    except subprocess.TimeoutExpired:
        audit_log("SANDBOX_DOCKER", f"TIMEOUT ({timeout}s)", "WARN")
        return {"success": False, "error": f"Timeout ({timeout}s)", "layer": "docker_standard"}
    except Exception as e:
        audit_log("SANDBOX_DOCKER", f"Error: {e}", "ERROR")
        return {"success": False, "error": str(e), "layer": "docker_standard"}


def run_restricted_subprocess(script_path: str, timeout: int = 30) -> dict:
    """
    Capa 4: Subprocess con restricciones (ultimo recurso).
    Sin Docker ni Windows Sandbox disponible.
    """
    audit_log("SANDBOX_SUBPROCESS", f"Fallback a subprocess: {script_path}", "WARN")
    
    env = os.environ.copy()
    # Remove dangerous env vars
    for key in ["COMPUTERNAME", "USERNAME", "USERPROFILE", "HOMEPATH", "APPDATA"]:
        env.pop(key, None)
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True,
            timeout=timeout,
            env=env,
            cwd=tempfile.mkdtemp()
        )
        audit_log("SANDBOX_SUBPROCESS", f"Exit code: {result.returncode}", "INFO")
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "layer": "subprocess_restricted"
        }
    except subprocess.TimeoutExpired:
        audit_log("SANDBOX_SUBPROCESS", f"TIMEOUT ({timeout}s)", "WARN")
        return {"success": False, "error": f"Timeout ({timeout}s)", "layer": "subprocess_restricted"}
    except Exception as e:
        audit_log("SANDBOX_SUBPROCESS", f"Error: {e}", "ERROR")
        return {"success": False, "error": str(e), "layer": "subprocess_restricted"}


def request_hitl_approval(script_path: str, risks: list) -> bool:
    """Solicitar aprobacion humana por Telegram para operaciones destructivas."""
    try:
        risk_desc = "\n".join([f"  - {r['desc']}" for r in risks[:5]])
        msg = f"SANDBOX ALERTA: {os.path.basename(script_path)} tiene riesgos:\n{risk_desc}\nApruebas ejecucion? (si/no)"
        
        hitl_path = TOOLS / "hitl_telegram.py"
        if hitl_path.exists():
            result = subprocess.run(
                [sys.executable, str(hitl_path), msg],
                capture_output=True, text=True, timeout=120
            )
            response = result.stdout.strip().lower()
            approved = response in ("si", "sí", "yes", "s", "y", "ok")
            audit_log("HITL", f"Aprobacion: {approved} ({response})", "INFO")
            return approved
    except Exception as e:
        audit_log("HITL", f"Error HITL: {e}", "ERROR")
    
    return False


def run_in_sandbox(script_path: str, network: bool = False, 
                    timeout: int = 60, force_layer: str = None,
                    skip_scan: bool = False) -> dict:
    """
    Punto de entrada principal. Ejecuta un script en el sandbox mas seguro disponible.
    
    Args:
        script_path: Ruta al script Python a ejecutar
        network: Permitir acceso a red (default: False)
        timeout: Timeout en segundos
        force_layer: Forzar capa especifica (win_sandbox/docker_hyperv/docker/subprocess)
        skip_scan: Saltar pre-scan de seguridad
    
    Returns:
        dict con {success, output, errors, layer, scan_result}
    """
    if not os.path.exists(script_path):
        return {"success": False, "error": f"No existe: {script_path}"}
    
    audit_log("SANDBOX_START", f"Script: {script_path}", "INFO")
    
    # ─── Pre-scan de seguridad ───
    scan_result = {"safe": True, "risks": [], "severity": "SAFE"}
    if not skip_scan:
        scan_result = pre_scan_security(script_path)
        audit_log("PRE_SCAN", f"Severity: {scan_result['severity']}, Risks: {len(scan_result['risks'])}", 
                  "WARN" if not scan_result["safe"] else "INFO")
        
        # Si es HIGH risk, pedir aprobacion HITL
        if scan_result["severity"] == "HIGH":
            print(f"[Sandbox] ALERTA: {len(scan_result['risks'])} riesgos detectados (severity: HIGH)")
            for r in scan_result["risks"]:
                print(f"  - {r['desc']}")
            
            if not request_hitl_approval(script_path, scan_result["risks"]):
                audit_log("BLOCKED", f"Ejecucion bloqueada por HITL o timeout", "WARN")
                return {
                    "success": False, 
                    "error": "Ejecucion bloqueada: riesgos detectados, aprobacion denegada",
                    "scan_result": scan_result
                }
    
    # ─── Seleccion de capa ───
    if force_layer:
        layers = [force_layer]
    else:
        layers = []
        if _check_windows_sandbox():
            layers.append("win_sandbox")
        if _check_docker_hyperv():
            layers.append("docker_hyperv")
        if _check_docker():
            layers.append("docker")
        layers.append("subprocess")  # Siempre disponible como fallback
    
    # ─── Ejecutar en la mejor capa disponible ───
    for layer in layers:
        print(f"[Sandbox] Usando capa: {layer}")
        
        if layer == "win_sandbox":
            result = run_windows_sandbox(script_path, network, timeout)
        elif layer == "docker_hyperv":
            result = run_docker_hyperv(script_path, network, timeout)
        elif layer == "docker":
            result = run_docker_standard(script_path, network, timeout)
        elif layer == "subprocess":
            result = run_restricted_subprocess(script_path, timeout)
        else:
            continue
        
        result["scan_result"] = scan_result
        
        if result.get("success") or layer == layers[-1]:
            return result
        
        print(f"[Sandbox] Capa {layer} fallo, intentando siguiente...")
    
    return {"success": False, "error": "Todas las capas fallaron", "scan_result": scan_result}


def get_capabilities() -> dict:
    """Retorna las capas disponibles en este sistema."""
    return {
        "windows_sandbox": _check_windows_sandbox(),
        "docker_hyperv": _check_docker_hyperv(),
        "docker_standard": _check_docker(),
        "subprocess": True,
        "pre_scan": True,
        "hitl_approval": (TOOLS / "hitl_telegram.py").exists(),
        "audit_log": True
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status":
            caps = get_capabilities()
            print("=== Sandbox Multi-Capa - Estado ===")
            for k, v in caps.items():
                status = "[OK] Disponible" if v else "[--] No disponible"
                print(f"  {k}: {status}")
        else:
            result = run_in_sandbox(sys.argv[1])
            print(f"\n[Resultado] Layer: {result.get('layer', 'N/A')}")
            print(f"[Resultado] Success: {result.get('success')}")
            if result.get("output"):
                print(f"\n--- OUTPUT ---\n{result['output']}")
            if result.get("errors"):
                print(f"\n--- ERRORS ---\n{result['errors']}")
            if result.get("error"):
                print(f"\n--- ERROR ---\n{result['error']}")
    else:
        print("Uso: python sandbox.py <script.py>")
        print("      python sandbox.py --status")
