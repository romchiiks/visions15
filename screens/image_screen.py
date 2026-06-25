from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from screens.common import create_button


class ImageScreen(QWidget):
    back_requested = Signal()

    def __init__(self, buttons_config):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        nav = QHBoxLayout()
        self.image_back_button = create_button(buttons_config, "image_back_button")
        self.image_back_button.clicked.connect(self.back_requested.emit)
        nav.addWidget(self.image_back_button)
        nav.addStretch()

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(360)
        self.image_label.setText("Изображение не найдено")

        layout.addLayout(nav)
        layout.addWidget(self.image_label, stretch=1)

    def show_image(self, image_path):
        if image_path is None:
            self.show_not_found()
            return

        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self.show_not_found()
            return

        self.image_label.setText("")
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.FastTransformation,
        )
        self.image_label.setPixmap(scaled_pixmap)

    def show_not_found(self):
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText("Изображение не найдено")
