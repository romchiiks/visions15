from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
import cv2

from screens.common import create_button


PREVIEW_WIDTH = 1280
PREVIEW_HEIGHT = 720


class SettingsCameraScreen(QWidget):
    back_requested = Signal()

    def __init__(self, buttons_config):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        nav = QHBoxLayout()
        self.settings_camera_back_button = create_button(buttons_config, "settings_camera_back_button")
        self.settings_camera_back_button.clicked.connect(self.back_requested.emit)
        nav.addWidget(self.settings_camera_back_button)
        nav.addStretch()

        title = QLabel("Вывод с камеры")
        title.setObjectName("title")

        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumHeight(320)
        self.camera_label.setText("Камера не запущена")

        layout.addLayout(nav)
        layout.addWidget(title)
        layout.addWidget(self.camera_label, stretch=1)

    def show_message(self, text):
        self.camera_label.setPixmap(QPixmap())
        self.camera_label.setText(text)

    def show_frame(self, frame):
        preview_frame = self.create_preview_frame(frame)
        rgb_frame = cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb_frame.shape
        bytes_per_line = channels * width
        image = QImage(
            rgb_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888,
        ).copy()

        self.camera_label.setText("")
        pixmap = QPixmap.fromImage(image)
        self.camera_label.setPixmap(
            pixmap.scaled(
                self.camera_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def create_preview_frame(self, frame):
        height, width = frame.shape[:2]
        scale = min(PREVIEW_WIDTH / width, PREVIEW_HEIGHT / height, 1)
        if scale == 1:
            return frame

        preview_width = max(1, int(width * scale))
        preview_height = max(1, int(height * scale))
        return cv2.resize(
            frame,
            (preview_width, preview_height),
            interpolation=cv2.INTER_AREA,
        )
