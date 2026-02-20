import win32gui
import win32process

import keyboard

def get_hwnds_for_pid(pid : int):
    def callback(hwnd : int, hwnds : list):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                hwnds.append(hwnd)
        return True
    
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds


def activate(pid : int):
    for hwnd in get_hwnds_for_pid(pid):
        keyboard.send("alt")
        win32gui.SetForegroundWindow(hwnd)

def send_key(pid : int, key : str):
    activate(pid)
    keyboard.send(key)