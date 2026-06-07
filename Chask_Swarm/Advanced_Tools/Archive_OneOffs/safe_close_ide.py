import ctypes
import psutil
import time

user32 = ctypes.windll.user32
hwnds = []

def callback(hwnd, extra):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                p = psutil.Process(pid.value)
                if "charm" in p.name().lower():
                    hwnds.append(hwnd)
            except:
                pass
    return True

user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)(callback), 0)

for hwnd in hwnds:
    print(f"Cerrando ventana {hwnd}")
    user32.PostMessageW(hwnd, 0x0010, 0, 0) # WM_CLOSE

time.sleep(2)

# Si quedan procesos, matarlos
for p in psutil.process_iter(['name']):
    if "charm" in p.info['name'].lower():
        try:
            p.kill()
        except:
            pass
