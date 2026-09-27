"""Light status skill — stdlib only (no psutil/pyautogui). Port of helpers.cpu() idea."""
import ctypes, datetime, shutil, os

class MEM(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPF", ctypes.c_ulonglong), ("ullAvailPF", ctypes.c_ulonglong),
                ("ullTotalV", ctypes.c_ulonglong), ("ullAvailV", ctypes.c_ulonglong),
                ("ullExV", ctypes.c_ulonglong)]

def ram():
    m = MEM(); m.dwLength = ctypes.sizeof(MEM)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    total = m.ullTotalPhys / 1e9
    free = m.ullAvailPhys / 1e9
    return f"RAM {total-free:.1f} of {total:.1f} GB used, {free:.1f} free ({m.dwMemoryLoad}% load)"

def wish():
    h = datetime.datetime.now().hour
    daypart = "morning" if h < 12 else "afternoon" if h < 18 else "evening"
    return f"Good {daypart}, sir. I am JARVIS. {ram()}."

def disk():
    t, u, f = shutil.disk_usage("C:\\")
    return f"Disk C free {f/1e9:.0f} of {t/1e9:.0f} GB."

def now():
    return datetime.datetime.now().strftime("It is %H:%M on %d %b.")
