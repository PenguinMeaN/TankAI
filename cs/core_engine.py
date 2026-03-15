import pyMeow as pmw
import requests
import pymem
import pymem.process

# --- АВТО-ОФФСЕТЫ (Прямо из дампера) ---
offsets = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json").json()
client_dll = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json").json()

dwEntityList = offsets['client_dll']['dwEntityList']
dwLocalPlayerPawn = offsets['client_dll']['dwLocalPlayerPawn']
dwViewMatrix = offsets['client_dll']['dwViewMatrix']

m_iTeamNum = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
m_iHealth = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
m_vOldOrigin = client_dll['client.dll']['classes']['C_BasePlayerPawn']['fields']['m_vOldOrigin']

class PenguinESP:
    def __init__(self):
        try:
            self.pm = pymem.Pymem("cs2.exe")
            self.client = pymem.process.module_from_name(self.pm.process_handle, "client.dll").lpBaseOfDll
            # Инициализация оверлея pyMeow
            pmw.overlay_init("Counter-Strike 2", fps=144)
            print("[PenguinAI] WH Started Successfully!")
        except Exception as e:
            print(f"[ERROR] Run CS2 first! {e}")
            sys.exit()

    def run(self):
        while pmw.overlay_loop():
            pmw.begin_drawing()
            
            # Читаем матрицу вида (для World-to-Screen)
            view_matrix = self.pm.read_bytes(self.client + dwViewMatrix, 64)
            matrix = [sum(struct.unpack('f' * 4, view_matrix[i*16:i*16+16])) for i in range(4)] # Упрощенно
            # В pyMeow есть встроенная функция для матрицы, используем её
            v_matrix = []
            for i in range(16):
                v_matrix.append(self.pm.read_float(self.client + dwViewMatrix + (i * 4)))

            local_player = self.pm.read_longlong(self.client + dwLocalPlayerPawn)
            local_team = self.pm.read_int(local_player + m_iTeamNum)

            entity_list = self.pm.read_longlong(self.client + dwEntityList)
            
            for i in range(1, 64): # Проход по игрокам
                try:
                    list_entry = self.pm.read_longlong(entity_list + (8 * (i & 0x7FFF) >> 9) + 16)
                    pawn_handle = self.pm.read_long(list_entry + 120 * (i & 0x1FF))
                    
                    pawn_ptr = self.pm.read_longlong(list_entry + 120 * (pawn_handle & 0x1FF))
                    if not pawn_ptr or pawn_ptr == local_player: continue

                    health = self.pm.read_int(pawn_ptr + m_iHealth)
                    team = self.pm.read_int(pawn_ptr + m_iTeamNum)

                    if health > 0 and team != local_team:
                        # Получаем 3D позицию врага
                        pos = self.pm.read_vec3(pawn_ptr + m_vOldOrigin)
                        
                        # Проекция 3D -> 2D (World to Screen)
                        screen_pos = pmw.world_to_screen(v_matrix, pos, 1) # 1 - это разрешение
                        
                        if screen_pos:
                            # Рисуем бокс вокруг врага
                            # Для простоты рисуем круг/точку, пока не настроим размеры бокса
                            pmw.draw_circle(screen_pos['x'], screen_pos['y'], 5, pmw.get_color("green"))
                            pmw.draw_text(f"HP: {health}", screen_pos['x'], screen_pos['y'] - 15, 12, pmw.get_color("white"))
                except:
                    continue

            pmw.end_drawing()

if __name__ == "__main__":
    import struct, sys
     PenguinESP().run()
