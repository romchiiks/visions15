import json
import random
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import monotonic, sleep

import yaml
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QStackedWidget

from screens import (
    AddDetailScreen,
    DatasetCameraScreen,
    HomeScreen,
    ImageScreen,
    ScanScreen,
    SettingsCameraScreen,
    SettingsScreen,
    UploadScreen,
)
from screens.common import LoadingDialog
from services.camera_service import (
    CAMERA_CONFIG_PATH,
    DATASET_METADATA_PATH,
    DEFAULT_CAMERA_CONFIG,
    count_dataset_images,
    open_configured_camera,
    remove_empty_dataset_class_dir,
    save_camera_image,
    save_frame_image,
    validate_class_name,
    write_dataset_metadata,
)
from services.perspective_warp_service import (
    detect_aruco_marker_rectangle,
    draw_aruco_marker_rectangle,
)
from services.upload_service import (
    UploadArchiveError,
    UploadRequestError,
    upload_selected_classes,
)


BASE_DIR = Path(__file__).resolve().parent
BUTTONS_PATH = BASE_DIR / "buttons.yaml"
DETAILS_PATH = BASE_DIR / "details.json"
ENV_PATH = BASE_DIR / ".env"
SERVER_HEALTH_TIMEOUT_SECONDS = 5


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
        self.active_dataset_article = None
        self.active_dataset_is_new_class = False
        self.dataset_camera = None
        self.dataset_camera_settings = None
        self.dataset_current_frame = None
        self.dataset_marker_rectangle = None
        self.dataset_pending_frames = []
        self.dataset_saved_images_count = 0
        self.dataset_recording = False
        self.settings_camera = None
        self.settings_camera_settings = None
        self.loading_dialog = LoadingDialog(self)
        self.loading_executor = ThreadPoolExecutor(max_workers=1)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.dataset_preview_timer = QTimer(self)
        self.dataset_preview_timer.setInterval(1000)
        self.dataset_preview_timer.timeout.connect(self.refresh_dataset_camera_frame)

        self.dataset_record_timer = QTimer(self)
        self.dataset_record_timer.setInterval(1000)
        self.dataset_record_timer.timeout.connect(self.record_dataset_frame)

        self.settings_camera_timer = QTimer(self)
        self.settings_camera_timer.setInterval(1000)
        self.settings_camera_timer.timeout.connect(self.refresh_settings_camera_frame)

        self.home_screen = HomeScreen(self.buttons_config)
        self.scan_screen = ScanScreen(self.buttons_config)
        self.image_screen = ImageScreen(self.buttons_config)
        self.add_detail_screen = AddDetailScreen(self.buttons_config)
        self.upload_screen = UploadScreen(self.buttons_config)
        self.dataset_camera_screen = DatasetCameraScreen(self.buttons_config)
        self.settings_screen = SettingsScreen(self.buttons_config)
        self.settings_camera_screen = SettingsCameraScreen(self.buttons_config)

        self.stack.addWidget(self.home_screen)
        self.stack.addWidget(self.scan_screen)
        self.stack.addWidget(self.image_screen)
        self.stack.addWidget(self.add_detail_screen)
        self.stack.addWidget(self.upload_screen)
        self.stack.addWidget(self.dataset_camera_screen)
        self.stack.addWidget(self.settings_screen)
        self.stack.addWidget(self.settings_camera_screen)

        self.connect_screen_signals()

    def show_loading(self, text="Загрузка"):
        self.loading_dialog.start(text)
        QApplication.processEvents()

    def hide_loading(self):
        self.loading_dialog.stop()
        QApplication.processEvents()

    def process_loading_events(self):
        QApplication.processEvents()

    def run_with_current_loading(self, operation):
        future = self.loading_executor.submit(operation)
        while not future.done():
            self.process_loading_events()
            sleep(0.03)

        return future.result()

    def run_blocking_with_loading(self, text, operation):
        self.show_loading(text)
        try:
            return self.run_with_current_loading(operation)
        finally:
            self.hide_loading()

    def connect_screen_signals(self):
        self.home_screen.scan_requested.connect(self.open_scan_screen)
        self.home_screen.add_detail_requested.connect(self.open_add_detail_screen)
        self.home_screen.upload_requested.connect(self.open_upload_screen)
        self.home_screen.settings_requested.connect(self.open_settings_screen)

        self.scan_screen.back_requested.connect(self.open_home_screen)
        self.scan_screen.scan_requested.connect(self.scan_camera_image)
        self.scan_screen.show_image_requested.connect(self.open_image_screen)

        self.image_screen.back_requested.connect(self.return_to_scan_screen)

        self.add_detail_screen.back_requested.connect(self.open_home_screen)
        self.add_detail_screen.add_detail_requested.connect(self.add_detail_class)

        self.upload_screen.back_requested.connect(self.open_home_screen)
        self.upload_screen.upload_requested.connect(self.upload_selected_classes)

        self.dataset_camera_screen.back_requested.connect(self.cancel_dataset_detail)
        self.dataset_camera_screen.snapshot_requested.connect(self.take_dataset_snapshot)
        self.dataset_camera_screen.record_requested.connect(self.toggle_dataset_recording)
        self.dataset_camera_screen.save_requested.connect(self.save_dataset_images)

        self.settings_screen.back_requested.connect(self.open_home_screen)
        self.settings_screen.save_requested.connect(self.save_settings)
        self.settings_screen.check_connection_requested.connect(self.check_server_connection)
        self.settings_screen.camera_output_requested.connect(self.open_settings_camera_screen)

        self.settings_camera_screen.back_requested.connect(self.open_settings_screen)

    def open_home_screen(self):
        self.stop_dataset_camera()
        self.stop_settings_camera()
        self.stack.setCurrentWidget(self.home_screen)

    def open_scan_screen(self):
        self.stop_dataset_camera()
        self.stop_settings_camera()
        self.scan_screen.clear_scan_result()
        self.stack.setCurrentWidget(self.scan_screen)

    def return_to_scan_screen(self):
        self.stack.setCurrentWidget(self.scan_screen)

    def open_add_detail_screen(self):
        self.stop_dataset_camera()
        self.stop_settings_camera()
        self.load_details()
        self.stack.setCurrentWidget(self.add_detail_screen)

    def return_to_add_detail_screen(self):
        self.stop_dataset_camera()
        self.load_details()
        self.stack.setCurrentWidget(self.add_detail_screen)

    def open_upload_screen(self):
        self.stop_dataset_camera()
        self.stop_settings_camera()
        self.load_upload_classes()
        self.stack.setCurrentWidget(self.upload_screen)

    def load_upload_classes(self):
        self.upload_screen.show_classes(self.read_upload_classes(), self.read_details())

    def read_upload_classes(self):
        if not DATASET_METADATA_PATH.exists() or DATASET_METADATA_PATH.stat().st_size == 0:
            return {}

        try:
            with DATASET_METADATA_PATH.open("r", encoding="utf-8") as file:
                metadata = json.load(file)
        except (OSError, json.JSONDecodeError):
            return {}

        classes = metadata.get("classes", {})
        if not isinstance(classes, dict):
            return {}

        return {
            str(class_name): class_data
            for class_name, class_data in classes.items()
            if isinstance(class_data, dict)
        }

    def upload_selected_classes(self):
        selected_classes = self.upload_screen.selected_classes()
        if not selected_classes:
            QMessageBox.information(self, "Выгрузка", "Классы не выбраны")
            return

        try:
            archive_paths, response_status_code = self.run_blocking_with_loading(
                "Выгрузка",
                lambda: self.upload_selected_classes_data(selected_classes),
            )
        except (OSError, ValueError, json.JSONDecodeError, UploadArchiveError, UploadRequestError) as error:
            QMessageBox.warning(self, "Выгрузка", str(error))
            return

        self.load_upload_classes()

        archive_message_title = "Создан архив" if len(archive_paths) == 1 else "Созданы архивы"
        message = (
            f"{archive_message_title}:\n"
            + "\n".join(str(path) for path in archive_paths)
            + f"\n\nПроект отправлен. Код ответа: {response_status_code}"
        )

        QMessageBox.information(self, "Выгрузка", message)

    def upload_selected_classes_data(self, selected_classes):
        archive_paths, response = upload_selected_classes(selected_classes)
        return archive_paths, response.status_code

    def reset_dataset_detail_state(self):
        self.active_dataset_class_name = None
        self.active_dataset_article = None
        self.active_dataset_is_new_class = False
        self.dataset_marker_rectangle = None
        self.dataset_pending_frames = []
        self.dataset_saved_images_count = 0

    def open_dataset_camera_screen(self):
        if self.active_dataset_class_name is None:
            QMessageBox.warning(self, "Добавление детали", "Сначала добавьте класс детали")
            return

        self.dataset_camera_screen.set_class_name(self.active_dataset_class_name)
        self.stack.setCurrentWidget(self.dataset_camera_screen)
        self.start_dataset_camera()

    def open_settings_screen(self):
        self.stop_dataset_camera()
        self.stop_settings_camera()
        self.load_server_settings()
        self.load_camera_settings()
        self.stack.setCurrentWidget(self.settings_screen)

    def open_settings_camera_screen(self):
        self.stop_dataset_camera()
        self.settings_camera_screen.show_message("Камера запускается")
        self.stack.setCurrentWidget(self.settings_camera_screen)
        self.start_settings_camera()

    def save_settings(self):
        unload_times = self.settings_screen.unload_times()
        if not self.are_unload_times_valid(unload_times):
            QMessageBox.warning(self, "Настройки", "Введите часы выгрузки в формате ЧЧ:ММ")
            return

        try:
            camera_settings = self.parse_camera_settings(self.settings_screen.camera_settings())
        except ValueError as error:
            QMessageBox.warning(self, "Настройки", str(error))
            return

        api_key = self.settings_screen.api_key()

        def write_settings():
            self.write_env_values(
                {
                    "API_KEY": api_key,
                    "UNLOAD_TIME_1": unload_times[0],
                    "UNLOAD_TIME_2": unload_times[1],
                }
            )
            self.write_camera_config(camera_settings)

        try:
            self.run_blocking_with_loading("Сохранение настроек", write_settings)
        except OSError as error:
            QMessageBox.warning(self, "Настройки", str(error))
            return

        QMessageBox.information(self, "Настройки", "Настройки сохранены")

    def check_server_connection(self):
        api_url = self.read_env_value("API_URL")
        if not api_url:
            QMessageBox.warning(self, "Настройки", "Соединение: ОШИБКА")
            return

        health_url = self.build_health_url(api_url)

        def request_health():
            with urllib.request.urlopen(health_url, timeout=SERVER_HEALTH_TIMEOUT_SECONDS) as response:
                return json.loads(response.read().decode("utf-8"))

        try:
            response_data = self.run_blocking_with_loading("Проверка соединения", request_health)
        except (TimeoutError, OSError, urllib.error.URLError, json.JSONDecodeError):
            QMessageBox.warning(self, "Настройки", "Соединение: ОШИБКА")
            return

        if response_data.get("status") == "ok":
            QMessageBox.information(self, "Настройки", "Соединение: ОК")
            return

        QMessageBox.warning(self, "Настройки", "Соединение: ОШИБКА")

    def build_health_url(self, api_url):
        api_url = api_url.strip().rstrip("/")
        if not re.match(r"^https?://", api_url):
            api_url = f"http://{api_url}"

        return f"{api_url}/health"

    def read_env_value(self, target_key):
        if not ENV_PATH.exists() or ENV_PATH.stat().st_size == 0:
            return None

        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("#"):
                continue
            if stripped_line.startswith("export "):
                stripped_line = stripped_line[len("export ") :].lstrip()
            if "=" not in stripped_line:
                continue

            key, value = stripped_line.split("=", 1)
            if key.strip() != target_key:
                continue

            return self.parse_env_value(value.strip())

        return None

    def parse_env_value(self, value):
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ['"', "'"]:
            value = value[1:-1]

        return value.replace('\\"', '"').replace("\\\\", "\\")

    def are_unload_times_valid(self, unload_times):
        time_pattern = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
        return all(time_pattern.fullmatch(unload_time) for unload_time in unload_times)

    def load_server_settings(self):
        self.settings_screen.set_server_settings(
            {
                "api_key": self.read_env_value("API_KEY") or "",
                "unload_time_1": self.read_env_value("UNLOAD_TIME_1") or "",
                "unload_time_2": self.read_env_value("UNLOAD_TIME_2") or "",
            }
        )

    def load_camera_settings(self):
        camera_config = self.read_camera_config()
        settings = DEFAULT_CAMERA_CONFIG.copy()
        settings.update(camera_config)
        self.settings_screen.set_camera_settings(settings)

    def read_camera_config(self):
        if not CAMERA_CONFIG_PATH.exists() or CAMERA_CONFIG_PATH.stat().st_size == 0:
            return {}

        with CAMERA_CONFIG_PATH.open("r", encoding="utf-8") as file:
            try:
                config = json.load(file)
            except json.JSONDecodeError:
                return {}

        if not isinstance(config, dict):
            return {}

        return config

    def parse_camera_settings(self, raw_settings):
        labels = {
            "height": "Высота",
            "width": "Ширина",
            "capture_interval": "Интервал записи",
            "fps": "FPS",
            "device_index": "Индекс устройства",
        }
        settings = {}

        for key, label in labels.items():
            try:
                settings[key] = int(raw_settings[key])
            except (TypeError, ValueError):
                raise ValueError(f"{label}: введите целое число") from None

        if settings["height"] <= 0:
            raise ValueError("Высота должна быть больше 0")
        if settings["width"] <= 0:
            raise ValueError("Ширина должна быть больше 0")
        if settings["capture_interval"] <= 0:
            raise ValueError("Интервал записи должен быть больше 0")
        if settings["fps"] <= 0:
            raise ValueError("FPS должен быть больше 0")
        if settings["device_index"] < 0:
            raise ValueError("Индекс устройства должен быть больше или равен 0")

        return settings

    def write_camera_config(self, camera_settings):
        config = DEFAULT_CAMERA_CONFIG.copy()
        config.update(self.read_camera_config())
        config.update(camera_settings)

        with CAMERA_CONFIG_PATH.open("w", encoding="utf-8") as file:
            json.dump(config, file, ensure_ascii=False, indent=2)
            file.write("\n")

    def write_env_values(self, values):
        lines = []
        updated_keys = set()

        if ENV_PATH.exists():
            lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

        for index, line in enumerate(lines):
            stripped_line = line.lstrip()
            for key, value in values.items():
                if stripped_line.startswith(f"{key}=") or stripped_line.startswith(f"export {key}="):
                    lines[index] = f"{key}={self.format_env_value(value)}"
                    updated_keys.add(key)
                    break

        for key, value in values.items():
            if key not in updated_keys:
                lines.append(f"{key}={self.format_env_value(value)}")

        ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def format_env_value(self, value):
        if value == "" or any(char.isspace() or char in ['"', "'", "#", "\\"] for char in value):
            escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped_value}"'

        return value

    def add_detail_class(self):
        class_name = self.add_detail_screen.detail_name()
        try:
            class_name = validate_class_name(class_name)
        except ValueError as error:
            QMessageBox.warning(self, "Добавление детали", str(error))
            return

        details = self.read_details()
        if class_name in details:
            article = details[class_name]
            is_new_class = False
        else:
            article = self.generate_random_article(details.values())
            is_new_class = True

        self.active_dataset_class_name = class_name
        self.active_dataset_article = article
        self.active_dataset_is_new_class = is_new_class
        self.dataset_pending_frames = []
        self.dataset_saved_images_count = count_dataset_images(class_name)
        self.add_detail_screen.clear_detail_input()
        self.open_dataset_camera_screen()

    def scan_camera_image(self):
        try:
            self.last_scanned_image_path = self.run_blocking_with_loading(
                "Сканирование",
                lambda: save_camera_image(is_scanned=True),
            )
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
        self.update_dataset_images_count()
        self.show_loading("Запуск камеры")
        try:
            try:
                self.dataset_camera, self.dataset_camera_settings = self.run_with_current_loading(
                    open_configured_camera
                )
            except ValueError as error:
                self.dataset_camera = None
                self.dataset_camera_settings = None
                self.hide_loading()
                QMessageBox.warning(self, "Камера", str(error))
                return

            fps = self.dataset_camera_settings["fps"]
            preview_interval_ms = max(1, int(1000 / fps))
            record_interval_ms = self.dataset_camera_settings["capture_interval"] * 1000
            self.dataset_preview_timer.setInterval(preview_interval_ms)
            self.dataset_record_timer.setInterval(record_interval_ms)

            if not self.dataset_camera.isOpened():
                device_index = self.dataset_camera_settings["device_index"]
                self.dataset_camera.release()
                self.dataset_camera = None
                self.dataset_camera_settings = None
                self.dataset_camera_screen.show_message("Камера не найдена")
                self.hide_loading()
                QMessageBox.warning(self, "Камера", f"Не удалось открыть камеру с index device = {device_index}")
                return

            self.loading_dialog.label.setText("Определение рабочей области")
            self.process_loading_events()
            if not self.detect_dataset_marker_rectangle_on_start():
                return

            self.dataset_preview_timer.start()
        finally:
            self.hide_loading()

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
        self.dataset_marker_rectangle = None

    def update_dataset_images_count(self):
        self.dataset_camera_screen.set_images_count(
            self.dataset_saved_images_count + len(self.dataset_pending_frames)
        )

    def detect_dataset_marker_rectangle_on_start(self):
        while self.dataset_camera is not None:
            frame = self.read_dataset_warmup_frame()
            if frame is None:
                return False

            try:
                self.dataset_marker_rectangle = detect_aruco_marker_rectangle(frame)
            except RuntimeError:
                self.dataset_marker_rectangle = None
                self.dataset_camera_screen.show_frame(frame)
                self.hide_loading()
                should_retry = self.should_retry_dataset_marker_detection()
                if should_retry:
                    self.show_loading("Определение рабочей области")
                    continue

                self.cancel_dataset_detail()
                return False

            self.show_dataset_frame(frame)
            return True

        return False

    def read_dataset_warmup_frame(self):
        warmup_seconds = self.dataset_camera_settings["scan_warmup_seconds"]
        started_at = monotonic()
        last_frame = None

        while self.dataset_camera is not None:
            success, frame = self.dataset_camera.read()
            if not success:
                self.dataset_camera_screen.show_message("Не удалось получить кадр")
                return None

            last_frame = frame
            self.dataset_current_frame = frame
            if monotonic() - started_at >= warmup_seconds:
                return last_frame

            self.process_loading_events()
            sleep(0.05)

        return None

    def should_retry_dataset_marker_detection(self):
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Рабочая область")
        message_box.setText("Рабочая область не определена")
        retry_button = message_box.addButton("Попробовать снова", QMessageBox.AcceptRole)
        message_box.addButton("Отмена", QMessageBox.RejectRole)
        message_box.setDefaultButton(retry_button)
        message_box.exec()

        return message_box.clickedButton() == retry_button

    def refresh_dataset_camera_frame(self):
        if self.dataset_camera is None:
            return

        success, frame = self.dataset_camera.read()
        if not success:
            self.dataset_camera_screen.show_message("Не удалось получить кадр")
            return

        self.dataset_current_frame = frame
        self.show_dataset_frame(frame)

    def show_dataset_frame(self, frame):
        if self.dataset_marker_rectangle is None:
            self.dataset_camera_screen.show_frame(frame)
            return

        self.dataset_camera_screen.show_frame(
            draw_aruco_marker_rectangle(frame, self.dataset_marker_rectangle)
        )

    def take_dataset_snapshot(self):
        if self.active_dataset_class_name is None:
            return
        if self.dataset_current_frame is None:
            self.refresh_dataset_camera_frame()
        if self.dataset_current_frame is None:
            QMessageBox.warning(self, "Камера", "Нет кадра для сохранения")
            return

        self.dataset_pending_frames.append(self.dataset_current_frame.copy())
        self.update_dataset_images_count()

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
        self.show_dataset_frame(frame)
        self.dataset_pending_frames.append(frame.copy())
        self.update_dataset_images_count()

    def save_dataset_images(self):
        if self.active_dataset_class_name is None:
            return
        if self.dataset_recording:
            self.toggle_dataset_recording()
        if not self.dataset_pending_frames:
            QMessageBox.information(self, "Датасет", "Нет новых фотографий для сохранения")
            return

        class_name = self.active_dataset_class_name
        article = self.active_dataset_article
        pending_frames = list(self.dataset_pending_frames)

        def save_images():
            for frame in pending_frames:
                save_frame_image(
                    frame,
                    class_name=class_name,
                    is_scanned=False,
                )
            details = self.read_details()
            if class_name not in details:
                details[class_name] = article
                self.write_details(details)

            images_count = count_dataset_images(class_name)
            write_dataset_metadata(details)
            return images_count

        try:
            images_count = self.run_blocking_with_loading("Сохранение", save_images)
            self.dataset_pending_frames = []
            self.dataset_saved_images_count = images_count
        except (RuntimeError, ValueError, OSError) as error:
            QMessageBox.warning(self, "Датасет", str(error))
            return

        self.update_dataset_images_count()
        QMessageBox.information(self, "Датасет", "Успешно сохранено")
        self.return_to_add_detail_screen()
        self.reset_dataset_detail_state()

    def cancel_dataset_detail(self):
        class_name = self.active_dataset_class_name
        is_new_class = self.active_dataset_is_new_class

        self.stop_dataset_camera()
        self.reset_dataset_detail_state()
        if class_name is not None and is_new_class:
            remove_empty_dataset_class_dir(class_name)

        self.load_details()
        self.stack.setCurrentWidget(self.add_detail_screen)

    def start_settings_camera(self):
        self.stop_settings_camera()
        try:
            self.settings_camera, self.settings_camera_settings = self.run_blocking_with_loading(
                "Запуск камеры",
                open_configured_camera,
            )
        except ValueError as error:
            self.settings_camera = None
            self.settings_camera_settings = None
            self.settings_camera_screen.show_message("Камера не запущена")
            QMessageBox.warning(self, "Камера", str(error))
            return

        fps = self.settings_camera_settings["fps"]
        interval_ms = max(1, int(1000 / fps))
        self.settings_camera_timer.setInterval(interval_ms)

        if not self.settings_camera.isOpened():
            device_index = self.settings_camera_settings["device_index"]
            self.settings_camera.release()
            self.settings_camera = None
            self.settings_camera_settings = None
            self.settings_camera_screen.show_message("Камера не найдена")
            QMessageBox.warning(self, "Камера", f"Не удалось открыть камеру с index device = {device_index}")
            return

        self.refresh_settings_camera_frame()
        self.settings_camera_timer.start()

    def stop_settings_camera(self):
        self.settings_camera_timer.stop()

        if self.settings_camera is not None:
            self.settings_camera.release()
            self.settings_camera = None

        self.settings_camera_settings = None

    def refresh_settings_camera_frame(self):
        if self.settings_camera is None:
            return

        success, frame = self.settings_camera.read()
        if not success:
            self.settings_camera_screen.show_message("Не удалось получить кадр")
            return

        self.settings_camera_screen.show_frame(frame)

    def closeEvent(self, event):
        self.stop_dataset_camera()
        self.stop_settings_camera()
        self.loading_executor.shutdown(wait=False, cancel_futures=True)
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
