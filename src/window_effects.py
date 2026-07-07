import ctypes
import platform
from ctypes import wintypes

# ==========================================================
# Windows API
# ==========================================================

user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi

# ==========================================================
# Constants
# ==========================================================

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_SYSTEMBACKDROP_TYPE = 38

DWMWCP_DEFAULT = 0
DWMWCP_DONOTROUND = 1
DWMWCP_ROUND = 2
DWMWCP_ROUNDSMALL = 3

DWMSBT_AUTO = 0
DWMSBT_NONE = 1
DWMSBT_MAINWINDOW = 2
DWMSBT_TRANSIENTWINDOW = 3
DWMSBT_TABBEDWINDOW = 4

ACCENT_DISABLED = 0
ACCENT_ENABLE_GRADIENT = 1
ACCENT_ENABLE_TRANSPARENTGRADIENT = 2
ACCENT_ENABLE_BLURBEHIND = 3
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4

WCA_ACCENT_POLICY = 19

# ==========================================================
# Structures
# ==========================================================


class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_int)
    ]


class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.c_void_p),
        ("SizeOfData", ctypes.c_size_t)
    ]


# ==========================================================
# Internal Function
# ==========================================================


def _set_window_composition(hwnd, accent_state, gradient_color=0xCC202020):
    """
    Enables Blur/Acrylic.

    gradient_color format:

    AABBGGRR
    """

    accent = ACCENT_POLICY()

    accent.AccentState = accent_state
    accent.AccentFlags = 2
    accent.GradientColor = gradient_color
    accent.AnimationId = 0

    data = WINDOWCOMPOSITIONATTRIBDATA()

    data.Attribute = WCA_ACCENT_POLICY
    data.SizeOfData = ctypes.sizeof(accent)
    data.Data = ctypes.cast(
        ctypes.pointer(accent),
        ctypes.c_void_p
    )

    set_window = user32.SetWindowCompositionAttribute
    set_window.argtypes = (
        wintypes.HWND,
        ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)
    )

    set_window(hwnd, ctypes.byref(data))


# ==========================================================
# Blur
# ==========================================================


def enable_blur(hwnd):
    """
    Windows 10 Blur
    """
    _set_window_composition(
        hwnd,
        ACCENT_ENABLE_BLURBEHIND
    )


# ==========================================================
# Acrylic
# ==========================================================


def enable_acrylic(hwnd):
    """
    Windows 10 Acrylic

    Default tint:
    Semi-transparent dark gray.
    """

    _set_window_composition(
        hwnd,
        ACCENT_ENABLE_ACRYLICBLURBEHIND,
        0xCC202020
    )


# ==========================================================
# Mica
# ==========================================================


def enable_mica(hwnd):
    """
    Windows 11 Mica

    Only works on Windows 11.
    """

    value = ctypes.c_int(DWMSBT_MAINWINDOW)

    dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_SYSTEMBACKDROP_TYPE,
        ctypes.byref(value),
        ctypes.sizeof(value)
    )


# ==========================================================
# Rounded Corners
# ==========================================================


def enable_rounded_corners(hwnd):

    preference = ctypes.c_int(DWMWCP_ROUND)

    dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_WINDOW_CORNER_PREFERENCE,
        ctypes.byref(preference),
        ctypes.sizeof(preference)
    )


# ==========================================================
# Dark Mode Title Bar
# ==========================================================


def enable_dark_title_bar(hwnd):

    value = ctypes.c_int(True)

    dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_USE_IMMERSIVE_DARK_MODE,
        ctypes.byref(value),
        ctypes.sizeof(value)
    )


# ==========================================================
# Window Shadow
# ==========================================================


class MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth", ctypes.c_int),
        ("cxRightWidth", ctypes.c_int),
        ("cyTopHeight", ctypes.c_int),
        ("cyBottomHeight", ctypes.c_int)
    ]


def enable_shadow(hwnd):

    margins = MARGINS(-1, -1, -1, -1)

    dwmapi.DwmExtendFrameIntoClientArea(
        hwnd,
        ctypes.byref(margins)
    )


# ==========================================================
# DPI Scaling
# ==========================================================


def get_scale_factor():

    try:

        user32.SetProcessDPIAware()

        dc = user32.GetDC(0)

        LOGPIXELSX = 88

        gdi32 = ctypes.windll.gdi32

        dpi = gdi32.GetDeviceCaps(dc, LOGPIXELSX)

        user32.ReleaseDC(0, dc)

        return dpi / 96

    except Exception:

        return 1.0


# ==========================================================
# Windows Version
# ==========================================================


def is_windows_11():

    version = platform.version()

    try:

        build = int(version.split(".")[-1])

        return build >= 22000

    except Exception:

        return False


# ==========================================================
# Initialize Effects
# ==========================================================


def apply_window_effects(hwnd):

    enable_shadow(hwnd)

    enable_rounded_corners(hwnd)

    enable_dark_title_bar(hwnd)

    if is_windows_11():
        enable_mica(hwnd)
    else:
        enable_acrylic(hwnd)