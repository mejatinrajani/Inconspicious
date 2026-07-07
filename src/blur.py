import ctypes
from ctypes import wintypes

def enable_blur(hwnd):
    accent_policy = ctypes.Structure
    class ACCENT_POLICY(ctypes.Structure):
        _fields_ = [
            ("AccentState", ctypes.c_int),
            ("AccentFlags", ctypes.c_int),
            ("GradientColor", ctypes.c_int),
            ("AnimationId", ctypes.c_int)
        ]

    class WINCOMPATTRDATA(ctypes.Structure):
        _fields_ = [
            ("Attribute", ctypes.c_int),
            ("Data", ctypes.c_void_p),
            ("SizeOfData", ctypes.c_size_t)
        ]

    accent = ACCENT_POLICY()
    accent.AccentState = 3  # ACCENT_ENABLE_BLURBEHIND

    data = WINCOMPATTRDATA()
    data.Attribute = 19  # WCA_ACCENT_POLICY
    data.Data = ctypes.addressof(accent)
    data.SizeOfData = ctypes.sizeof(accent)

    user32 = ctypes.windll.user32
    user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
