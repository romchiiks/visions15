from PySide6.QtWidgets import QPushButton


def create_button(buttons_config, button_variable_name):
    button_config = buttons_config[button_variable_name]
    button = QPushButton(button_config["button_text"])
    button.setObjectName(button_variable_name)
    return button
