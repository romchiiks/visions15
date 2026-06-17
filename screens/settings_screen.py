from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from screens.common import create_button


class SettingsScreen(QWidget):
    back_requested = Signal()
    save_requested = Signal()

    def __init__(self, buttons_config):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        nav = QHBoxLayout()
        self.settings_back_button = create_button(buttons_config, "settings_back_button")
        self.settings_save_button = create_button(buttons_config, "settings_save_button")
        self.settings_back_button.clicked.connect(self.back_requested.emit)
        self.settings_save_button.clicked.connect(self.save_requested.emit)
        nav.addWidget(self.settings_back_button)
        nav.addWidget(self.settings_save_button)
        nav.addStretch()

        api_key_row = QHBoxLayout()
        api_key_label = QLabel("Ключ")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Ключ")

        api_key_row.addWidget(api_key_label)
        api_key_row.addWidget(self.api_key_input, stretch=1)

        unload_time_row = QHBoxLayout()
        unload_time_label = QLabel("Часы выгрузки")
        self.first_unload_time_input = QLineEdit()
        self.second_unload_time_input = QLineEdit()
        self.first_unload_time_input.setPlaceholderText("ЧЧ:ММ")
        self.second_unload_time_input.setPlaceholderText("ЧЧ:ММ")
        self.first_unload_time_input.setMaxLength(5)
        self.second_unload_time_input.setMaxLength(5)

        unload_time_row.addWidget(unload_time_label)
        unload_time_row.addWidget(self.first_unload_time_input)
        unload_time_row.addWidget(self.second_unload_time_input)
        unload_time_row.addStretch()

        layout.addLayout(nav)
        layout.addLayout(api_key_row)
        layout.addLayout(unload_time_row)
        layout.addStretch()

    def api_key(self):
        return self.api_key_input.text()

    def unload_times(self):
        return [
            self.first_unload_time_input.text().strip(),
            self.second_unload_time_input.text().strip(),
        ]
