"""Accept only an explicitly requested disposable certificate in a Windows test."""
import ctypes
from ctypes import wintypes
import re
import threading


def accept_matching_dialog(thumbprint):
    user = ctypes.WinDLL("user32", use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user.GetDlgItem.argtypes = [wintypes.HWND, ctypes.c_int]
    user.GetDlgItem.restype = wintypes.HWND
    user.IsWindowEnabled.argtypes = [wintypes.HWND]
    handled = []

    def text(handle):
        value = ctypes.create_unicode_buffer(4096)
        user.GetWindowTextW(handle, value, len(value))
        return value.value

    @callback_type
    def inspect(handle, unused):
        if text(handle) not in {"Security Warning", "Root Certificate Store"}:
            return True
        contents = []

        @callback_type
        def child(child_handle, unused):
            contents.append(text(child_handle))
            return True

        user.EnumChildWindows(handle, child, 0)
        # The leaf is generated per fixture; exact SHA-1 matching prevents
        # touching prompts for another certificate or a personal application.
        normalized = re.sub(r"\s+", "", " ".join(contents)).upper()
        if thumbprint.upper() in normalized:
            button = user.GetDlgItem(handle, 6)  # IDYES
            if button and user.IsWindowEnabled(button):
                user.ShowWindow(handle, 0)
                user.PostMessageW(handle, 0x0111, 6, 0)
                handled.append(thumbprint)
        return True

    user.EnumWindows(inspect, 0)
    return bool(handled)


def with_certificate_dialog(thumbprint, action):
    finished = threading.Event()

    def observe():
        while not finished.wait(0.2):
            accept_matching_dialog(thumbprint)

    worker = threading.Thread(target=observe, daemon=True)
    worker.start()
    try:
        return action()
    finally:
        finished.set()
        worker.join(timeout=2)
