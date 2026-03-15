import sys
import ctypes
import pymem
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QFont

user32 = ctypes.windll.user32

# Константы клавиш Windows (WinAPI)
VK_INSERT = 0x2D
VK_F12 = 0x7B
VK_UP = 0x26
VK_DOWN = 0x28
VK_RIGHT = 0x27
VK_LEFT = 0x25

class ESPOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- НАСТРОЙКИ ОВЕРЛЕЯ ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(QApplication.primaryScreen().geometry())

        # --- ЛОГИКА МЕНЮ ---
        self.show_menu = False
        self.features = {
            "Crosshair": True,
            "ESP Box (Скоро)": False
        }
        self.menu_keys = list(self.features.keys())
        self.selected_index = 0

        # Анти-спам кнопок
        self.ins_pressed = False
        self.f12_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.right_pressed = False

        # Таймер (60 кадров в секунду)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_state)
        self.timer.start(16)
        
        print("[PenguinAI] Module Loaded. Press INS for Menu, F12 to Exit.")

    def update_state(self):
        # 1. Проверка клавиш в фоне (Глобальные хоткеи)
        
        # Кнопка INS (Открыть/Закрыть меню)
        ins_state = user32.GetAsyncKeyState(VK_INSERT) & 0x8000
        if ins_state and not self.ins_pressed:
            self.show_menu = not self.show_menu
            self.ins_pressed = True
        elif not ins_state:
            self.ins_pressed = False

        # Кнопка F12 (Выгрузка чита)
        f12_state = user32.GetAsyncKeyState(VK_F12) & 0x8000
        if f12_state and not self.f12_pressed:
            print("[PenguinAI] Unloading module...")
            QApplication.quit()
        
        # 2. Навигация по меню (Работает только если меню открыто)
        if self.show_menu:
            up_state = user32.GetAsyncKeyState(VK_UP) & 0x8000
            if up_state and not self.up_pressed:
                self.selected_index = (self.selected_index - 1) % len(self.menu_keys)
                self.up_pressed = True
            elif not up_state:
                self.up_pressed = False

            down_state = user32.GetAsyncKeyState(VK_DOWN) & 0x8000
            if down_state and not self.down_pressed:
                self.selected_index = (self.selected_index + 1) % len(self.menu_keys)
                self.down_pressed = True
            elif not down_state:
                self.down_pressed = False

            # Включение/Выключение функций на Вправо/Влево
            right_state = (user32.GetAsyncKeyState(VK_RIGHT) & 0x8000) or (user32.GetAsyncKeyState(VK_LEFT) & 0x8000)
            if right_state and not self.right_pressed:
                key = self.menu_keys[self.selected_index]
                self.features[key] = not self.features[key] # Меняем True на False и наоборот
                self.right_pressed = True
            elif not right_state:
                self.right_pressed = False

        # Перерисовываем экран
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        cx, cy = w // 2, h // 2

        # --- РИСУЕМ ТОЧКУ (CROSSHAIR) ---
        if self.features["Crosshair"]:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#00DF64")) # Наш фирменный неоновый зеленый
            painter.drawEllipse(cx - 3, cy - 3, 6, 6) # Точка 6x6 пикселей

        # --- РИСУЕМ МЕНЮ ---
        if self.show_menu:
            menu_x, menu_y = 50, 50 # Позиция меню в левом верхнем углу
            
            # Фон меню
            painter.setPen(QPen(QColor("#22262E"), 2))
            painter.setBrush(QColor(13, 14, 17, 240)) # Матовый черный
            painter.drawRoundedRect(menu_x, menu_y, 220, 120, 10, 10)
            
            # Заголовок
            painter.setPen(QColor("#00DF64"))
            painter.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
            painter.drawText(menu_x + 15, menu_y + 25, "PenguinAI: CS2")
            painter.drawLine(menu_x + 10, menu_y + 35, menu_x + 210, menu_y + 35)

            # Пункты меню
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
                
                # Рисуем статус справа
                painter.drawText(menu_x + 160, menu_y + y_offset, state)
                y_offset += 25

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = ESPOverlay()
    overlay.show()
    sys.exit(app.exec())
