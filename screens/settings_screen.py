from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from screens.common import create_button


class SettingsScreen(QWidget):
    back_requested = Signal()
    save_requested = Signal()
    check_connection_requested = Signal()
    camera_output_requested = Signal()

    def __init__(self, buttons_config):
        super().__init__()

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
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

        server_group = QGroupBox("Сервер")
        server_layout = QVBoxLayout(server_group)

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

        server_layout.addLayout(api_key_row)
        server_layout.addLayout(unload_time_row)

        server_actions = QHBoxLayout()
        self.settings_check_connection_button = create_button(buttons_config, "settings_check_connection_button")
        self.settings_check_connection_button.clicked.connect(self.check_connection_requested.emit)
        server_actions.addWidget(self.settings_check_connection_button)
        server_actions.addStretch()
        server_layout.addLayout(server_actions)

        camera_group = QGroupBox("Камера")
        camera_layout = QGridLayout(camera_group)
        self.camera_height_input = QLineEdit()
        self.camera_width_input = QLineEdit()
        self.camera_fps_input = QLineEdit()
        self.camera_device_index_input = QLineEdit()
        positive_int_validator = QIntValidator(1, 99999, self)
        device_index_validator = QIntValidator(0, 99999, self)
        self.camera_height_input.setValidator(positive_int_validator)
        self.camera_width_input.setValidator(positive_int_validator)
        self.camera_fps_input.setValidator(positive_int_validator)
        self.camera_device_index_input.setValidator(device_index_validator)

        camera_layout.addWidget(QLabel("Высота"), 0, 0)
        camera_layout.addWidget(self.camera_height_input, 0, 1)
        camera_layout.addWidget(QLabel("Ширина"), 1, 0)
        camera_layout.addWidget(self.camera_width_input, 1, 1)
        camera_layout.addWidget(QLabel("FPS"), 2, 0)
        camera_layout.addWidget(self.camera_fps_input, 2, 1)
        camera_layout.addWidget(QLabel("Индекс устройства"), 3, 0)
        camera_layout.addWidget(self.camera_device_index_input, 3, 1)

        camera_actions = QHBoxLayout()
        self.settings_camera_button = create_button(buttons_config, "settings_camera_button")
        self.settings_camera_button.clicked.connect(self.camera_output_requested.emit)
        camera_actions.addWidget(self.settings_camera_button)
        camera_actions.addStretch()
        camera_layout.addLayout(camera_actions, 4, 0, 1, 2)

        layout.addLayout(nav)
        layout.addWidget(server_group)
        layout.addWidget(camera_group)
        layout.addStretch()

        scroll_area.setWidget(content)
        outer_layout.addWidget(scroll_area)

    def api_key(self):
        return self.api_key_input.text()

    def unload_times(self):
        return [
            self.first_unload_time_input.text().strip(),
            self.second_unload_time_input.text().strip(),
        ]

    def set_camera_settings(self, settings):
        self.camera_height_input.setText(str(settings["height"]))
        self.camera_width_input.setText(str(settings["width"]))
        self.camera_fps_input.setText(str(settings["fps"]))
        self.camera_device_index_input.setText(str(settings["device_index"]))

    def camera_settings(self):
        return {
            "height": self.camera_height_input.text().strip(),
            "width": self.camera_width_input.text().strip(),
            "fps": self.camera_fps_input.text().strip(),
            "device_index": self.camera_device_index_input.text().strip(),
        }
