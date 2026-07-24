from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from screens.common import create_button


class ImageScreen(QWidget):
    back_requested = Signal()

    def __init__(self, buttons_config):
        super().__init__()
        self.annotated_pixmap = QPixmap()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        nav = QHBoxLayout()
        self.image_back_button = create_button(buttons_config, "image_back_button")
        self.image_back_button.clicked.connect(self.back_requested.emit)
        nav.addWidget(self.image_back_button)
        nav.addStretch()

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(360)
        self.image_label.setText("Изображение ещё не отсканировано")

        layout.addLayout(nav)
        layout.addWidget(self.image_label, stretch=1)

    def show_prediction_result(self, prediction_result):
        pixmap = QPixmap(str(prediction_result.image_path))
        if pixmap.isNull():
            self.show_not_found()
            return

        self.annotated_pixmap = self.draw_predictions(
            pixmap,
            prediction_result.predictions,
            prediction_result.width,
            prediction_result.height,
        )
        self.update_displayed_pixmap()

    def draw_predictions(self, pixmap, predictions, source_width, source_height):
        annotated_pixmap = pixmap.copy()
        painter = QPainter(annotated_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        scale_x = annotated_pixmap.width() / source_width
        scale_y = annotated_pixmap.height() / source_height
        line_width = max(2, round(min(scale_x, scale_y) * 4))
        font = QFont()
        font.setPixelSize(max(18, round(annotated_pixmap.height() / 55)))
        font.setBold(True)
        painter.setFont(font)

        for prediction in predictions:
            x1, y1, x2, y2 = prediction.bbox_xyxy
            left = max(0.0, min(x1, x2) * scale_x)
            top = max(0.0, min(y1, y2) * scale_y)
            right = min(float(annotated_pixmap.width() - 1), max(x1, x2) * scale_x)
            bottom = min(float(annotated_pixmap.height() - 1), max(y1, y2) * scale_y)

            color = QColor(0, 200, 80)
            painter.setPen(QPen(color, line_width))
            painter.drawRect(QRectF(left, top, right - left, bottom - top))

            label = f"{prediction.category_name} | Уверенность: {prediction.score:.1%}"
            metrics = painter.fontMetrics()
            text_rect = metrics.boundingRect(label)
            label_height = text_rect.height() + 12
            label_width = text_rect.width() + 16
            label_top = top - label_height if top >= label_height else top
            label_rect = QRectF(left, label_top, label_width, label_height)

            painter.fillRect(label_rect, QColor(0, 0, 0, 190))
            painter.setPen(QPen(Qt.white))
            painter.drawText(
                label_rect.adjusted(8, 0, -8, 0),
                Qt.AlignLeft | Qt.AlignVCenter,
                label,
            )

        painter.end()
        return annotated_pixmap

    def update_displayed_pixmap(self):
        if self.annotated_pixmap.isNull():
            return

        self.image_label.setText("")
        self.image_label.setPixmap(
            self.annotated_pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_displayed_pixmap()

    def show_not_found(self):
        self.annotated_pixmap = QPixmap()
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText("Изображение ещё не отсканировано")
