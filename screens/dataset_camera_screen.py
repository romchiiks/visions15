from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from screens.camera_preview import show_camera_frame
from screens.common import create_button


class DatasetCameraScreen(QWidget):
    back_requested = Signal()
    snapshot_requested = Signal()
    record_requested = Signal()
    save_requested = Signal()

    def __init__(self, buttons_config):
        super().__init__()
        self.buttons_config = buttons_config

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        nav = QHBoxLayout()
        self.dataset_camera_back_button = create_button(buttons_config, "dataset_camera_back_button")
        self.dataset_camera_back_button.clicked.connect(self.back_requested.emit)
        nav.addWidget(self.dataset_camera_back_button)
        nav.addStretch()

        self.camera_title = QLabel("Новый класс детали")
        self.camera_title.setObjectName("title")
        self.images_count_label = QLabel("Фотографий: 0")

        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumHeight(320)
        self.camera_label.setText("Камера не запущена")

        actions = QHBoxLayout()
        self.snapshot_button = create_button(buttons_config, "dataset_snapshot_button")
        self.record_button = create_button(buttons_config, "dataset_record_button")
        self.save_button = create_button(buttons_config, "dataset_save_button")
        self.snapshot_button.clicked.connect(self.snapshot_requested.emit)
        self.record_button.clicked.connect(self.record_requested.emit)
        self.save_button.clicked.connect(self.save_requested.emit)
        actions.addWidget(self.snapshot_button)
        actions.addWidget(self.record_button)
        actions.addWidget(self.save_button)
        actions.addStretch()

        title_row = QHBoxLayout()
        title_row.addWidget(self.camera_title)
        title_row.addWidget(self.images_count_label)
        title_row.addStretch()

        layout.addLayout(nav)
        layout.addLayout(title_row)
        layout.addWidget(self.camera_label, stretch=1)
        layout.addLayout(actions)

    def set_class_name(self, class_name):
        self.camera_title.setText(f"Класс детали: {class_name}")

    def set_recording(self, is_recording):
        if is_recording:
            self.record_button.setText("Остановить запись")
            return

        self.record_button.setText(self.buttons_config["dataset_record_button"]["button_text"])

    def set_images_count(self, images_count):
        self.images_count_label.setText(f"Фотографий: {images_count}")

    def show_message(self, text):
        self.camera_label.setPixmap(QPixmap())
        self.camera_label.setText(text)

    def show_frame(self, frame, marker_rectangle=None):
        show_camera_frame(self.camera_label, frame, marker_rectangle=marker_rectangle)
