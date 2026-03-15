import pyMeow as pmw
import requests, pymem, pymem.process, sys, time

# --- АВТО-ОФФСЕТЫ ---
try:
    offsets = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json").json()
    client_dll = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json").json()
except:
    print("[ERROR] Failed to fetch offsets!")
    sys.exit()

# Адреса
dwEntityList = offsets['client_dll']['dwEntityList']
dwLocalPlayerPawn = offsets['client_dll']['dwLocalPlayerPawn']
dwViewMatrix = offsets['client_dll']['dwViewMatrix']

# Поля
m_iTeamNum = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
m_iHealth = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
m_vOldOrigin = client_dll['client.dll']['classes']['C_BasePlayerPawn']['fields']['m_vOldOrigin']
m_entitySpottedState = client_dll['client.dll']['classes']['C_CSPlayerPawnBase']['fields']['m_entitySpottedState']

class PenguinAI_CS2:
    def __init__(self):
        try:
            self.pm = pymem.Pymem("cs2.exe")
            self.client = pymem.process.module_from_name(self.pm.process_handle, "client.dll").lpBaseOfDll
            self.overlay = pmw.overlay_init("Counter-Strike 2", fps=144)
            self.width = pmw.get_window_width("Counter-Strike 2")
            self.height = pmw.get_window_height("Counter-Strike 2")
            
            # Настройки функций
            self.menu_open = True
            self.wh_enabled = True
            self.aim_enabled = False
            self.trigger_enabled = False
            self.bhop_enabled = False
            
            print(f"[PenguinAI: CS2] Loaded! Version: 1.2")
        except:
            print("[!] CS2 not found. Run the game first!")
            sys.exit()

    def draw_menu(self):
        if not self.menu_open: return
        
        # Матовый темный фон меню
        pmw.draw_rectangle(10, 10, 200, 260, pmw.get_color("#0D0E11"))
        pmw.draw_rectangle_lines(10, 10, 200, 260, pmw.get_color("#00DF64"), 2)
        
        pmw.draw_text("PenguinAI: CS2", 25, 25, 18, pmw.get_color("#00DF64"))
        pmw.draw_line(20, 50, 200, 50, pmw.get_color("#22262E"), 1)

        # Кнопки (функционал будем вешать позже)
        self.draw_toggle("WH (Visuals)", 70, self.wh_enabled)
        self.draw_toggle("AIM (Soon)", 110, self.aim_enabled)
        self.draw_toggle("TRIGGER (Soon)", 150, self.trigger_enabled)
        self.draw_toggle("B-HOP (Soon)", 190, self.bhop_enabled)
        
        pmw.draw_text("Press INSERT to hide", 25, 235, 10, pmw.get_color("#444"))

    def draw_toggle(self, text, y, state):
        color = "#00DF64" if state else "#ff4757"
        status = "[ON]" if state else "[OFF]"
        pmw.draw_text(f"{text}:", 25, y, 13, pmw.get_color("white"))
        pmw.draw_text(status, 150, y, 13, pmw.get_color(color))

    def run(self):
        while pmw.overlay_loop():
            # Управление меню
            if pmw.key_pressed(0x2D): # INSERT
                self.menu_open = not self.menu_open
                time.sleep(0.2)

            pmw.begin_drawing()
            self.draw_menu()

            try:
                # Читаем матрицу для ESP
                view_matrix = [self.pm.read_float(self.client + dwViewMatrix + (i * 4)) for i in range(16)]
                local_player = self.pm.read_longlong(self.client + dwLocalPlayerPawn)
                local_team = self.pm.read_int(local_player + m_iTeamNum)
                entity_list = self.pm.read_longlong(self.client + dwEntityList)

                for i in range(1, 64):
                    # Ищем энтити
                    list_entry = self.pm.read_longlong(entity_list + (8 * (i & 0x7FFF) >> 9) + 16)
                    if not list_entry: continue
                    controller_ptr = self.pm.read_longlong(list_entry + 120 * (i & 0x1FF))
                    if not controller_ptr: continue
                    pawn_handle = self.pm.read_long(controller_ptr + 0x7FC)
                    if not pawn_handle: continue
                    
                    list_entry2 = self.pm.read_longlong(entity_list + (8 * (pawn_handle & 0x7FFF) >> 9) + 16)
                    pawn_ptr = self.pm.read_longlong(list_entry2 + 120 * (pawn_handle & 0x1FF))
                    
                    if not pawn_ptr or pawn_ptr == local_player: continue

                    health = self.pm.read_int(pawn_ptr + m_iHealth)
                    team = self.pm.read_int(pawn_ptr + m_iTeamNum)

                    if 0 < health <= 100 and team != local_team:
                        # --- МЕТОД 1: RADAR HACK (100% результат) ---
                        # Ставим флаг "замечен", чтобы враг появился на игровой мини-карте
                        self.pm.write_bool(pawn_ptr + m_entitySpottedState + 0x8, True)

                        # --- МЕТОД 2: ESP OVERLAY ---
                        if self.wh_enabled:
                            pos = self.pm.read_vec3(pawn_ptr + m_vOldOrigin)
                            screen = pmw.world_to_screen(view_matrix, pos, self.width, self.height)
                            
                            if screen:
                                pmw.draw_rectangle_lines(screen['x'] - 15, screen['y'] - 40, 30, 60, pmw.get_color("#00DF64"), 1)
                                pmw.draw_text(f"{health} HP", screen['x'] - 15, screen['y'] - 55, 10, pmw.get_color("white"))
            except:
                pass

            pmw.end_drawing()

if __name__ == "__main__":
    PenguinAI_CS2().run()
