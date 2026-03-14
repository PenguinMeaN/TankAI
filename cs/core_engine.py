import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor

class CrosshairOverlay(QWidget):
    def __init__(self):
        super().__init__()
        # Делаем окно прозрачным, без рамок и поверх всех окон
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.showFullScreen()

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(QColor(255, 0, 0)) # Красный цвет
        pen.setWidth(6) # Размер точки
        painter.setPen(pen)
        
        # Находим центр экрана
        x = self.width() // 2
        y = self.height() // 2
        
        # Рисуем точку
        painter.drawPoint(x, y)

if __name__ == '__main__':
    print("[Crossfire Module] Starting transparent crosshair overlay...")
    print("Press CTRL+C in this console to close the crosshair.")
    app = QApplication(sys.argv)
    overlay = CrosshairOverlay()
    sys.exit(app.exec())
