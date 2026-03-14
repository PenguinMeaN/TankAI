import sys
import cv2
import mss
import numpy as np
import time
import json
import os
import keyboard  # Библиотека для отслеживания клавиш
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

CONFIG_FILE = "config.json"

def save_config(area):
    with open(CONFIG_FILE, "w") as f:
        json.dump(area, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"top": 700, "left": 1500, "width": 300, "height": 300}

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.area = load_config()
        self.is_calibrating = False
        self.drag_pos = QPoint()
        self.resize_mode = False
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.update_geometry()
        
        self.sct = mss.mss()
        self.lost_tanks = {} 
        self.last_seen_tanks = []
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_logic)
        self.timer.start(30)
        self.show()

    def update_geometry(self):
        self.setGeometry(self.area["left"], self.area["top"], self.area["width"], self.area["height"])

    def set_mode(self, calibrating):
        self.is_calibrating = calibrating
        if calibrating:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowTransparentForInput)
        self.show()

    def get_red_mask(self, img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_red1 = np.array([0, 150, 150])
        upper_red1 = np.array([10, 255, 255])
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        lower_red2 = np.array([165, 150, 150])
        upper_red2 = np.array([180, 255, 255])
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        return mask1 + mask2

    def update_logic(self):
        if self.is_calibrating: 
            self.update()
            return
        
        capture_area = {"top": self.y(), "left": self.x(), "width": self.width(), "height": self.height()}
        
        try:
            screenshot = np.array(self.sct.grab(capture_area))
            frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            mask = self.get_red_mask(frame)
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            raw_tanks = []
            for cnt in contours:
                if 15 < cv2.contourArea(cnt) < 300: 
                    x, y, w, h = cv2.boundingRect(cnt)
                    raw_tanks.append(np.array([x + w//2, y + h//2]))
            
            current_tanks = []
            if raw_tanks:
                used = [False] * len(raw_tanks)
                for i in range(len(raw_tanks)):
                    if not used[i]:
                        cluster = [raw_tanks[i]]
                        used[i] = True
                        for j in range(i + 1, len(raw_tanks)):
                            if not used[j] and np.linalg.norm(raw_tanks[i] - raw_tanks[j]) < 15:
                                cluster.append(raw_tanks[j])
                                used[j] = True
                        avg_pos = np.mean(cluster, axis=0)
                        current_tanks.append((int(avg_pos[0]), int(avg_pos[1])))
            
            now = time.time()
            for old_tank in self.last_seen_tanks:
                if not any(np.linalg.norm(np.array(old_tank) - np.array(new_tank)) < 20 for new_tank in current_tanks):
                    if 15 < old_tank[0] < self.width()-15 and 15 < old_tank[1] < self.height()-15:
                        if not any(np.linalg.norm(np.array(old_tank) - np.array(lp)) < 20 for lp in self.lost_tanks):
                            self.lost_tanks[old_tank] = now
            
            for new_tank in current_tanks:
                self.lost_tanks = {pos: t for pos, t in self.lost_tanks.items() 
                                  if np.linalg.norm(np.array(pos) - np.array(new_tank)) > 25}
            
            self.last_seen_tanks = current_tanks
            self.update()
        except: pass

    def paintEvent(self, event):
        painter = QPainter(self)
        now = time.time()
        
        if self.is_calibrating:
            painter.setPen(QPen(QColor(0, 255, 0, 255), 3))
            painter.setBrush(QColor(0, 255, 0, 30))
            painter.drawRect(0, 0, self.width()-1, self.height()-1)
            painter.drawText(10, 20, "КАЛИБРОВКА: ТЯНИ ЗА ЦЕНТР ИЛИ УГОЛ")
        else:
            painter.setFont(QFont('Arial', 9, QFont.Weight.Bold))
            for pos, lost_time in list(self.lost_tanks.items()):
                dt = now - lost_time
                if dt > 5:
                    del self.lost_tanks[pos]
                    continue
                alpha = int(200 * (1 - dt/5))
                radius = int(12 + (dt * 7))
                painter.setPen(QPen(QColor(255, 255, 255, alpha), 2))
                painter.setBrush(QColor(255, 50, 50, int(alpha/4)))
                painter.drawEllipse(pos[0] - radius, pos[1] - radius, radius * 2, radius * 2)
                painter.drawText(pos[0] - 15, pos[1] - radius - 5, "LOST %ds" % int(dt))

    def mousePressEvent(self, event):
        if self.is_calibrating:
            if event.position().x() > self.width() - 25 and event.position().y() > self.height() - 25:
                self.resize_mode = True
            else:
                self.resize_mode = False
                self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.is_calibrating and event.buttons() == Qt.MouseButton.LeftButton:
            if self.resize_mode:
                new_w = max(50, event.position().toPoint().x())
                new_h = max(50, event.position().toPoint().y())
                self.resize(new_w, new_h)
            else:
                new_pos = event.globalPosition().toPoint()
                diff = new_pos - self.drag_pos
                self.move(self.x() + diff.x(), self.y() + diff.y())
                self.drag_pos = new_pos

class ControlPanel(QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("AI Settings")
        self.setGeometry(20, 20, 220, 110)
        self.setStyleSheet("background-color: rgba(30, 30, 30, 220); border: 1px solid #555; border-radius: 5px;")
        
        layout = QVBoxLayout()
        label = QLabel("МЕНЮ НАСТРОЕК [INS]")
        label.setStyleSheet("color: white; font-weight: bold; border: none;")
        layout.addWidget(label)
        
        self.btn_calib = QPushButton("НАЧАТЬ КАЛИБРОВКУ")
        self.btn_calib.setStyleSheet("background-color: #444; color: white; padding: 5px;")
        self.btn_calib.clicked.connect(self.toggle_calibration)
        layout.addWidget(self.btn_calib)
        
        btn_exit = QPushButton("ВЫХОД")
        btn_exit.setStyleSheet("background-color: #622; color: white; padding: 5px;")
        btn_exit.clicked.connect(QApplication.instance().quit)
        layout.addWidget(btn_exit)
        self.setLayout(layout)

    def toggle_calibration(self):
        if not self.overlay.is_calibrating:
            self.overlay.set_mode(True)
            self.btn_calib.setText("СОХРАНИТЬ")
        else:
            area = {"top": self.overlay.y(), "left": self.overlay.x(), "width": self.overlay.width(), "height": self.overlay.height()}
            save_config(area)
            self.overlay.set_mode(False)
            self.btn_calib.setText("НАЧАТЬ КАЛИБРОВКУ")

def check_hotkey(panel):
    # Если нажата клавиша Insert - переключаем видимость панели
    if keyboard.is_pressed('insert'):
        if panel.isVisible():
            panel.hide()
        else:
            panel.show()
        time.sleep(0.2) # Защита от дребезга

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = Overlay()
    panel = ControlPanel(overlay)
    
    # Скрываем панель при старте
    panel.hide()
    
    # Таймер для проверки нажатия клавиши INS
    key_timer = QTimer()
    key_timer.timeout.connect(lambda: check_hotkey(panel))
    key_timer.start(100) # Проверяем каждые 100мс
    
    print("Скрипт запущен. Нажми 'INSERT' для вызова меню.")
    sys.exit(app.exec())
