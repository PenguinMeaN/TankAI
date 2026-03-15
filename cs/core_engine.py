import pyMeow as pmw
import time
import winsound # Для звукового теста
import sys

class PenguinTestOverlay:
    def __init__(self):
        try:
            # Пытаемся прицепиться к рабочему столу для теста, если игры нет
            # Если игра есть, он прицепится к ней
            self.overlay = pmw.overlay_init(target="Counter-Strike 2", fps=144)
            self.width = pmw.get_window_width("Counter-Strike 2")
            self.height = pmw.get_window_height("Counter-Strike 2")
            
            self.menu_open = True
            self.wh_status = False
            self.aim_status = False
            
            print(f"[PenguinAI: Debug] Overlay created: {self.width}x{self.height}")
            print("[SYSTEM] If you see a black square and it vanishes - Windows blocks transparency.")
        except:
            # Если CS2 не найдена, создаем оверлей на весь экран (тестовый режим)
            self.overlay = pmw.overlay_init() 
            self.width = 1920
            self.height = 1080
            print("[PenguinAI: Debug] CS2 not found. Running in FULLSCREEN TEST MODE.")

    def draw_ui(self):
        if not self.menu_open: return

        # Наше овальное матовое меню
        # Фон
        pmw.draw_rectangle(50, 50, 250, 300, pmw.get_color("#0D0E11"))
        # Неоновая рамка
        pmw.draw_rectangle_lines(50, 50, 250, 300, pmw.get_color("#00DF64"), 2)
        
        # Заголовок
        pmw.draw_text("PenguinAI: HUB", 75, 75, 20, pmw.get_color("#00DF64"))
        pmw.draw_line(65, 110, 285, 110, pmw.get_color("#22262E"), 1)

        # Кнопки-индикаторы
        self.draw_indicator("Visuals WH", 140, self.wh_status)
        self.draw_indicator("Aimbot Root", 180, self.aim_status)
        self.draw_indicator("Trigger Bot", 220, False)
        
        pmw.draw_text("Status: Running...", 75, 280, 12, pmw.get_color("#444"))
        pmw.draw_text("Press [INS] to Toggle", 75, 310, 10, pmw.get_color("#00DF64"))

    def draw_indicator(self, text, y, state):
        color = "#00DF64" if state else "#333"
        pmw.draw_circle(75, y + 10, 6, pmw.get_color(color))
        pmw.draw_text(text, 100, y, 15, pmw.get_color("white"))

    def run(self):
        print("[!] Press INSERT to test Sound and Menu visibility.")
        
        while pmw.overlay_loop():
            # Тест кнопки INSERT (0x2D)
            if pmw.key_pressed(0x2D):
                self.menu_open = not self.menu_open
                # ПИЩИМ ПРИ НАЖАТИИ (Частота 800Гц, длительность 100мс)
                winsound.Beep(800, 100) 
                print(f"[DEBUG] INSERT Pressed. Menu Visible: {self.menu_open}")
                time.sleep(0.3)

            pmw.begin_drawing()
            
            # РИСУЕМ ТЕСТОВЫЙ КВАДРАТ В ЦЕНТРЕ ЭКРАНА
            pmw.draw_rectangle_lines(self.width//2 - 50, self.height//2 - 50, 100, 100, pmw.get_color("#00DF64"), 2)
            pmw.draw_text("PENGUIN OVERLAY TEST", self.width//2 - 70, self.height//2 + 60, 12, pmw.get_color("white"))
            
            self.draw_ui()
            
            pmw.end_drawing()

if __name__ == "__main__":
    test = PenguinTestOverlay()
    test.run()
