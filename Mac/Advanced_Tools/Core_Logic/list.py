import ctypes
user32 = ctypes.windll.user32
titles = []
def cb(h, e):
    b = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(h, b, 512)
    t = b.value
    if t: titles.append(t)
    return True
user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)(cb), 0)
for t in titles:
    if "charm" in t.lower() or "charm" in t.lower() or "resolving" in t.lower():
        print(t)
