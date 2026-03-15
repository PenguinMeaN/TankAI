import os
import sys
import ctypes
import requests
import subprocess
from ctypes import wintypes

# --- КОНСТАНТЫ WINAPI ---
PROCESS_ALL_ACCESS = 0x001F0FFF
MEM_COMMIT = 0x00001000
MEM_RESERVE = 0x00002000
PAGE_READWRITE = 0x04

kernel32 = ctypes.windll.kernel32

# --- НАСТРОЙКИ ДЛЯ CS2 ---
TARGET_PROCESS = "cs2.exe"
# Ссылка на будущую скомпилированную DLL на твоем Гитхабе
DLL_URL = "https://raw.githubusercontent.com/PenguinMeaN/TankAI/main/cs/penguin_cheat.dll"
DLL_LOCAL_PATH = os.path.abspath("penguin_cs2.dll")

def get_pid(process_name):
    """Ищет процесс по имени и возвращает его PID"""
    try:
        output = subprocess.check_output(["tasklist", "/fi", f"imagename eq {process_name}", "/nh", "/fo", "csv"]).decode('cp866', errors='ignore')
        if process_name.lower() in output.lower():
            for line in output.splitlines():
                if process_name.lower() in line.lower():
                    pid = line.strip().split('","')[1]
                    return int(pid)
    except Exception:
        pass
    return None

def inject(pid, dll_path):
    """Главная магия внедрения DLL в чужой процесс"""
    # 1. Открываем процесс с полными правами
    h_process = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not h_process:
        print(f"[ERROR] Could not open process {TARGET_PROCESS}. Please run Launcher as Administrator!")
        return False

    # 2. Выделяем память в CS2 под путь к нашей DLL
    dll_path_bytes = dll_path.encode('utf-8')
    arg_address = kernel32.VirtualAllocEx(h_process, 0, len(dll_path_bytes), MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE)
    if not arg_address:
        print("[ERROR] Failed to allocate memory in target process.")
        return False
        
    # 3. Записываем путь к DLL в выделенную память
    written = wintypes.DWORD(0)
    kernel32.WriteProcessMemory(h_process, arg_address, dll_path_bytes, len(dll_path_bytes), ctypes.byref(written))

    # 4. Находим адрес стандартной функции загрузки библиотек (LoadLibraryA)
    h_kernel32 = kernel32.GetModuleHandleW("kernel32.dll")
    load_lib_addr = kernel32.GetProcAddress(h_kernel32, b"LoadLibraryA")

    # 5. Создаем удаленный поток, заставляя CS2 загрузить нашу DLL
    thread_id = wintypes.DWORD(0)
    h_thread = kernel32.CreateRemoteThread(h_process, None, 0, load_lib_addr, arg_address, 0, ctypes.byref(thread_id))
    
    if not h_thread:
        print("[ERROR] Failed to create remote thread.")
        return False
        
    print("[SUCCESS] DLL Injected successfully! Check the game.")
    return True

if __name__ == "__main__":
    print(f"[PenguinAI] Starting Injector for {TARGET_PROCESS}...")
    
    # ШАГ 1: Проверяем, запущена ли игра
    pid = get_pid(TARGET_PROCESS)
    if not pid:
        print(f"[ERROR] {TARGET_PROCESS} is not running! Please start the game first.")
        # Ждем 3 секунды, чтобы пользователь успел прочитать лог перед закрытием
        import time; time.sleep(3)
        sys.exit()
        
    print(f"[PenguinAI] Found {TARGET_PROCESS} (PID: {pid})")

    # ШАГ 2: Скачиваем актуальную DLL с сервера
    print("[PenguinAI] Downloading latest DLL...")
    try:
        # Пока мы не написали DLL, этот код закомментирован, чтобы не выдавать ошибку 404
        '''
        response = requests.get(DLL_URL)
        if response.status_code == 200:
            with open(DLL_LOCAL_PATH, "wb") as f:
                f.write(response.content)
            print("[PenguinAI] DLL download complete.")
        else:
            print(f"[ERROR] Failed to download DLL (Status: {response.status_code})")
            sys.exit()
        '''
        
        # ЗАГЛУШКА ДЛЯ ТЕСТА: Создаем пустой файл, чтобы скрипт прошел дальше
        if not os.path.exists(DLL_LOCAL_PATH):
            with open(DLL_LOCAL_PATH, "wb") as f:
                f.write(b"MOCK")
        print("[PenguinAI] DLL ready.")

    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        sys.exit()

    # ШАГ 3: Инжект!
    print(f"[PenguinAI] Injecting into {TARGET_PROCESS} memory...")
    if inject(pid, DLL_LOCAL_PATH):
        print("[PenguinAI] All done. You can close this window if it doesn't close automatically.")
