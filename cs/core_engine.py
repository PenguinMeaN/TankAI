import pyMeow as pmw
import requests, pymem, pymem.process, sys, time

# --- CONFIG & OFFSETS ---
try:
    offsets = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json").json()
    client_dll = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json").json()
except:
    print("[ERROR] Cloud connection failed!")
    sys.exit()

dwEntityList = offsets['client_dll']['dwEntityList']
dwLocalPlayerPawn = offsets['client_dll']['dwLocalPlayerPawn']
dwViewMatrix = offsets['client_dll']['dwViewMatrix']

m_iTeamNum = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
m_iHealth = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
m_vOldOrigin = client_dll['client.dll']['classes']['C_BasePlayerPawn']['fields']['m_vOldOrigin']
m_entitySpottedState = client_dll['client.dll']['classes']['C_CSPlayerPawnBase']['fields']['m_entitySpottedState']

class PenguinAI_CS2:
    def __init__(self):
        try:
            self.pm = pymem.Pymem("cs2.exe")
            self.client = pymem.process.module_from_name(self.pm.process_handle, "client.dll").lpBaseOfDll
            
            # Инициализация оверлея с принудительным поиском окна
            self.overlay = pmw.overlay_init("Counter-Strike 2", fps=144)
            self.width = pmw.get_window_width("Counter-Strike 2")
            self.height = pmw.get_window_height("Counter-Strike 2")
            
            self.menu_open = True
            self.wh_enabled = True
            self.radar_enabled = True
            
            print(f"[PenguinAI: CS2] Overlay Synced: {self.width}x{self.height}")
        except Exception as e:
            print(f"[!] Critical Launch Error: {e}")
            sys.exit()

    def draw_menu(self):
        if not self.menu_open: return
        
        # Овальное меню в стиле v3.3
        pmw.draw_rectangle(20, 20, 220, 240, pmw.get_color("#0D0E11"))
        pmw.draw_rectangle_lines(20, 20, 220, 240, pmw.get_color("#00DF64"), 2)
        
        pmw.draw_text("PenguinAI: HUB", 40, 40, 18, pmw.get_color("#00DF64"))
        pmw.draw_line(30, 70, 230, 70, pmw.get_color("#22262E"), 1)

        self.draw_btn("WH Visuals", 90, self.wh_enabled)
        self.draw_btn("Radar Hack", 130, self.radar_enabled)
        self.draw_btn("Aim Bot", 170, False) # Soon
        
        pmw.draw_text("Press [INS] to toggle", 40, 220, 11, pmw.get_color("#444"))

    def draw_btn(self, text, y, active):
        color = "#00DF64" if active else "#555"
        pmw.draw_circle(45, y + 8, 5, pmw.get_color(color))
        pmw.draw_text(text, 65, y, 14, pmw.get_color("white"))

    def run(self):
        print("[SYSTEM] Loop Started. Press INSERT to test menu.")
        while pmw.overlay_loop():
            # Захват клавиши INSERT (0x2D)
            if pmw.key_pressed(0x2D):
                self.menu_open = not self.menu_open
                print(f"[DEBUG] Menu toggled: {self.menu_open}")
                time.sleep(0.2)

            pmw.begin_drawing()
            self.draw_menu()

            try:
                view_matrix = [self.pm.read_float(self.client + dwViewMatrix + (i * 4)) for i in range(16)]
                local_player = self.pm.read_longlong(self.client + dwLocalPlayerPawn)
                local_team = self.pm.read_int(local_player + m_iTeamNum)
                entity_list = self.pm.read_longlong(self.client + dwEntityList)

                for i in range(1, 64):
                    entry = self.pm.read_longlong(entity_list + (8 * (i & 0x7FFF) >> 9) + 16)
                    if not entry: continue
                    ctrl = self.pm.read_longlong(entry + 120 * (i & 0x1FF))
                    if not ctrl: continue
                    pawn_h = self.pm.read_long(ctrl + 0x7FC)
                    if not pawn_h: continue
                    
                    entry2 = self.pm.read_longlong(entity_list + (8 * (pawn_h & 0x7FFF) >> 9) + 16)
                    pawn_ptr = self.pm.read_longlong(entry2 + 120 * (pawn_h & 0x1FF))
                    
                    if not pawn_ptr or pawn_ptr == local_player: continue

                    hp = self.pm.read_int(pawn_ptr + m_iHealth)
                    team = self.pm.read_int(pawn_ptr + m_iTeamNum)

                    if 0 < hp <= 100 and team != local_team:
                        # Radar Hack
                        if self.radar_enabled:
                            self.pm.write_bool(pawn_ptr + m_entitySpottedState + 0x8, True)

                        # ESP Boxes
                        if self.wh_enabled:
                            pos = self.pm.read_vec3(pawn_ptr + m_vOldOrigin)
                            screen = pmw.world_to_screen(view_matrix, pos, self.width, self.height)
                            if screen:
                                pmw.draw_rectangle_lines(screen['x'] - 15, screen['y'] - 40, 30, 60, pmw.get_color("#00DF64"), 1)
            except: pass
            pmw.end_drawing()

if __name__ == "__main__":
    PenguinAI_CS2().run()
