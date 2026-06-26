from collections import Counter

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

    def show_scan_result(self, predictions, details):
        counts = Counter(prediction.category_name for prediction in predictions)

        if not counts:
            self.results_table.setRowCount(1)
            self.set_result_row(0, "Не найдено", "0", "")
            return

        self.results_table.setRowCount(len(counts))
        for row, (category_name, count) in enumerate(sorted(counts.items())):
            self.set_result_row(row, category_name, str(count), str(details.get(category_name, "")))

    def clear_scan_result(self):
        self.results_table.setRowCount(0)

    def set_result_row(self, row, name, count, article):
        for column, value in enumerate((name, count, article)):
            item = QTableWidgetItem(value)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.results_table.setItem(row, column, item)
