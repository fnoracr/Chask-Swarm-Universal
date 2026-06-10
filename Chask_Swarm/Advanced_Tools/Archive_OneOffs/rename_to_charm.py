import ctypes
import time

user32 = ctypes.windll.user32

print("Cambiando el foco a la ventana actual en 3 segundos...")
time.sleep(3)
hwnd = user32.GetForegroundWindow()

# Obtenemos el titulo actual
length = user32.GetWindowTextLengthW(hwnd)
buff = ctypes.create_unicode_buffer(length + 1)
user32.GetWindowTextW(hwnd, buff, length + 1)
old_title = buff.value

# Le concatenamos " - Charm"
new_title = old_title + " - Charm"
user32.SetWindowTextW(hwnd, new_title)

print(f"Ventana renombrada a: {new_title}")
