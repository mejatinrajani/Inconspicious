import ctypes

def make_stealth(window):
    hwnd = int(window.winId())
    user32 = ctypes.windll.user32
    WDA_EXCLUDEFROMCAPTURE = 0x00000011
    user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
