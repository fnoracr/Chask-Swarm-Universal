"""
git_worktree_manager.py — Aislamiento por Git Worktrees
=========================================================
Permite trabajar en múltiples ramas simultáneamente sin conflictos.
Cada tarea compleja se ejecuta en su propio worktree aislado.

Flujo:
  1. Crear worktree para una tarea → directorio aislado
  2. Trabajar en el worktree sin afectar main
  3. Mergear cuando está listo
  4. Limpiar worktrees obsoletos

Uso:
  python git_worktree_manager.py create feature-x
  python git_worktree_manager.py list
  python git_worktree_manager.py merge feature-x
  python git_worktree_manager.py clean
"""
import os
import sys
import io
import json
import subprocess
from datetime import datetime

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKTREES_DIR = os.path.join(BASE_DIR, "worktrees")
WORKTREE_LOG = os.path.join(BASE_DIR, "worktree_log.json")


def _git(args: list[str], cwd: str = None) -> tuple[int, str]:
    """Ejecuta un comando git."""
    cmd = ["git"] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=cwd or BASE_DIR, timeout=30,
            encoding="utf-8", errors="replace"
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n{result.stderr.strip()}"
        return result.returncode, output
    except Exception as e:
        return 1, f"[ERROR] {e}"


def _is_git_repo(path: str = None) -> bool:
    """Verifica si el directorio es un repo git."""
    code, _ = _git(["rev-parse", "--git-dir"], cwd=path)
    return code == 0


