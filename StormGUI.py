import sys
import json
import base64
import threading
import time

import numpy as np
import cv2

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsView,
    QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem,
    QGridLayout, QPushButton
)

import websocket

SERVER_URL = "ws://192.168.1.123:1909"
UI_SENDER  = "4"   # this laptop UI
ROBOT_SENDER = "3"
CAM_SENDER   = "3_cam"

# ---------------- Telemetry model ----------------
class Telemetry:
    def __init__(self):
        self.drive_fl = 0.0
        self.drive_fr = 0.0
        self.drive_bl = 0.0
        self.drive_br = 0.0
        self.intake_power = 0.0
        self.arm_base_pos = 0.0
        self.wrist_pos = 0.0
        self.claw_pos = 0.0
        self.climb_pos = 0.0
        self.arm_extend_power = 0.0
        self.voltage_device_on = False
        self.wheel_rpm_target = 0
        self.tube_ready = False

        self.frame = None   # latest camera frame as QImage

# ---------------- WebSocket client in background thread ----------------
class UIWebSocketClient:
    def __init__(self, telemetry: Telemetry, on_update_callback):
        self.telemetry = telemetry
        self.on_update_callback = on_update_callback
        self.ws = None
        self.thread = None
        self.stop_flag = False

    def start(self):
        def run():
            self.ws = websocket.WebSocketApp(
                SERVER_URL,
                on_message=self.on_message,
                on_open=self.on_open,
                on_close=self.on_close,
                on_error=self.on_error
            )
            self.ws.run_forever(ping_interval=10, ping_timeout=5)

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_flag = True
        try:
            if self.ws:
                self.ws.close()
        except:
            pass

    def on_open(self, ws):
        print("[UI] WebSocket connected")
        # Register this client as sender "4" so relay can route to it
        hello = {
            "sender": UI_SENDER,
            "destination": UI_SENDER,
            "data": json.dumps({"id": 99, "hello": True})
        }
        try:
            ws.send(json.dumps(hello))
        except Exception as e:
            print("[UI] hello send error:", e)

    def on_close(self, ws, code, reason):
        print(f"[UI] WebSocket closed: {code} {reason}")

    def on_error(self, ws, error):
        print(f"[UI] WebSocket error: {error}")

    def on_message(self, ws, message):
        try:
            outer = json.loads(message)
            sender = outer.get("sender", "")
            data = json.loads(outer.get("data", "{}"))
            msg_id = data.get("id")

            #print("[UI] Got message from", sender, "id", msg_id)

            # Camera frames
            if sender == CAM_SENDER and msg_id == 20:
                b64 = data.get("frame_b64")
                if b64:
                    jpg_bytes = base64.b64decode(b64)
                    arr = np.frombuffer(jpg_bytes, dtype=np.uint8)
                    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    if img is not None:
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        h, w, ch = img.shape
                        bytes_per_line = ch * w
                        qimg = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
                        self.telemetry.frame = qimg

            # Telemetry
            if sender == ROBOT_SENDER and msg_id == 30:
                self.telemetry.drive_fl = float(data.get("drive_fl", 0.0))
                self.telemetry.drive_fr = float(data.get("drive_fr", 0.0))
                self.telemetry.drive_bl = float(data.get("drive_bl", 0.0))
                self.telemetry.drive_br = float(data.get("drive_br", 0.0))
                self.telemetry.intake_power = float(data.get("intake_power", 0.0))
                self.telemetry.arm_base_pos = float(data.get("arm_base_pos", 0.0))
                self.telemetry.wrist_pos = float(data.get("wrist_pos", 0.0))
                self.telemetry.claw_pos = float(data.get("claw_pos", 0.0))
                self.telemetry.climb_pos = float(data.get("climb_pos", 0.0))
                self.telemetry.arm_extend_power = float(data.get("arm_extend_power", 0.0))
                self.telemetry.voltage_device_on = bool(data.get("voltage_device_on", False))
                self.telemetry.wheel_rpm_target = int(data.get("wheel_rpm_target", 0))
                self.telemetry.tube_ready = bool(data.get("tube_ready", False))

            self.on_update_callback()

        except Exception as e:
            print(f"[UI] on_message error: {e}")

