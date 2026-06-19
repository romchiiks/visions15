from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


def create_button(buttons_config, button_variable_name):
    button_config = buttons_config[button_variable_name]
    button = QPushButton(button_config["button_text"])
    button.setObjectName(button_variable_name)
    return button


class SpinnerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.rotate)
        self.setFixedSize(48, 48)

    def start(self):
        self.timer.start()
        self.show()

    def stop(self):
        self.timer.stop()
        self.hide()

    def rotate(self):
        self.angle = (self.angle + 30) % 360
        self.update()

    def sizeHint(self):
        return QSize(48, 48)

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 8
        painter.translate(center)
        painter.rotate(self.angle)

        for index in range(12):
            color = QColor(0, 0, 0)
            color.setAlpha(40 + index * 18)
            painter.setPen(QPen(color, 3, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(0, -radius, 0, -radius + 10)
            painter.rotate(30)


class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Загрузка")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

        self.spinner = SpinnerWidget(self)
        self.label = QLabel("Загрузка")
        self.label.setAlignment(Qt.AlignCenter)

        content = QHBoxLayout()
        content.addWidget(self.spinner)
        content.addWidget(self.label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.addLayout(content)

    def start(self, text="Загрузка"):
        self.label.setText(text)
        self.spinner.start()
        self.show()

    def stop(self):
        self.spinner.stop()
        self.hide()