def _log_action(action: str, branch: str, details: str = ""):
    """Log de acciones de worktree."""
    logs = []
    if os.path.exists(WORKTREE_LOG):
        try:
            with open(WORKTREE_LOG, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            pass
    logs.append({
        "ts": datetime.now().isoformat(),
        "action": action,
        "branch": branch,
        "details": details
    })
    logs = logs[-50:]
    with open(WORKTREE_LOG, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


def create_worktree(branch_name: str, base_branch: str = "main", repo_path: str = None) -> dict:
    """
    Crea un worktree aislado para una rama.
    
    Args:
        branch_name: Nombre de la rama/worktree
        base_branch: Rama base desde la que crear
        repo_path: Path del repo (default: detecta automáticamente)
    
    Returns:
        {"success": bool, "path": str, "branch": str, "error": str?}
    """
    cwd = repo_path or BASE_DIR
    
    if not _is_git_repo(cwd):
        return {"success": False, "error": f"No es un repo git: {cwd}"}
    
    os.makedirs(WORKTREES_DIR, exist_ok=True)
    wt_path = os.path.join(WORKTREES_DIR, branch_name)
    
    if os.path.exists(wt_path):
        return {"success": False, "error": f"Worktree ya existe: {wt_path}"}
    
    # Crear rama si no existe
    code, out = _git(["branch", "--list", branch_name], cwd=cwd)
    if branch_name not in out:
        code, out = _git(["branch", branch_name, base_branch], cwd=cwd)
        if code != 0:
            return {"success": False, "error": f"Error creando rama: {out}"}
    
    # Crear worktree
    code, out = _git(["worktree", "add", wt_path, branch_name], cwd=cwd)
    if code != 0:
        return {"success": False, "error": f"Error creando worktree: {out}"}
    
    _log_action("create", branch_name, wt_path)
    print(f"[Worktree] Creado: {wt_path} (rama: {branch_name})")
    return {"success": True, "path": wt_path, "branch": branch_name}


def list_worktrees(repo_path: str = None) -> list[dict]:
    """Lista todos los worktrees activos."""
    cwd = repo_path or BASE_DIR
    
    if not _is_git_repo(cwd):
        return []
    
    code, out = _git(["worktree", "list", "--porcelain"], cwd=cwd)
    if code != 0:
        return []
    
    worktrees = []
    current = {}
    for line in out.split("\n"):
        line = line.strip()
        if line.startswith("worktree "):
            if current:
                worktrees.append(current)
            current = {"path": line[9:]}
        elif line.startswith("HEAD "):
            current["head"] = line[5:]
        elif line.startswith("branch "):
            current["branch"] = line[7:].replace("refs/heads/", "")
        elif line == "bare":
            current["bare"] = True
        elif line == "detached":
            current["detached"] = True
    if current:
        worktrees.append(current)
    
    return worktrees


def merge_worktree(branch_name: str, target: str = "main", delete: bool = True, repo_path: str = None) -> dict:
    """
    Mergea un worktree/rama a la rama target.
    
    Args:
        branch_name: Rama del worktree a mergear
        target: Rama destino (default: main)
        delete: Si True, elimina el worktree después del merge
    """
    cwd = repo_path or BASE_DIR
    
    # Checkout a target
    code, out = _git(["checkout", target], cwd=cwd)
    if code != 0:
        return {"success": False, "error": f"Error cambiando a {target}: {out}"}
    
    # Merge
    code, out = _git(["merge", branch_name, "--no-edit"], cwd=cwd)
    if code != 0:
        return {"success": False, "error": f"Conflicto de merge: {out}"}
    
    _log_action("merge", branch_name, f"merged into {target}")
    
    # Limpiar
    if delete:
        remove_worktree(branch_name, repo_path=cwd)
    
    print(f"[Worktree] Mergeado: {branch_name} -> {target}")
    return {"success": True, "merged": branch_name, "into": target}


def remove_worktree(branch_name: str, repo_path: str = None) -> bool:
    """Elimina un worktree y su rama."""
    cwd = repo_path or BASE_DIR
    wt_path = os.path.join(WORKTREES_DIR, branch_name)
    
    # Eliminar worktree
    code, out = _git(["worktree", "remove", wt_path, "--force"], cwd=cwd)
    
    # Eliminar rama
    _git(["branch", "-d", branch_name], cwd=cwd)
    
    _log_action("remove", branch_name)
    print(f"[Worktree] Eliminado: {branch_name}")
    return True


def clean_worktrees(repo_path: str = None) -> int:
    """Limpia worktrees huérfanos."""
    cwd = repo_path or BASE_DIR
    code, out = _git(["worktree", "prune"], cwd=cwd)
    
    # Contar eliminados
    worktrees = list_worktrees(cwd)
    _log_action("clean", "all", f"{len(worktrees)} worktrees activos")
    print(f"[Worktree] Limpieza completada. {len(worktrees)} worktrees activos.")
    return len(worktrees)


def get_status(branch_name: str, repo_path: str = None) -> dict:
    """Estado de un worktree específico."""
    wt_path = os.path.join(WORKTREES_DIR, branch_name)
    if not os.path.exists(wt_path):
        return {"exists": False}
    
    code, status = _git(["status", "--short"], cwd=wt_path)
    code, log = _git(["log", "--oneline", "-5"], cwd=wt_path)
    code, diff_stat = _git(["diff", "--stat", "main"], cwd=wt_path)
    
    return {
        "exists": True,
        "path": wt_path,
        "branch": branch_name,
        "uncommitted_changes": status or "(clean)",
        "recent_commits": log,
        "diff_from_main": diff_stat or "(sin diferencias)"
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python git_worktree_manager.py create branch-name [base-branch]")
        print("  python git_worktree_manager.py list")
        print("  python git_worktree_manager.py status branch-name")
        print("  python git_worktree_manager.py merge branch-name [target-branch]")
        print("  python git_worktree_manager.py remove branch-name")
        print("  python git_worktree_manager.py clean")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "create" and len(sys.argv) >= 3:
        branch = sys.argv[2]
        base = sys.argv[3] if len(sys.argv) > 3 else "main"
        result = create_worktree(branch, base)
        if result["success"]:
            print(f"  OK: {result['path']}")
        else:
            print(f"  ERROR: {result['error']}")

    elif cmd == "list":
        wts = list_worktrees()
        print(f"\nWORKTREES ({len(wts)}):\n")
        for wt in wts:
            branch = wt.get("branch", "detached")
            print(f"  {branch}: {wt['path']}")

    elif cmd == "status" and len(sys.argv) >= 3:
        status = get_status(sys.argv[2])
        for k, v in status.items():
            print(f"  {k}: {v}")

    elif cmd == "merge" and len(sys.argv) >= 3:
        branch = sys.argv[2]
        target = sys.argv[3] if len(sys.argv) > 3 else "main"
        result = merge_worktree(branch, target)
        print(f"  {'OK' if result['success'] else 'ERROR'}: {result}")

    elif cmd == "remove" and len(sys.argv) >= 3:
        remove_worktree(sys.argv[2])

    elif cmd == "clean":
        clean_worktrees()

    else:
        print(f"Comando desconocido: {cmd}")
