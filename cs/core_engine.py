import pymem
import pymem.process
import requests
import ctypes
import time
import struct

# --- СИСТЕМНЫЕ ВЫЗОВЫ WINDOWS (GDI) ---
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
hdc = user32.GetDC(0) # Получаем контекст рисования поверх всего экрана

# Создаем перо для рисования (Цвет: 0x00DF64 - наш неоновый зеленый, Толщина: 2)
GREEN_PEN = gdi32.CreatePen(0, 2, 0x00DF64)
gdi32.SelectObject(hdc, GREEN_PEN)

# --- АВТО-ОФФСЕТЫ ---
try:
    off = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json").json()
    dll = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json").json()
    
    dwEntityList = off['client_dll']['dwEntityList']
    dwLocalPlayerPawn = off['client_dll']['dwLocalPlayerPawn']
    dwViewMatrix = off['client_dll']['dwViewMatrix']
    
    m_iTeamNum = dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
    m_iHealth = dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
    m_vOldOrigin = dll['client.dll']['classes']['C_BasePlayerPawn']['fields']['m_vOldOrigin']
except Exception as e:
    print(f"Error fetching offsets: {e}")

def world_to_screen(matrix, pos, width, height):
    # Математика проекции 3D координат в 2D пиксели экрана
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
            self.sw = user32.GetSystemMetrics(0) # Ширина монитора
            self.sh = user32.GetSystemMetrics(1) # Высота монитора
            print(f"[PenguinAI: GDI] WH Active. Screen: {self.sw}x{self.sh}")
        except:
            print("[!] CS2.exe not found!")
            time.sleep(3)
            exit()

    def draw_box(self, x, y, w, h):
        # Рисуем рамку через LineTo (самый надежный способ в GDI)
        gdi32.MoveToEx(hdc, x - w, y - h, None)
        gdi32.LineTo(hdc, x + w, y - h)
        gdi32.LineTo(hdc, x + w, y + h)
        gdi32.LineTo(hdc, x - w, y + h)
        gdi32.LineTo(hdc, x - w, y - h)

    def run(self):
        while True:
            try:
                # Читаем матрицу вида
                vm = [self.pm.read_float(self.client + dwViewMatrix + (i * 4)) for i in range(16)]
                lp = self.pm.read_longlong(self.client + dwLocalPlayerPawn)
                lt = self.pm.read_int(lp + m_iTeamNum)
                el = self.pm.read_longlong(self.client + dwEntityList)

                for i in range(1, 64):
                    # Цепочка энтити для CS2
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
                        
                        # Если враг жив и не в нашей команде
                        if 0 < hp <= 100 and team != lt:
                            pos = self.pm.read_vec3(pawn + m_vOldOrigin)
                            screen = world_to_screen(vm, pos, self.sw, self.sh)
                            
                            if screen:
                                # Рисуем бокс (размеры подбираются под дистанцию, пока статичные 15x30)
                                self.draw_box(screen[0], screen[1], 15, 35)
            except:
                pass
            time.sleep(0.01) # Чтобы не вешать проц (100 FPS рисовки)

if __name__ == "__main__":
    PenguinGDI().run()
