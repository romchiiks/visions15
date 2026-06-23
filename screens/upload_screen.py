from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from screens.common import create_button


class UploadScreen(QWidget):
    back_requested = Signal()
    upload_requested = Signal()

    def __init__(self, buttons_config):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        nav = QHBoxLayout()
        self.upload_back_button = create_button(buttons_config, "upload_back_button")
        self.upload_back_button.clicked.connect(self.back_requested.emit)
        self.upload_action_button = create_button(buttons_config, "upload_action_button")
        self.upload_action_button.clicked.connect(self.upload_requested.emit)
        nav.addWidget(self.upload_back_button)
        nav.addWidget(self.upload_action_button)
        nav.addStretch()

        self.classes_table = QTableWidget(0, 4)
        self.classes_table.setHorizontalHeaderLabels(
            ["Выбор", "Класс", "Артикул", "Кол-во изобр."]
        )
        self.classes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.classes_table.verticalHeader().setVisible(False)

        layout.addLayout(nav)
        layout.addWidget(self.classes_table)

    def show_classes(self, classes, details):
        self.classes_table.setRowCount(len(classes))
        for row, (class_name, class_data) in enumerate(classes.items()):
            images_count = class_data.get("images_count", 0)
            article = details.get(class_name, "")

            select_item = QTableWidgetItem()
            select_item.setFlags(
                Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
            )
            select_item.setCheckState(Qt.Unchecked)

            class_item = QTableWidgetItem(str(class_name))
            article_item = QTableWidgetItem(str(article))
            images_count_item = QTableWidgetItem(str(images_count))

            class_item.setFlags(class_item.flags() & ~Qt.ItemIsEditable)
            article_item.setFlags(article_item.flags() & ~Qt.ItemIsEditable)
            images_count_item.setFlags(images_count_item.flags() & ~Qt.ItemIsEditable)

            self.classes_table.setItem(row, 0, select_item)
            self.classes_table.setItem(row, 1, class_item)
            self.classes_table.setItem(row, 2, article_item)
            self.classes_table.setItem(row, 3, images_count_item)

    def selected_classes(self):
        selected = []
        for row in range(self.classes_table.rowCount()):
            select_item = self.classes_table.item(row, 0)
            class_item = self.classes_table.item(row, 1)
            if (
                select_item is not None
                and class_item is not None
                and select_item.checkState() == Qt.Checked
            ):
                selected.append(class_item.text())

        return selected
