import pyMeow as pmw
import requests, pymem, pymem.process, struct, sys

# --- АВТО-ОФФСЕТЫ ---
try:
    offsets = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json").json()
    client_dll = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json").json()
except:
    print("[ERROR] Не удалось стянуть оффсеты с GitHub!")
    sys.exit()

dwEntityList = offsets['client_dll']['dwEntityList']
dwLocalPlayerPawn = offsets['client_dll']['dwLocalPlayerPawn']
dwViewMatrix = offsets['client_dll']['dwViewMatrix']

m_iTeamNum = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
m_iHealth = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
m_vOldOrigin = client_dll['client.dll']['classes']['C_BasePlayerPawn']['fields']['m_vOldOrigin']

class PenguinWH:
    def __init__(self):
        try:
            self.pm = pymem.Pymem("cs2.exe")
            self.client = pymem.process.module_from_name(self.pm.process_handle, "client.dll").lpBaseOfDll
            # Инициализация оверлея (важно: название окна должно совпадать!)
            self.overlay = pmw.overlay_init("Counter-Strike 2", fps=144)
            self.width = pmw.get_window_width("Counter-Strike 2")
            self.height = pmw.get_window_height("Counter-Strike 2")
            print(f"[PenguinAI] Connected! Window: {self.width}x{self.height}")
        except Exception as e:
            print(f"[!] Ошибка запуска: {e}. Сначала запусти CS2!")
            sys.exit()

    def run(self):
        while pmw.overlay_loop():
            pmw.begin_drawing()
            
            # Читаем матрицу (ровно 16 флоатов)
            try:
                view_matrix = []
                for i in range(16):
                    view_matrix.append(self.pm.read_float(self.client + dwViewMatrix + (i * 4)))
                
                local_player = self.pm.read_longlong(self.client + dwLocalPlayerPawn)
                local_team = self.pm.read_int(local_player + m_iTeamNum)
                entity_list = self.pm.read_longlong(self.client + dwEntityList)
            except: continue

            for i in range(1, 64):
                try:
                    # Поиск энтити в Source 2 (хитрая цепочка поинтеров)
                    list_entry = self.pm.read_longlong(entity_list + (8 * (i & 0x7FFF) >> 9) + 16)
                    if not list_entry: continue
                    
                    pawn_handle = self.pm.read_long(list_entry + 120 * (i & 0x1FF))
                    if not pawn_handle: continue
                    
                    # Получаем сам Pawn
                    list_entry2 = self.pm.read_longlong(entity_list + (8 * (pawn_handle & 0x7FFF) >> 9) + 16)
                    pawn_ptr = self.pm.read_longlong(list_entry2 + 120 * (pawn_handle & 0x1FF))
                    
                    if not pawn_ptr or pawn_ptr == local_player: continue

                    health = self.pm.read_int(pawn_ptr + m_iHealth)
                    team = self.pm.read_int(pawn_ptr + m_iTeamNum)

                    # Рисуем только живых врагов
                    if 0 < health <= 100 and team != local_team:
                        pos = self.pm.read_vec3(pawn_ptr + m_vOldOrigin)
                        
                        # Пересчет в экранные координаты
                        screen = pmw.world_to_screen(view_matrix, pos, self.width, self.height)
                        
                        if screen:
                            # РИСУЕМ
                            # Сочный неоновый бокс (квадрат)
                            head_pos = {'x': screen['x'], 'y': screen['y'] - 5}
                            pmw.draw_rectangle_lines(
                                screen['x'] - 15, screen['y'] - 30, 
                                30, 60, pmw.get_color("lime"), 2
                            )
                            pmw.draw_text(f"HP: {health}", screen['x'] - 15, screen['y'] - 45, 12, pmw.get_color("white"))
                            # Отладка в консоль (если завалено — закомментируй)
                            # print(f"Found Enemy at {screen['x']}, {screen['y']}")
                except:
                    continue

            pmw.end_drawing()

if __name__ == "__main__":
    PenguinWH().run()
