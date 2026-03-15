import sys
import ctypes
import pymem
import requests
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QFont

user32 = ctypes.windll.user32

# Константы клавиш
VK_INSERT = 0x2D
VK_F12 = 0x7B
VK_UP = 0x26
VK_DOWN = 0x28
VK_RIGHT = 0x27
VK_LEFT = 0x25

# --- ПОЛУЧЕНИЕ ОФФСЕТОВ ---
try:
    print("[PenguinAI] Fetching latest offsets...")
    off = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json").json()
    dll = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json").json()
    
    dwEntityList = off['client_dll']['dwEntityList']
    dwLocalPlayerPawn = off['client_dll']['dwLocalPlayerPawn']
    dwViewMatrix = off['client_dll']['dwViewMatrix']
    
    m_iTeamNum = dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
    m_iHealth = dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
    m_vOldOrigin = dll['client.dll']['classes']['C_BasePlayerPawn']['fields']['m_vOldOrigin']
    print("[PenguinAI] Offsets loaded successfully!")
except Exception as e:
    print(f"[ERROR] Failed to load offsets: {e}")

def world_to_screen(matrix, px, py, pz, width, height):
    # Математика проекции 3D в 2D (Исправленная)
    w = matrix[12] * px + matrix[13] * py + matrix[14] * pz + matrix[15]
    if w < 0.01: return None
    
    x = (matrix[0] * px + matrix[1] * py + matrix[2] * pz + matrix[3]) / w
    y = (matrix[4] * px + matrix[5] * py + matrix[6] * pz + matrix[7]) / w
    
    sx = (width / 2) + (x * width / 2)
    sy = (height / 2) - (y * height / 2)
    return int(sx), int(sy)

class ESPOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        screen_rect = QApplication.primaryScreen().geometry()
        self.sw = screen_rect.width()
        self.sh = screen_rect.height()
        self.setGeometry(screen_rect)

        self.show_menu = False
        self.features = {
            "Crosshair": True,
            "ESP Box": False
        }
        self.menu_keys = list(self.features.keys())
        self.selected_index = 0
        
        self.enemy_boxes = []

        self.ins_pressed = False
        self.f12_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.right_pressed = False

        self.pm = None
        self.client = None
        self.hook_game()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_state)
        self.timer.start(16)
        
        print("[PenguinAI] Module Loaded. Press INS for Menu, F12 to Exit.")

    def hook_game(self):
        try:
            self.pm = pymem.Pymem("cs2.exe")
            self.client = pymem.process.module_from_name(self.pm.process_handle, "client.dll").lpBaseOfDll
            print("[PenguinAI] Hooked to CS2 memory!")
        except:
            self.pm = None

    def update_state(self):
        # 1. ОБРАБОТКА МЕНЮ
        if user32.GetAsyncKeyState(VK_INSERT) & 0x8000:
            if not self.ins_pressed:
                self.show_menu = not self.show_menu
                self.ins_pressed = True
        else: self.ins_pressed = False

        if user32.GetAsyncKeyState(VK_F12) & 0x8000:
            if not self.f12_pressed:
                print("[PenguinAI] Unloading module...")
                QApplication.quit()
        
        if self.show_menu:
            if user32.GetAsyncKeyState(VK_UP) & 0x8000:
                if not self.up_pressed:
                    self.selected_index = (self.selected_index - 1) % len(self.menu_keys)
                    self.up_pressed = True
            else: self.up_pressed = False

            if user32.GetAsyncKeyState(VK_DOWN) & 0x8000:
                if not self.down_pressed:
                    self.selected_index = (self.selected_index + 1) % len(self.menu_keys)
                    self.down_pressed = True
            else: self.down_pressed = False

            right_state = (user32.GetAsyncKeyState(VK_RIGHT) & 0x8000) or (user32.GetAsyncKeyState(VK_LEFT) & 0x8000)
            if right_state:
                if not self.right_pressed:
                    key = self.menu_keys[self.selected_index]
                    self.features[key] = not self.features[key]
                    self.right_pressed = True
            else: self.right_pressed = False

        # 2. ESP ЛОГИКА
        self.enemy_boxes.clear()
        
        if self.features["ESP Box"] and not self.pm:
            self.hook_game()

        if self.features["ESP Box"] and self.pm:
            try:
                vm = [self.pm.read_float(self.client + dwViewMatrix + (i * 4)) for i in range(16)]
                lp = self.pm.read_longlong(self.client + dwLocalPlayerPawn)
                lt = self.pm.read_int(lp + m_iTeamNum)
                el = self.pm.read_longlong(self.client + dwEntityList)

                for i in range(1, 64):
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
                            # ИСПРАВЛЕНИЕ: Читаем 3 координаты отдельно, так как read_vec3 не существует
                            pos_x = self.pm.read_float(pawn + m_vOldOrigin)
                            pos_y = self.pm.read_float(pawn + m_vOldOrigin + 4)
                            pos_z = self.pm.read_float(pawn + m_vOldOrigin + 8)
                            
                            screen = world_to_screen(vm, pos_x, pos_y, pos_z, self.sw, self.sh)
                            
                            if screen:
                                self.enemy_boxes.append((screen[0], screen[1], 35, 70))
            except Exception as e:
                print(f"[ERROR ESP] {e}") # Теперь мы увидим ошибку, если она будет!
                self.pm = None

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.features["ESP Box"]:
            painter.setPen(QPen(QColor("#00DF64"), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            for x, y, w, h in self.enemy_boxes:
                painter.drawRect(x - (w//2), y - h, w, h)

        if self.features["Crosshair"]:
            cx, cy = self.sw // 2, self.sh // 2
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#00DF64"))
            painter.drawEllipse(cx - 3, cy - 3, 6, 6)

        if self.show_menu:
            menu_x, menu_y = 50, 50 
            
            painter.setPen(QPen(QColor("#22262E"), 2))
            painter.setBrush(QColor(13, 14, 17, 240))
            painter.drawRoundedRect(menu_x, menu_y, 220, 120, 10, 10)
            
            painter.setPen(QColor("#00DF64"))
            painter.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
            painter.drawText(menu_x + 15, menu_y + 25, "PenguinAI: CS2")
            painter.drawLine(menu_x + 10, menu_y + 35, menu_x + 210, menu_y + 35)

            painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
            y_offset = 60
            for i, key in enumerate(self.menu_keys):
                if i == self.selected_index:
                    painter.setPen(QColor("#00DF64"))
                    prefix = "> "
                else:
                    painter.setPen(QColor("#E2E8F0"))
                    prefix = "  "
                
                state = "[ON]" if self.features[key] else "[OFF]"
                painter.drawText(menu_x + 15, menu_y + y_offset, f"{prefix}{key}")
                painter.drawText(menu_x + 160, menu_y + y_offset, state)
                y_offset += 25

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = ESPOverlay()
    overlay.show()
    sys.exit(app.exec())
