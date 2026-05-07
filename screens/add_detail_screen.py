from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from screens.common import create_button


class AddDetailScreen(QWidget):
    back_requested = Signal()
    add_detail_requested = Signal()

    def __init__(self, buttons_config):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        nav = QHBoxLayout()
        self.add_detail_back_button = create_button(buttons_config, "add_detail_back_button")
        self.add_detail_back_button.clicked.connect(self.back_requested.emit)
        nav.addWidget(self.add_detail_back_button)
        nav.addStretch()

        input_row = QHBoxLayout()
        self.detail_input = QLineEdit()
        self.detail_input.setPlaceholderText("Введите новый класс детали")

        self.detail_add_button = create_button(buttons_config, "detail_add_button")
        self.detail_add_button.clicked.connect(self.add_detail_requested.emit)

        input_row.addWidget(self.detail_input, stretch=1)
        input_row.addWidget(self.detail_add_button)

        self.details_table = QTableWidget(0, 2)
        self.details_table.setHorizontalHeaderLabels(["Деталь", "Артикул"])
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.details_table.verticalHeader().setVisible(False)

        layout.addLayout(nav)
        layout.addLayout(input_row)
        layout.addWidget(self.details_table)

    def detail_name(self):
        return self.detail_input.text().strip()

    def clear_detail_input(self):
        self.detail_input.clear()

    def show_details(self, details):
        self.details_table.setRowCount(len(details))
        for row, (detail, article) in enumerate(details.items()):
            detail_item = QTableWidgetItem(detail)
            article_item = QTableWidgetItem(str(article))
            detail_item.setFlags(detail_item.flags() & ~Qt.ItemIsEditable)
            article_item.setFlags(article_item.flags() & ~Qt.ItemIsEditable)
            self.details_table.setItem(row, 0, detail_item)
            self.details_table.setItem(row, 1, article_item)
