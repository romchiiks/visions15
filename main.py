import json
import random
import sys
from pathlib import Path

import yaml
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QStackedWidget

from screens import AddDetailScreen, DatasetCameraScreen, HomeScreen, ImageScreen, ScanScreen
from services.camera_service import (
    get_dataset_class_dir,
    open_configured_camera,
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
        self.dataset_camera_settings = None
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

        self.home_screen = HomeScreen(self.buttons_config)
        self.scan_screen = ScanScreen(self.buttons_config)
        self.image_screen = ImageScreen(self.buttons_config)
        self.add_detail_screen = AddDetailScreen(self.buttons_config)
        self.dataset_camera_screen = DatasetCameraScreen(self.buttons_config)

        self.stack.addWidget(self.home_screen)
        self.stack.addWidget(self.scan_screen)
        self.stack.addWidget(self.image_screen)
        self.stack.addWidget(self.add_detail_screen)
        self.stack.addWidget(self.dataset_camera_screen)

        self.connect_screen_signals()

    def connect_screen_signals(self):
        self.home_screen.scan_requested.connect(self.open_scan_screen)
        self.home_screen.add_detail_requested.connect(self.open_add_detail_screen)

        self.scan_screen.back_requested.connect(self.open_home_screen)
        self.scan_screen.scan_requested.connect(self.scan_camera_image)
        self.scan_screen.show_image_requested.connect(self.open_image_screen)

        self.image_screen.back_requested.connect(self.return_to_scan_screen)

        self.add_detail_screen.back_requested.connect(self.open_home_screen)
        self.add_detail_screen.add_detail_requested.connect(self.add_detail_class)

        self.dataset_camera_screen.back_requested.connect(self.return_to_add_detail_screen)
        self.dataset_camera_screen.snapshot_requested.connect(self.take_dataset_snapshot)
        self.dataset_camera_screen.record_requested.connect(self.toggle_dataset_recording)

    def open_home_screen(self):
        self.stop_dataset_camera()
        self.stack.setCurrentWidget(self.home_screen)

    def open_scan_screen(self):
        self.stop_dataset_camera()
        self.scan_screen.clear_scan_result()
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

        self.dataset_camera_screen.set_class_name(self.active_dataset_class_name)
        self.stack.setCurrentWidget(self.dataset_camera_screen)
        self.start_dataset_camera()

    def add_detail_class(self):
        class_name = self.add_detail_screen.detail_name()
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
        self.add_detail_screen.clear_detail_input()
        self.load_details()
        self.open_dataset_camera_screen()

    def scan_camera_image(self):
        try:
            self.last_scanned_image_path = save_camera_image(is_scanned=True)
        except (RuntimeError, ValueError) as error:
            self.last_scanned_image_path = None
            QMessageBox.warning(self, "Сканирование", str(error))
            return

        self.scan_screen.show_scan_result()

    def open_image_screen(self):
        self.stack.setCurrentWidget(self.image_screen)
        self.image_screen.show_image(self.last_scanned_image_path)

    def load_details(self):
        self.add_detail_screen.show_details(self.read_details())

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
        try:
            self.dataset_camera, self.dataset_camera_settings = open_configured_camera()
        except ValueError as error:
            self.dataset_camera = None
            self.dataset_camera_settings = None
            QMessageBox.warning(self, "Камера", str(error))
            return

        fps = self.dataset_camera_settings["fps"]
        interval_ms = max(1, int(1000 / fps))
        self.dataset_preview_timer.setInterval(interval_ms)
        self.dataset_record_timer.setInterval(interval_ms)

        if not self.dataset_camera.isOpened():
            device_index = self.dataset_camera_settings["device_index"]
            self.dataset_camera.release()
            self.dataset_camera = None
            self.dataset_camera_settings = None
            self.dataset_camera_screen.show_message("Камера не найдена")
            QMessageBox.warning(self, "Камера", f"Не удалось открыть камеру с index device = {device_index}")
            return

        self.refresh_dataset_camera_frame()
        self.dataset_preview_timer.start()

    def stop_dataset_camera(self):
        self.dataset_preview_timer.stop()
        self.dataset_record_timer.stop()
        self.dataset_recording = False
        self.dataset_camera_screen.set_recording(False)

        if self.dataset_camera is not None:
            self.dataset_camera.release()
            self.dataset_camera = None

        self.dataset_camera_settings = None
        self.dataset_current_frame = None

    def refresh_dataset_camera_frame(self):
        if self.dataset_camera is None:
            return

        success, frame = self.dataset_camera.read()
        if not success:
            self.dataset_camera_screen.show_message("Не удалось получить кадр")
            return

        self.dataset_current_frame = frame
        self.dataset_camera_screen.show_frame(frame)

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
            self.dataset_camera_screen.set_recording(False)
            return

        if self.dataset_camera is None or self.active_dataset_class_name is None:
            return

        self.dataset_preview_timer.stop()
        self.dataset_recording = True
        self.dataset_camera_screen.set_recording(True)
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
        self.dataset_camera_screen.show_frame(frame)
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
