from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from screens.common import create_button


class HomeScreen(QWidget):
    scan_requested = Signal()
    add_detail_requested = Signal()

    def __init__(self, buttons_config):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        self.scan_button = create_button(buttons_config, "scan_button")
        self.add_detail_button = create_button(buttons_config, "add_detail_button")

        self.scan_button.clicked.connect(self.scan_requested.emit)
        self.add_detail_button.clicked.connect(self.add_detail_requested.emit)

        layout.addWidget(self.scan_button)
        layout.addWidget(self.add_detail_button)
