from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from screens.camera_preview import show_camera_frame
from screens.common import create_button


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
        show_camera_frame(self.camera_label, frame)
