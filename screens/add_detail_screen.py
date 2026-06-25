from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from screens.common import create_button


class AddDetailScreen(QWidget):
    back_requested = Signal()
    add_detail_requested = Signal()
    edit_detail_requested = Signal(str)
    delete_detail_requested = Signal(str)

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
        self.detail_input.setPlaceholderText("Введите название детали")

        self.detail_add_button = create_button(buttons_config, "detail_add_button")
        self.detail_add_button.clicked.connect(self.add_detail_requested.emit)

        input_row.addWidget(self.detail_input, stretch=1)
        input_row.addWidget(self.detail_add_button)

        self.details_table = QTableWidget(0, 2)
        self.details_table.setHorizontalHeaderLabels(["Деталь", "Артикул"])
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.details_table.verticalHeader().setVisible(False)
        self.details_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.details_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.details_table.itemDoubleClicked.connect(self.fill_input_from_detail_item)
        self.details_table.customContextMenuRequested.connect(self.show_detail_context_menu)

        layout.addLayout(nav)
        layout.addLayout(input_row)
        layout.addWidget(self.details_table)

    def detail_name(self):
        return self.detail_input.text().strip()

    def clear_detail_input(self):
        self.detail_input.clear()

    def fill_input_from_detail_item(self, item):
        detail_name = self.detail_name_from_row(item.row())
        if detail_name:
            self.detail_input.setText(detail_name)
            self.detail_input.setFocus()

    def show_detail_context_menu(self, position):
        row = self.details_table.rowAt(position.y())
        detail_name = self.detail_name_from_row(row)
        if not detail_name:
            return

        self.details_table.selectRow(row)

        menu = QMenu(self)
        edit_action = QAction("Редактировать название", self)
        delete_action = QAction("Удалить", self)
        menu.addAction(edit_action)
        menu.addAction(delete_action)

        selected_action = menu.exec(self.details_table.viewport().mapToGlobal(position))
        if selected_action == edit_action:
            self.edit_detail_requested.emit(detail_name)
        elif selected_action == delete_action:
            self.delete_detail_requested.emit(detail_name)

    def detail_name_from_row(self, row):
        if row < 0:
            return None

        item = self.details_table.item(row, 0)
        if item is None:
            return None

        return item.text().strip()

    def show_details(self, details):
        self.details_table.setRowCount(len(details))
        for row, (detail, article) in enumerate(details.items()):
            detail_item = QTableWidgetItem(detail)
            article_item = QTableWidgetItem(str(article))
            detail_item.setFlags(detail_item.flags() & ~Qt.ItemIsEditable)
            article_item.setFlags(article_item.flags() & ~Qt.ItemIsEditable)
            self.details_table.setItem(row, 0, detail_item)
            self.details_table.setItem(row, 1, article_item)
