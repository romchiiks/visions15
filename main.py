import json
import random
import sys
from pathlib import Path

import cv2
import yaml
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.camera_service import (
    get_dataset_class_dir,
    save_camera_image,
    save_frame_image,
    validate_class_name,
)


BASE_DIR = Path(__file__).resolve().parent
BUTTONS_PATH = BASE_DIR / "buttons.yaml"
DETAILS_PATH = BASE_DIR / "details.json"


def load_buttons_config():
    with BUTTONS_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Складские детали")
        self.setMinimumSize(720, 480)
        self.buttons_config = load_buttons_config()
        self.last_scanned_image_path = None
        self.active_dataset_class_name = None
        self.dataset_camera = None
        self.dataset_current_frame = None
        self.dataset_recording = False

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.dataset_preview_timer = QTimer(self)
        self.dataset_preview_timer.setInterval(1000)
        self.dataset_preview_timer.timeout.connect(self.refresh_dataset_camera_frame)

        self.dataset_record_timer = QTimer(self)
        self.dataset_record_timer.setInterval(1000)
        self.dataset_record_timer.timeout.connect(self.record_dataset_frame)

        self.home_screen = self.create_home_screen()
        self.scan_screen = self.create_scan_screen()
        self.image_screen = self.create_image_screen()
        self.add_detail_screen = self.create_add_detail_screen()
        self.dataset_camera_screen = self.create_dataset_camera_screen()

        self.stack.addWidget(self.home_screen)
        self.stack.addWidget(self.scan_screen)
        self.stack.addWidget(self.image_screen)
        self.stack.addWidget(self.add_detail_screen)
        self.stack.addWidget(self.dataset_camera_screen)

    def create_home_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        scan_button = self.create_button("scan_button")
        add_detail_button = self.create_button("add_detail_button")

        scan_button.clicked.connect(self.open_scan_screen)
        add_detail_button.clicked.connect(self.open_add_detail_screen)

        layout.addWidget(scan_button)
        layout.addWidget(add_detail_button)

        return page

    def create_scan_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        nav = QHBoxLayout()
        scan_back_button = self.create_button("scan_back_button")
        scan_action_button = self.create_button("scan_action_button")
        show_image_button = self.create_button("show_image_button")

        scan_back_button.clicked.connect(self.open_home_screen)
        scan_action_button.clicked.connect(self.scan_camera_image)
        show_image_button.clicked.connect(self.open_image_screen)

        nav.addWidget(scan_back_button)
        nav.addWidget(scan_action_button)
        nav.addWidget(show_image_button)
        nav.addStretch()

        title = QLabel("Результат сканирования")
        title.setObjectName("title")

        self.scan_results_table = QTableWidget(0, 3)
        self.scan_results_table.setHorizontalHeaderLabels(["Наименование", "Количество", "Артикул"])
        self.scan_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.scan_results_table.verticalHeader().setVisible(False)

        layout.addLayout(nav)
        layout.addWidget(title)
        layout.addWidget(self.scan_results_table)

        return page

    def create_image_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        nav = QHBoxLayout()
        image_back_button = self.create_button("image_back_button")
        image_back_button.clicked.connect(self.return_to_scan_screen)
        nav.addWidget(image_back_button)
        nav.addStretch()

        self.scanned_image_label = QLabel()
        self.scanned_image_label.setAlignment(Qt.AlignCenter)
        self.scanned_image_label.setMinimumHeight(360)
        self.scanned_image_label.setText("Изображение не найдено")

        layout.addLayout(nav)
        layout.addWidget(self.scanned_image_label, stretch=1)

        return page

    def create_add_detail_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        nav = QHBoxLayout()
        add_detail_back_button = self.create_button("add_detail_back_button")
        add_detail_back_button.clicked.connect(self.open_home_screen)
        nav.addWidget(add_detail_back_button)
        nav.addStretch()

        input_row = QHBoxLayout()
        self.detail_input = QLineEdit()
        self.detail_input.setPlaceholderText("Введите новый класс детали")

        detail_add_button = self.create_button("detail_add_button")
        detail_add_button.clicked.connect(self.add_detail_class)

        input_row.addWidget(self.detail_input, stretch=1)
        input_row.addWidget(detail_add_button)

        self.details_table = QTableWidget(0, 2)
        self.details_table.setHorizontalHeaderLabels(["Деталь", "Артикул"])
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.details_table.verticalHeader().setVisible(False)

        layout.addLayout(nav)
        layout.addLayout(input_row)
        layout.addWidget(self.details_table)

        return page

    def create_dataset_camera_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        nav = QHBoxLayout()
        dataset_camera_back_button = self.create_button("dataset_camera_back_button")
        dataset_camera_back_button.clicked.connect(self.return_to_add_detail_screen)
        nav.addWidget(dataset_camera_back_button)
        nav.addStretch()

        self.dataset_camera_title = QLabel("Новый класс детали")
        self.dataset_camera_title.setObjectName("title")

        self.dataset_camera_label = QLabel()
        self.dataset_camera_label.setAlignment(Qt.AlignCenter)
        self.dataset_camera_label.setMinimumHeight(320)
        self.dataset_camera_label.setText("Камера не запущена")

        actions = QHBoxLayout()
        self.dataset_snapshot_button = self.create_button("dataset_snapshot_button")
        self.dataset_record_button = self.create_button("dataset_record_button")
        self.dataset_snapshot_button.clicked.connect(self.take_dataset_snapshot)
        self.dataset_record_button.clicked.connect(self.toggle_dataset_recording)
        actions.addWidget(self.dataset_snapshot_button)
        actions.addWidget(self.dataset_record_button)
        actions.addStretch()

        layout.addLayout(nav)
        layout.addWidget(self.dataset_camera_title)
        layout.addWidget(self.dataset_camera_label, stretch=1)
        layout.addLayout(actions)

        return page

    def create_button(self, button_variable_name):
        button_config = self.buttons_config[button_variable_name]
        button = QPushButton(button_config["button_text"])
        button.setObjectName(button_variable_name)
        return button

    def open_home_screen(self):
        self.stop_dataset_camera()
        self.stack.setCurrentWidget(self.home_screen)

    def open_scan_screen(self):
        self.stop_dataset_camera()
        self.clear_scan_result()
        self.stack.setCurrentWidget(self.scan_screen)

    def return_to_scan_screen(self):
        self.stack.setCurrentWidget(self.scan_screen)

    def open_add_detail_screen(self):
        self.stop_dataset_camera()
        self.load_details()
        self.stack.setCurrentWidget(self.add_detail_screen)

    def return_to_add_detail_screen(self):
        self.stop_dataset_camera()
        self.load_details()
        self.stack.setCurrentWidget(self.add_detail_screen)

    def open_dataset_camera_screen(self):
        if self.active_dataset_class_name is None:
            QMessageBox.warning(self, "Добавление детали", "Сначала добавьте класс детали")
            return

        self.dataset_camera_title.setText(f"Класс детали: {self.active_dataset_class_name}")
        self.stack.setCurrentWidget(self.dataset_camera_screen)
        self.start_dataset_camera()

    def add_detail_class(self):
        class_name = self.detail_input.text().strip()
        try:
            class_name = validate_class_name(class_name)
        except ValueError as error:
            QMessageBox.warning(self, "Добавление детали", str(error))
            return

        details = self.read_details()
        if class_name not in details:
            details[class_name] = self.generate_random_article(details.values())
            self.write_details(details)

        get_dataset_class_dir(class_name)
        self.active_dataset_class_name = class_name
        self.detail_input.clear()
        self.load_details()
        self.open_dataset_camera_screen()

    def scan_camera_image(self):
        self.last_scanned_image_path = save_camera_image(is_scanned=True)
        self.show_scan_result()

    def open_image_screen(self):
        self.stack.setCurrentWidget(self.image_screen)
        self.show_last_scanned_image()

    def show_scan_result(self):
        self.scan_results_table.setRowCount(1)
        for column in range(3):
            item = QTableWidgetItem("null")
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.scan_results_table.setItem(0, column, item)

    def clear_scan_result(self):
        self.scan_results_table.setRowCount(0)

    def show_last_scanned_image(self):
        if self.last_scanned_image_path is None:
            self.scanned_image_label.setPixmap(QPixmap())
            self.scanned_image_label.setText("Изображение не найдено")
            return

        pixmap = QPixmap(str(self.last_scanned_image_path))
        if pixmap.isNull():
            self.scanned_image_label.setPixmap(QPixmap())
            self.scanned_image_label.setText("Изображение не найдено")
            return

        self.scanned_image_label.setText("")
        scaled_pixmap = pixmap.scaled(
            self.scanned_image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.scanned_image_label.setPixmap(scaled_pixmap)

    def load_details(self):
        details = self.read_details()

        self.details_table.setRowCount(len(details))
        for row, (detail, article) in enumerate(details.items()):
            detail_item = QTableWidgetItem(detail)
            article_item = QTableWidgetItem(str(article))
            detail_item.setFlags(detail_item.flags() & ~Qt.ItemIsEditable)
            article_item.setFlags(article_item.flags() & ~Qt.ItemIsEditable)
            self.details_table.setItem(row, 0, detail_item)
            self.details_table.setItem(row, 1, article_item)

    def read_details(self):
        if not DETAILS_PATH.exists() or DETAILS_PATH.stat().st_size == 0:
            return {}

        with DETAILS_PATH.open("r", encoding="utf-8") as file:
            try:
                details = json.load(file)
            except json.JSONDecodeError:
                return {}

        if not isinstance(details, dict):
            return {}

        return details

    def write_details(self, details):
        with DETAILS_PATH.open("w", encoding="utf-8") as file:
            json.dump(details, file, ensure_ascii=False, indent=2)
            file.write("\n")

    def generate_random_article(self, existing_articles):
        existing_articles = {str(article) for article in existing_articles}
        while True:
            article = str(random.randint(10000, 99999))
            if article not in existing_articles:
                return article

    def start_dataset_camera(self):
        self.stop_dataset_camera()
        self.dataset_camera = cv2.VideoCapture(0)
        self.dataset_camera.set(cv2.CAP_PROP_FPS, 1)

        if not self.dataset_camera.isOpened():
            self.dataset_camera.release()
            self.dataset_camera = None
            self.dataset_camera_label.setPixmap(QPixmap())
            self.dataset_camera_label.setText("Камера не найдена")
            QMessageBox.warning(self, "Камера", "Не удалось открыть камеру с index device = 0")
            return

        self.refresh_dataset_camera_frame()
        self.dataset_preview_timer.start()

    def stop_dataset_camera(self):
        self.dataset_preview_timer.stop()
        self.dataset_record_timer.stop()
        self.dataset_recording = False
        if hasattr(self, "dataset_record_button"):
            self.dataset_record_button.setText(self.buttons_config["dataset_record_button"]["button_text"])

        if self.dataset_camera is not None:
            self.dataset_camera.release()
            self.dataset_camera = None

        self.dataset_current_frame = None

    def refresh_dataset_camera_frame(self):
        if self.dataset_camera is None:
            return

        success, frame = self.dataset_camera.read()
        if not success:
            self.dataset_camera_label.setPixmap(QPixmap())
            self.dataset_camera_label.setText("Не удалось получить кадр")
            return

        self.dataset_current_frame = frame
        self.show_dataset_frame(frame)

    def show_dataset_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb_frame.shape
        bytes_per_line = channels * width
        image = QImage(
            rgb_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888,
        ).copy()

        self.dataset_camera_label.setText("")
        pixmap = QPixmap.fromImage(image)
        self.dataset_camera_label.setPixmap(
            pixmap.scaled(
                self.dataset_camera_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def take_dataset_snapshot(self):
        if self.active_dataset_class_name is None:
            return
        if self.dataset_current_frame is None:
            self.refresh_dataset_camera_frame()
        if self.dataset_current_frame is None:
            QMessageBox.warning(self, "Камера", "Нет кадра для сохранения")
            return

        save_frame_image(
            self.dataset_current_frame,
            class_name=self.active_dataset_class_name,
            is_scanned=False,
        )

    def toggle_dataset_recording(self):
        if self.dataset_recording:
            self.dataset_record_timer.stop()
            self.dataset_preview_timer.start()
            self.dataset_recording = False
            self.dataset_record_button.setText(self.buttons_config["dataset_record_button"]["button_text"])
            return

        if self.dataset_camera is None or self.active_dataset_class_name is None:
            return

        self.dataset_preview_timer.stop()
        self.dataset_recording = True
        self.dataset_record_button.setText("Остановить запись")
        self.record_dataset_frame()
        self.dataset_record_timer.start()

    def record_dataset_frame(self):
        if self.dataset_camera is None or self.active_dataset_class_name is None:
            return

        success, frame = self.dataset_camera.read()
        if not success:
            QMessageBox.warning(self, "Камера", "Не удалось получить кадр для записи")
            self.toggle_dataset_recording()
            return

        self.dataset_current_frame = frame
        self.show_dataset_frame(frame)
        save_frame_image(
            frame,
            class_name=self.active_dataset_class_name,
            is_scanned=False,
        )

    def closeEvent(self, event):
        self.stop_dataset_camera()
        super().closeEvent(event)


def apply_styles(app):
    app.setStyleSheet(
        """
        QWidget {
            background: #ffffff;
            color: #000000;
            font-size: 18px;
        }

        QPushButton {
            background: #f3f3f3;
            color: #000000;
            border: 1px solid #9a9a9a;
            border-radius: 4px;
            padding: 12px 20px;
            min-height: 44px;
        }

        QPushButton:hover {
            background: #e9e9e9;
        }

        QPushButton:pressed {
            background: #dcdcdc;
        }

        QLineEdit {
            background: #ffffff;
            color: #000000;
            border: 1px solid #9a9a9a;
            border-radius: 4px;
            padding: 10px 12px;
            min-height: 42px;
        }

        QTableWidget {
            background: #ffffff;
            color: #000000;
            border: 1px solid #b0b0b0;
            gridline-color: #d0d0d0;
            selection-background-color: #e6f0ff;
            selection-color: #000000;
        }

        QHeaderView::section {
            background: #f0f0f0;
            color: #000000;
            border: 1px solid #b0b0b0;
            padding: 8px;
            font-weight: 600;
        }

        QLabel#title {
            font-size: 22px;
            font-weight: 600;
        }
        """
    )


def main():
    app = QApplication(sys.argv)
    apply_styles(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
