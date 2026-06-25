import json
import os
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from time import monotonic, sleep
import re
import sys

import cv2

from services.perspective_warp_service import apply_perspective_warp


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CAMERA_CONFIG_PATH = PROJECT_ROOT / "camera_config.json"
CAPTURES_DIR = PROJECT_ROOT / "captures"
SCANNED_DIR = CAPTURES_DIR / "scanned"
DATASET_DIR = CAPTURES_DIR / "dataset"
DATASET_METADATA_PATH = DATASET_DIR / "metadata.json"
DATASET_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
DEFAULT_CAMERA_CONFIG = {
    "device_index": 0,
    "mjpg": False,
    "fps": 1,
    "width": 640,
    "height": 480,
    "capture_interval": 1,
    "scan_warmup_seconds": 2.0,
    "scan_max_wait_seconds": 5.0,
}


@contextmanager
def _suppress_native_stderr():
    try:
        stderr_fd = sys.stderr.fileno()
    except (AttributeError, OSError, ValueError):
        yield
        return

    saved_stderr_fd = None
    devnull_fd = None
    try:
        saved_stderr_fd = os.dup(stderr_fd)
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull_fd, stderr_fd)
        yield
    finally:
        if saved_stderr_fd is not None:
            os.dup2(saved_stderr_fd, stderr_fd)
            os.close(saved_stderr_fd)
        if devnull_fd is not None:
            os.close(devnull_fd)


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")


def _dataset_date() -> str:
    return datetime.now().strftime("%d-%m-%Y")


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
        "mjpg": config.get("mjpg", DEFAULT_CAMERA_CONFIG["mjpg"]),
        "fps": config.get("fps", DEFAULT_CAMERA_CONFIG["fps"]),
        "width": config.get("width", DEFAULT_CAMERA_CONFIG["width"]),
        "height": config.get("height", DEFAULT_CAMERA_CONFIG["height"]),
        "capture_interval": config.get("capture_interval", DEFAULT_CAMERA_CONFIG["capture_interval"]),
        "scan_warmup_seconds": config.get(
            "scan_warmup_seconds",
            DEFAULT_CAMERA_CONFIG["scan_warmup_seconds"],
        ),
        "scan_max_wait_seconds": config.get(
            "scan_max_wait_seconds",
            DEFAULT_CAMERA_CONFIG["scan_max_wait_seconds"],
        ),
    }


def _get_int_setting(settings: dict, key: str) -> int:
    try:
        return int(settings[key])
    except (TypeError, ValueError):
        raise ValueError(f"Некорректное значение {key} в camera_config.json") from None


def _get_float_setting(settings: dict, key: str) -> float:
    try:
        return float(settings[key])
    except (TypeError, ValueError):
        raise ValueError(f"Некорректное значение {key} в camera_config.json") from None


def _get_bool_setting(settings: dict, key: str) -> bool:
    value = settings[key]
    if not isinstance(value, bool):
        raise ValueError(f"{key} в camera_config.json должен быть true или false")

    return value


def get_camera_settings(
    device_index: int | None = None,
    fps: int | None = None,
) -> dict[str, bool | int | float]:
    settings = _load_camera_config()
    if device_index is not None:
        settings["device_index"] = device_index
    if fps is not None:
        settings["fps"] = fps

    settings = {
        "device_index": _get_int_setting(settings, "device_index"),
        "mjpg": _get_bool_setting(settings, "mjpg"),
        "fps": _get_int_setting(settings, "fps"),
        "width": _get_int_setting(settings, "width"),
        "height": _get_int_setting(settings, "height"),
        "capture_interval": _get_int_setting(settings, "capture_interval"),
        "scan_warmup_seconds": _get_float_setting(settings, "scan_warmup_seconds"),
        "scan_max_wait_seconds": _get_float_setting(settings, "scan_max_wait_seconds"),
    }

    if settings["device_index"] < 0:
        raise ValueError("device_index в camera_config.json должен быть больше или равен 0")
    if settings["fps"] <= 0:
        raise ValueError("fps в camera_config.json должен быть больше 0")
    if settings["width"] <= 0:
        raise ValueError("width в camera_config.json должен быть больше 0")
    if settings["height"] <= 0:
        raise ValueError("height в camera_config.json должен быть больше 0")
    if settings["capture_interval"] <= 0:
        raise ValueError("capture_interval в camera_config.json должен быть больше 0")
    if settings["scan_warmup_seconds"] < 0:
        raise ValueError("scan_warmup_seconds в camera_config.json должен быть больше или равен 0")
    if settings["scan_max_wait_seconds"] <= 0:
        raise ValueError("scan_max_wait_seconds в camera_config.json должен быть больше 0")

    return settings


def apply_camera_settings(camera, settings: dict[str, bool | int | float]) -> None:
    if settings["mjpg"]:
        camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

    camera.set(cv2.CAP_PROP_FPS, settings["fps"])
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, settings["width"])
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, settings["height"])
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)


def open_configured_camera(
    device_index: int | None = None,
    fps: int | None = None,
):
    settings = get_camera_settings(device_index=device_index, fps=fps)
    with _suppress_native_stderr():
        camera = cv2.VideoCapture(settings["device_index"])
        if camera.isOpened():
            apply_camera_settings(camera, settings)
    return camera, settings


