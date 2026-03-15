import pymem, requests, ctypes, time

# GDI инициализация
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
hdc = user32.GetDC(0)
RED_PEN = gdi32.CreatePen(0, 3, 0x0000FF) # Красный для теста
GREEN_PEN = gdi32.CreatePen(0, 2, 0x00DF64) # Зеленый наш

def draw_test_cross(hdc, sw, sh):
    # Рисует крест в центре экрана для проверки
    gdi32.SelectObject(hdc, RED_PEN)
    gdi32.MoveToEx(hdc, sw//2 - 20, sh//2, None); gdi32.LineTo(hdc, sw//2 + 20, sh//2)
    gdi32.MoveToEx(hdc, sw//2, sh//2 - 20, None); gdi32.LineTo(hdc, sw//2, sh//2 + 20)

print("[DEBUG] WH Started. Looking for CS2...")

try:
    pm = pymem.Pymem("cs2.exe")
    sw = user32.GetSystemMetrics(0); sh = user32.GetSystemMetrics(1)
    print(f"[DEBUG] Connected! Resolution: {sw}x{sh}")
    
    while True:
        # 1. Постоянно рисуем тестовый крест, чтобы видеть, что скрипт ЖИВ
        draw_test_cross(hdc, sw, sh)
        
        # 2. Тут будет логика WH (пока просто спим, чтобы не вешать систему)
        time.sleep(0.01)
except Exception as e:
    print(f"[ERROR] {e}")
    time.sleep(5)