# ---------------- Mecanum widget ----------------
class MecanumView(QGraphicsView):
    def __init__(self, telemetry: Telemetry, parent=None):
        super().__init__(parent)
        self.telemetry = telemetry
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setFixedSize(220, 220)
        self.robot_rect = QRectF(-50, -50, 100, 100)
        self._init_scene()

    def _init_scene(self):
        chassis = QGraphicsRectItem(self.robot_rect)
        chassis.setPen(QPen(Qt.white, 2))
        self.scene.addItem(chassis)
        self.scene.setSceneRect(-110, -110, 220, 220)

    def _wheel_color_and_arrow(self, speed):
        mag = min(1.0, abs(speed))
        if speed >= 0:
            color = QColor(0, int(255 * mag), 0)
        else:
            color = QColor(int(255 * mag), 0, 0)
        return color, mag

    def drawForeground(self, painter: QPainter, rect):
        painter.setRenderHint(QPainter.Antialiasing)
        r = self.robot_rect
        offset = 15
        positions = {
            "fl": QPointF(r.left(),  r.top()) + QPointF(offset, offset),
            "fr": QPointF(r.right(), r.top()) + QPointF(-offset, offset),
            "bl": QPointF(r.left(),  r.bottom()) + QPointF(offset, -offset),
            "br": QPointF(r.right(), r.bottom()) + QPointF(-offset, -offset),
        }

        speeds = {
            "fl": self.telemetry.drive_fl,
            "fr": self.telemetry.drive_fr,
            "bl": self.telemetry.drive_bl,
            "br": self.telemetry.drive_br,
        }

        for key, pos in positions.items():
            spd = speeds[key]
            color, mag = self._wheel_color_and_arrow(spd)

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(pos, 8, 8)

            painter.setPen(QPen(Qt.white, 2))
            length = 20 * mag
            if spd >= 0:
                end = QPointF(pos.x(), pos.y() - length)
            else:
                end = QPointF(pos.x(), pos.y() + length)
            painter.drawLine(pos, end)

# ---------------- Main window ----------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.telemetry = Telemetry()
        self.setWindowTitle("Robot UI")

        main_layout = QHBoxLayout(self)

        self.video_label = QLabel("Video")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 360)

        mid_layout = QVBoxLayout()
        self.mecanum_view = MecanumView(self.telemetry)

        status_layout = QGridLayout()
        self.lbl_intake = QLabel("Intake: 0.0")
        self.lbl_tube   = QLabel("Tube ready: False")
        self.lbl_arm    = QLabel("Arm base: 0.0  Wrist: 0.0  Claw: 0.0")
        self.lbl_climb  = QLabel("Climb pos: 0.0")
        self.lbl_volt   = QLabel("Voltage device: OFF")
        self.lbl_rpm    = QLabel("Wheel RPM target: 0")

        status_layout.addWidget(self.lbl_intake, 0, 0)
        status_layout.addWidget(self.lbl_tube,   0, 1)
        status_layout.addWidget(self.lbl_arm,    1, 0, 1, 2)
        status_layout.addWidget(self.lbl_climb,  2, 0)
        status_layout.addWidget(self.lbl_volt,   2, 1)
        status_layout.addWidget(self.lbl_rpm,    3, 0, 1, 2)

        mid_layout.addWidget(self.mecanum_view)
        mid_layout.addLayout(status_layout)

        right_layout = QVBoxLayout()
        self.btn_start_all = QPushButton("Start All (TODO)")
        self.btn_stop_all  = QPushButton("Stop All (TODO)")
        self.btn_start_all.setEnabled(False)
        self.btn_stop_all.setEnabled(False)
        right_layout.addWidget(self.btn_start_all)
        right_layout.addWidget(self.btn_stop_all)
        right_layout.addStretch()

        main_layout.addWidget(self.video_label, stretch=3)
        main_layout.addLayout(mid_layout, stretch=2)
        main_layout.addLayout(right_layout, stretch=1)

        self.ws_client = UIWebSocketClient(self.telemetry, self.request_update)
        self.ws_client.start()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_ui)
        self.timer.start(33)

    def request_update(self):
        pass

    def refresh_ui(self):
        if self.telemetry.frame is not None:
            pix = QPixmap.fromImage(self.telemetry.frame)
            self.video_label.setPixmap(pix.scaled(
                self.video_label.width(),
                self.video_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))

        self.lbl_intake.setText(f"Intake: {self.telemetry.intake_power:.2f}")
        self.lbl_tube.setText(f"Tube ready: {self.telemetry.tube_ready}")
        self.lbl_arm.setText(
            f"Arm base: {self.telemetry.arm_base_pos:.2f}  "
            f"Wrist: {self.telemetry.wrist_pos:.2f}  "
            f"Claw: {self.telemetry.claw_pos:.2f}"
        )
        self.lbl_climb.setText(f"Climb pos: {self.telemetry.climb_pos:.2f}")
        self.lbl_volt.setText(
            "Voltage device: ON" if self.telemetry.voltage_device_on else "Voltage device: OFF"
        )
        self.lbl_rpm.setText(f"Wheel RPM target: {self.telemetry.wheel_rpm_target}")

        self.mecanum_view.viewport().update()

    def closeEvent(self, event):
        self.ws_client.stop()
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
