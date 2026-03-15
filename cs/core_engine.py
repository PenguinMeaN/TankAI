import sys
import pymem
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor

class ESPOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- МАГИЯ ОВЕРЛЕЯ ---
        # Делаем окно прозрачным, без рамок, поверх всех окон и чтобы мышка проходила СКВОЗЬ него
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Растягиваем наше невидимое окно на весь экран
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # Подключаемся к игре (пока просто проверяем, запущена ли она)
        try:
            self.pm = pymem.Pymem("cs2.exe")
            print("[PenguinAI] Hooked to CS2!")
        except:
            print("[PenguinAI] Waiting for CS2...")

        # Таймер обновления экрана (60 FPS = 16 мс)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update) # Эта команда заставляет окно перерисовываться
        self.timer.start(16)

    def paintEvent(self, event):
        # Эта функция вызывается 60 раз в секунду и рисует нашу графику
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing) # Сглаживание
        
        # Берем "кисть" красного цвета, толщиной 2 пикселя
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)
        
        # Узнаем центр экрана
        w = self.width()
        h = self.height()
        cx, cy = w // 2, h // 2
        
        # Рисуем крест (Линия горизонтальная, линия вертикальная)
        painter.drawLine(cx - 15, cy, cx + 15, cy)
        painter.drawLine(cx, cy - 15, cx, cy + 15)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = ESPOverlay()
    overlay.show()
    sys.exit(app.exec())
