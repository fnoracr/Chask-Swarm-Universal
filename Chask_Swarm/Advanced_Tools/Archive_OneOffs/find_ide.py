import ctypes
import psutil

user32 = ctypes.windll.user32
pids = [p.pid for p in psutil.process_iter() if 'charm' in p.name().lower() or 'code' in p.name().lower()]
titles = []

def cb(h, e):
    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
    if pid.value in pids:
        b = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(h, b, 512)
        if b.value:
            titles.append(f"{h}: {b.value} (PID: {pid.value})")
    return True

user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)(cb), 0)
for t in titles:
    print(t)
