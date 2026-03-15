import pymem
import pymem.process
import requests
import ctypes
import time
from math import sqrt

# --- СТАНДАРТНЫЕ ВИНДОВЫЕ ШТУКИ (GDI) ---
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
hdc = user32.GetDC(0) # Получаем контекст всего экрана

# Цвет для рисовки (неоновый зеленый)
GREEN_PEN = gdi32.CreatePen(0, 2, 0x00DF64) 
gdi32.SelectObject(hdc, GREEN_PEN)

# --- ОФФСЕТЫ ---
try:
    off = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json").json()
    dll = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json").json()
    
    dwEntityList = off['client_dll']['dwEntityList']
    dwLocalPlayerPawn = off['client_dll']['dwLocalPlayerPawn']
    dwViewMatrix = off['client_dll']['dwViewMatrix']
    m_iTeamNum = dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
    m_iHealth = dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
    m_vOldOrigin = dll['client.dll']['classes']['C_BasePlayerPawn']['fields']['m_vOldOrigin']
except:
    print("Error fetching offsets!")

def world_to_screen(matrix, pos, width, height):
    # Упрощенная математика проекции для GDI
    w = matrix[12] * pos.x + matrix[13] * pos.y + matrix[14] * pos.z + matrix[15]
    if w < 0.01: return None
    x = (matrix[0] * pos.x + matrix[1] * pos.y + matrix[2] * pos.z + matrix[3]) / w
    y = (matrix[4] * pos.x + matrix[5] * pos.y + matrix[6] * pos.z + matrix[7]) / w
    px = (width / 2) + (x * width / 2)
    py = (height / 2) - (y * height / 2)
    return int(px), int(py)

class PenguinGDI:
    def __init__(self):
        try:
            self.pm = pymem.Pymem("cs2.exe")
            self.client = pymem.process.module_from_name(self.pm.process_handle, "client.dll").lpBaseOfDll
            self.sw = user32.GetSystemMetrics(0)
            self.sh = user32.GetSystemMetrics(1)
            print(f"[PenguinAI: GDI] Ready! Screen: {self.sw}x{self.sh}")
        except:
            print("CS2 not found!")

    def draw_box(self, x, y, w, h):
        # Рисуем квадрат через GDI (Rectangle)
        gdi32.MoveToEx(hdc, x - w, y - h, None)
        gdi32.LineTo(hdc, x + w, y - h)
        gdi32.LineTo(hdc, x + w, y + h)
        gdi32.LineTo(hdc, x - w, y + h)
        gdi32.LineTo(hdc, x - w, y - h)

    def run(self):
        while True:
            try:
                vm = [self.pm.read_float(self.client + dwViewMatrix + (i * 4)) for i in range(16)]
                lp = self.pm.read_longlong(self.client + dwLocalPlayerPawn)
                lt = self.pm.read_int(lp + m_iTeamNum)
                el = self.pm.read_longlong(self.client + dwEntityList)

                for i in range(1, 64):
                    # Базовая цепочка для энтити
                    ent_entry = self.pm.read_longlong(el + (8 * (i & 0x7FFF) >> 9) + 16)
                    if not ent_entry: continue
                    ctrl = self.pm.read_longlong(ent_entry + 120 * (i & 0x1FF))
                    if not ctrl: continue
                    p_handle = self.pm.read_long(ctrl + 0x7FC)
                    p_entry = self.pm.read_longlong(el + (8 * (p_handle & 0x7FFF) >> 9) + 16)
                    pawn = self.pm.read_longlong(p_entry + 120 * (p_handle & 0x1FF))

                    if pawn and pawn != lp:
                        hp = self.pm.read_int(pawn + m_iHealth)
                        team = self.pm.read_int(pawn + m_iTeamNum)
                        if 0 < hp <= 100 and team != lt:
                            pos = self.pm.read_vec3(pawn + m_vOldOrigin)
                            screen = world_to_screen(vm, pos, self.sw, self.sh)
                            if screen:
                                self.draw_box(screen[0], screen[1], 15, 30)
            except: pass
            time.sleep(0.01)

if __name__ == "__main__":
    PenguinGDI().run()
