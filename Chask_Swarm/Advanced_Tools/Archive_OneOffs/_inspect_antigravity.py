"""Inspecciona TODOS los HWNDs de Charm, incluyendo el que tiene el chat."""
import uiautomation as auto
import sys, io, ctypes, psutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
user32 = ctypes.windll.user32

target_pid = None
for proc in psutil.process_iter(['pid', 'name']):
    if 'charm' in proc.info['name'].lower():
        target_pid = proc.info['pid']
        break

if not target_pid:
    print("PROCESO NO ENCONTRADO"); sys.exit(1)

# Obtener TODOS los HWNDs del proceso (visibles e invisibles)
hwnd_all = []
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
def cb(hwnd, _):
    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == target_pid:
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buf, 256)
        title = buf.value
        visible = user32.IsWindowVisible(hwnd)
        hwnd_all.append((hwnd, title, visible))
    return True
user32.EnumWindows(WNDENUMPROC(cb), 0)

print(f"Todos los HWNDs del proceso Charm (PID={target_pid}):")
for h, t, v in hwnd_all:
    print(f"  HWND={h} | Visible={v} | Title='{t}'")

print()

# Inspeccionar cada HWND buscando controles de input
def recurse(c, depth=0):
    if depth > 8:
        return
    try:
        ct   = str(c.ControlTypeName)
        name = c.Name or ""
        aid  = c.AutomationId or ""

        is_edit = "Edit" in ct or "Document" in ct

        # Mostrar TODOS los controles visibles con nombre o solo los Edit
        if name or is_edit:
            print(f"{'  '*depth}[{ct}] Name='{name}' AutoId='{aid}'")

        for child in c.GetChildren():
            recurse(child, depth + 1)
    except Exception:
        pass

for h, t, v in hwnd_all:
    print(f"\n{'='*60}")
    print(f"Inspeccionando HWND={h} Title='{t}' Visible={v}")
    print('='*60)
    try:
        ctrl = auto.ControlFromHandle(h)
        if ctrl:
            recurse(ctrl)
    except Exception as e:
        print(f"  Error: {e}")
