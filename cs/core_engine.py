import os
import sys
import time

# Сразу пишем в файл, что скрипт хотя бы СТАРТОВАЛ
with open("debug_log.txt", "w") as f:
    f.write(f"[{time.ctime()}] Script started...\n")

try:
    import pyMeow as pmw
    import winsound
    with open("debug_log.txt", "a") as f: f.write("Libraries imported successfully.\n")
except Exception as e:
    with open("debug_log.txt", "a") as f: f.write(f"IMPORT ERROR: {e}\n")
    sys.exit()

class DiagnosticOverlay:
    def __init__(self):
        try:
            # Пытаемся создать оверлей БЕЗ привязки к игре (на весь экран)
            self.overlay = pmw.overlay_init() 
            self.width = 1920
            self.height = 1080
            self.menu_open = True
            
            with open("debug_log.txt", "a") as f: f.write("Overlay initialized successfully.\n")
            # Издаем звук при старте
            winsound.Beep(1000, 500)
        except Exception as e:
            with open("debug_log.txt", "a") as f: f.write(f"OVERLAY ERROR: {e}\n")

    def run(self):
        with open("debug_log.txt", "a") as f: f.write("Entering main loop...\n")
        
        # Цикл на 10 секунд, чтобы мы успели что-то увидеть
        start_time = time.time()
        while time.time() - start_time < 10:
            if pmw.overlay_loop():
                pmw.begin_drawing()
                
                # Рисуем огромный зеленый текст в центре
                pmw.draw_text("PENGUIN AI: DEBUG MODE", 500, 500, 40, pmw.get_color("#00DF64"))
                pmw.draw_rectangle_lines(100, 100, 500, 500, pmw.get_color("white"), 5)
                
                pmw.end_drawing()
            else:
                break
        
        with open("debug_log.txt", "a") as f: f.write("Loop finished or interrupted.\n")

if __name__ == "__main__":
    diag = DiagnosticOverlay()
    diag.run()
