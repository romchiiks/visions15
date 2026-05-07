import json
from datetime import datetime
from pathlib import Path
from time import monotonic, sleep
import re

import cv2


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CAMERA_CONFIG_PATH = PROJECT_ROOT / "camera_config.json"
CAPTURES_DIR = PROJECT_ROOT / "captures"
SCANNED_DIR = CAPTURES_DIR / "scanned"
DATASET_DIR = CAPTURES_DIR / "dataset"
DEFAULT_CAMERA_CONFIG = {
    "device_index": 0,
    "fps": 1,
    "width": 640,
    "height": 480,
}


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")


def _ensure_dir(target_dir: Path | str) -> Path:
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def _load_camera_config() -> dict:
    config = {}
    if CAMERA_CONFIG_PATH.exists() and CAMERA_CONFIG_PATH.stat().st_size > 0:
        try:
            with CAMERA_CONFIG_PATH.open("r", encoding="utf-8") as config_file:
                config = json.load(config_file)
        except json.JSONDecodeError:
            config = {}

    if not isinstance(config, dict):
        config = {}

    return {
        "device_index": config.get("device_index", DEFAULT_CAMERA_CONFIG["device_index"]),
        "fps": config.get("fps", DEFAULT_CAMERA_CONFIG["fps"]),
        "width": config.get("width", DEFAULT_CAMERA_CONFIG["width"]),
        "height": config.get("height", DEFAULT_CAMERA_CONFIG["height"]),
    }


def _get_int_setting(settings: dict, key: str) -> int:
    try:
        return int(settings[key])
    except (TypeError, ValueError):
        raise ValueError(f"Некорректное значение {key} в camera_config.json") from None


def get_camera_settings(
    device_index: int | None = None,
    fps: int | None = None,
) -> dict[str, int]:
    settings = _load_camera_config()
    if device_index is not None:
        settings["device_index"] = device_index
    if fps is not None:
        settings["fps"] = fps

    settings = {
        "device_index": _get_int_setting(settings, "device_index"),
        "fps": _get_int_setting(settings, "fps"),
        "width": _get_int_setting(settings, "width"),
        "height": _get_int_setting(settings, "height"),
    }

    if settings["device_index"] < 0:
        raise ValueError("device_index в camera_config.json должен быть больше или равен 0")
    if settings["fps"] <= 0:
        raise ValueError("fps в camera_config.json должен быть больше 0")
    if settings["width"] <= 0:
        raise ValueError("width в camera_config.json должен быть больше 0")
    if settings["height"] <= 0:
        raise ValueError("height в camera_config.json должен быть больше 0")

    return settings


def apply_camera_settings(camera, settings: dict[str, int]) -> None:
    camera.set(cv2.CAP_PROP_FPS, settings["fps"])
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, settings["width"])
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, settings["height"])


def open_configured_camera(
    device_index: int | None = None,
    fps: int | None = None,
):
    settings = get_camera_settings(device_index=device_index, fps=fps)
    camera = cv2.VideoCapture(settings["device_index"])
    apply_camera_settings(camera, settings)
    return camera, settings


def validate_class_name(class_name: str) -> str:
    class_name = class_name.strip()
    if not class_name:
        raise ValueError("Введите название класса детали")
    if re.search(r'[<>:"/\\|?*]', class_name):
        raise ValueError('Название класса не должно содержать символы <>:"/\\|?*')
    return class_name


def get_dataset_class_dir(class_name: str) -> Path:
    class_name = validate_class_name(class_name)
    return _ensure_dir(DATASET_DIR / class_name)


def _write_image(image_path: Path, frame) -> None:
    success, encoded_image = cv2.imencode(".jpeg", frame)
    if not success:
        raise RuntimeError(f"Cannot encode image for {image_path}")

    image_path.write_bytes(encoded_image.tobytes())


def save_frame_image(frame, class_name: str, is_scanned: bool = False) -> Path:
    if is_scanned:
        captures_dir = _ensure_dir(SCANNED_DIR)
        image_name = f"{_timestamp()}.jpeg"
    else:
        captures_dir = get_dataset_class_dir(class_name)
        image_name = f"{class_name}_{_timestamp()}.jpeg"

    image_path = captures_dir / image_name
    _write_image(image_path, frame)

    return image_path


def save_camera_image(
    device_index: int | None = None,
    fps: int | None = None,
    is_scanned: bool = True,
    dataset_class_name: str | None = None,
) -> Path:
    class_name = dataset_class_name if dataset_class_name is not None else "NEW_CLASS"
    camera, camera_settings = open_configured_camera(device_index=device_index, fps=fps)

    try:
        if not camera.isOpened():
            raise RuntimeError(f"Cannot open camera with device index {camera_settings['device_index']}")

        success, frame = camera.read()
        if not success:
            raise RuntimeError("Cannot read frame from camera")

        return save_frame_image(frame, class_name=class_name, is_scanned=is_scanned)
    finally:
        camera.release()


def save_camera_image_stream(
    device_index: int | None = None,
    fps: int | None = None,
    dataset_class_name: str | None = None,
    duration_seconds: float | None = None,
    max_images: int | None = None,
) -> list[Path]:
    class_name = dataset_class_name if dataset_class_name is not None else "NEW_CLASS"
    camera, camera_settings = open_configured_camera(device_index=device_index, fps=fps)

    saved_paths: list[Path] = []
    interval_seconds = 1 / camera_settings["fps"]
    started_at = monotonic()

    try:
        if not camera.isOpened():
            raise RuntimeError(f"Cannot open camera with device index {camera_settings['device_index']}")

        while True:
            if duration_seconds is not None and monotonic() - started_at >= duration_seconds:
                break
            if max_images is not None and len(saved_paths) >= max_images:
                break

            loop_started_at = monotonic()
            success, frame = camera.read()
            if not success:
                raise RuntimeError("Cannot read frame from camera")

            saved_paths.append(save_frame_image(frame, class_name=class_name, is_scanned=False))

            elapsed = monotonic() - loop_started_at
            sleep(max(0, interval_seconds - elapsed))
    finally:
        camera.release()

    return saved_paths
