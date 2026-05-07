from datetime import datetime
from pathlib import Path
from time import monotonic, sleep
import re

import cv2


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CAPTURES_DIR = PROJECT_ROOT / "captures"
SCANNED_DIR = CAPTURES_DIR / "scanned"
DATASET_DIR = CAPTURES_DIR / "dataset"


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")


def _ensure_dir(target_dir: Path | str) -> Path:
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


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
    device_index: int = 0,
    fps: int = 1,
    is_scanned: bool = True,
    dataset_class_name: str | None = None,
) -> Path:
    class_name = dataset_class_name if dataset_class_name is not None else "NEW_CLASS"

    camera = cv2.VideoCapture(device_index)
    camera.set(cv2.CAP_PROP_FPS, fps)

    try:
        if not camera.isOpened():
            raise RuntimeError(f"Cannot open camera with device index {device_index}")

        success, frame = camera.read()
        if not success:
            raise RuntimeError("Cannot read frame from camera")

        return save_frame_image(frame, class_name=class_name, is_scanned=is_scanned)
    finally:
        camera.release()


def save_camera_image_stream(
    device_index: int = 0,
    fps: int = 1,
    dataset_class_name: str | None = None,
    duration_seconds: float | None = None,
    max_images: int | None = None,
) -> list[Path]:
    class_name = dataset_class_name if dataset_class_name is not None else "NEW_CLASS"
    camera = cv2.VideoCapture(device_index)
    camera.set(cv2.CAP_PROP_FPS, fps)

    saved_paths: list[Path] = []
    interval_seconds = 1 / fps
    started_at = monotonic()

    try:
        if not camera.isOpened():
            raise RuntimeError(f"Cannot open camera with device index {device_index}")

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
