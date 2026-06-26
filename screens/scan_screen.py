from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from screens.common import create_button


class ScanScreen(QWidget):
    back_requested = Signal()
    scan_requested = Signal()
    show_image_requested = Signal()

    def __init__(self, buttons_config):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        nav = QHBoxLayout()
        self.scan_back_button = create_button(buttons_config, "scan_back_button")
        self.scan_action_button = create_button(buttons_config, "scan_action_button")
        self.show_image_button = create_button(buttons_config, "show_image_button")

        self.scan_back_button.clicked.connect(self.back_requested.emit)
        self.scan_action_button.clicked.connect(self.scan_requested.emit)
        self.show_image_button.clicked.connect(self.show_image_requested.emit)

        nav.addWidget(self.scan_back_button)
        nav.addWidget(self.scan_action_button)
        nav.addWidget(self.show_image_button)
        nav.addStretch()

        title = QLabel("Результат сканирования")
        title.setObjectName("title")

        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Наименование", "Количество", "Артикул"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.verticalHeader().setVisible(False)

        layout.addLayout(nav)
        layout.addWidget(title)
        layout.addWidget(self.results_table)

    def show_scan_result(self):
        self.results_table.setRowCount(1)
        for column in range(3):
            item = QTableWidgetItem("null")
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.results_table.setItem(0, column, item)

    def clear_scan_result(self):
        self.results_table.setRowCount(0)
