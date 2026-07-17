from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from screens.common import create_button


class ScanScreen(QWidget):
    back_requested = Signal()
    scan_requested = Signal()

    def __init__(self, buttons_config):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        nav = QHBoxLayout()
        self.scan_back_button = create_button(buttons_config, "scan_back_button")
        self.scan_action_button = create_button(buttons_config, "scan_action_button")

        self.scan_back_button.clicked.connect(self.back_requested.emit)
        self.scan_action_button.clicked.connect(self.scan_requested.emit)

        nav.addWidget(self.scan_back_button)
        nav.addWidget(self.scan_action_button)
        nav.addStretch()

        self.results_table = QTableWidget(0, 2)
        self.results_table.setHorizontalHeaderLabels(["Деталь", "Артикул"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.verticalHeader().setVisible(False)

        layout.addLayout(nav)
        layout.addWidget(self.results_table)

    def show_scan_results(self, details):
        self.results_table.setRowCount(len(details))
        for row, (detail, article) in enumerate(details.items()):
            detail_item = QTableWidgetItem(str(detail))
            article_item = QTableWidgetItem(str(article))
            detail_item.setFlags(detail_item.flags() & ~Qt.ItemIsEditable)
            article_item.setFlags(article_item.flags() & ~Qt.ItemIsEditable)
            self.results_table.setItem(row, 0, detail_item)
            self.results_table.setItem(row, 1, article_item)