def release_camera(camera) -> None:
    with _suppress_native_stderr():
        camera.release()


def validate_class_name(class_name: str) -> str:
    class_name = class_name.strip()
    if not class_name:
        raise ValueError("Введите название класса детали")
    if re.search(r'[<>:"/\\|?*]', class_name):
        raise ValueError('Название класса не должно содержать символы <>:"/\\|?*')
    return class_name


def get_dataset_class_dir(class_name: str) -> Path:
    class_name = validate_class_name(class_name)
    class_dir = _ensure_dir(DATASET_DIR / class_name)
    _ensure_dir(class_dir / "images")
    return class_dir


def get_dataset_class_images_dir(class_name: str) -> Path:
    return _ensure_dir(get_dataset_class_dir(class_name) / "images")


def get_dataset_image_paths(class_name: str) -> list[Path]:
    class_name = validate_class_name(class_name)
    images_dir = DATASET_DIR / class_name / "images"
    if not images_dir.exists():
        return []

    return sorted(
        image_path
        for image_path in images_dir.iterdir()
        if image_path.is_file() and image_path.suffix.lower() in DATASET_IMAGE_EXTENSIONS
    )


def count_dataset_images(class_name: str) -> int:
    return len(get_dataset_image_paths(class_name))


def _next_dataset_image_path(class_name: str) -> Path:
    images_dir = get_dataset_class_images_dir(class_name)
    next_index = count_dataset_images(class_name) + 1

    while True:
        image_path = images_dir / f"{class_name}_{next_index:03d}.jpeg"
        if not image_path.exists():
            return image_path

        next_index += 1


def write_dataset_metadata(details: dict, dataset_name: str | None = None) -> Path:
    _ensure_dir(DATASET_DIR)
    if dataset_name is None:
        dataset_name = f"dataset-{_dataset_date()}"

    classes = {}

    for class_name, article in details.items():
        class_name = validate_class_name(str(class_name))
        images_count = count_dataset_images(class_name)
        if images_count == 0:
            continue

        classes[class_name] = {
            "article": str(article),
            "directory": class_name,
            "images_count": images_count,
        }

    metadata = {
        "schema_version": "1.0",
        "dataset_update": {
            "name": dataset_name,
        },
        "classes": classes,
    }

    with DATASET_METADATA_PATH.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, ensure_ascii=False, indent=2)
        metadata_file.write("\n")

    return DATASET_METADATA_PATH


def remove_empty_dataset_class_dir(class_name: str) -> None:
    class_name = validate_class_name(class_name)
    class_dir = DATASET_DIR / class_name
    images_dir = class_dir / "images"

    if images_dir.exists():
        try:
            images_dir.rmdir()
        except OSError:
            pass

    if class_dir.exists():
        try:
            class_dir.rmdir()
        except OSError:
            pass


def _write_image(image_path: Path, frame) -> None:
    success, encoded_image = cv2.imencode(".jpeg", frame)
    if not success:
        raise RuntimeError(f"Cannot encode image for {image_path}")

    image_path.write_bytes(encoded_image.tobytes())


def _is_green_placeholder_frame(frame) -> bool:
    channel_means = frame.mean(axis=(0, 1))
    channel_stds = frame.std(axis=(0, 1))
    blue_mean, green_mean, red_mean = channel_means

    is_solid_color = all(channel_std < 8 for channel_std in channel_stds)
    is_green_dominant = green_mean > 80 and green_mean > blue_mean * 1.5 and green_mean > red_mean * 1.5

    return bool(is_solid_color and is_green_dominant)


def _read_stable_scan_frame(camera, settings: dict[str, bool | int | float]):
    warmup_seconds = settings["scan_warmup_seconds"]
    max_wait_seconds = settings["scan_max_wait_seconds"]
    started_at = monotonic()
    last_frame = None

    while True:
        success, frame = camera.read()
        if not success:
            raise RuntimeError("Cannot read frame from camera")

        last_frame = frame
        elapsed = monotonic() - started_at
        if elapsed >= warmup_seconds and not _is_green_placeholder_frame(frame):
            return frame
        if elapsed >= max_wait_seconds:
            if _is_green_placeholder_frame(last_frame):
                raise RuntimeError("Камера не успела подготовить изображение: получен зеленый кадр")
            return last_frame

        sleep(0.05)


def save_frame_image(frame, class_name: str, is_scanned: bool = False) -> Path:
    if is_scanned:
        captures_dir = _ensure_dir(SCANNED_DIR)
        image_name = f"{_timestamp()}.jpeg"
        image_path = captures_dir / image_name
    else:
        image_path = _next_dataset_image_path(class_name)

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

        if is_scanned:
            frame = _read_stable_scan_frame(camera, camera_settings)
            frame = apply_perspective_warp(frame)
        else:
            success, frame = camera.read()
            if not success:
                raise RuntimeError("Cannot read frame from camera")

        return save_frame_image(frame, class_name=class_name, is_scanned=is_scanned)
    finally:
        release_camera(camera)


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
    interval_seconds = camera_settings["capture_interval"]
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
        release_camera(camera)

    return saved_paths
