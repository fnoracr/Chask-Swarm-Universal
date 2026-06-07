import ctypes

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

def callback(hwnd, extra):
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value
        with open("C:\\Program Files\\Chask_Swarm\\Advanced_Tools\\windows.txt", "a", encoding="utf-8") as f:
            f.write(f"HWND: {hwnd}, Title: {title}\n")
    return True

# clear the file first
with open("C:\\Program Files\\Chask_Swarm\\Advanced_Tools\\windows.txt", "w", encoding="utf-8") as f:
    f.write("")

user32.EnumWindows(WNDENUMPROC(callback), 0)
