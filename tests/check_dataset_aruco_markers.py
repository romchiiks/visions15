import argparse
import json
from pathlib import Path
import sys

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.perspective_warp_service import (
    create_aruco_detector,
    detect_aruco_marker_rectangle,
)


DEFAULT_DATASET_DIR = PROJECT_ROOT / "captures" / "dataset"
DATASET_IMAGE_PATTERN = "*/images/*.jpeg"
DATASET_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
METADATA_FILE_NAME = "metadata.json"


def find_dataset_images(dataset_dir: Path) -> list[Path]:
    return sorted(dataset_dir.glob(DATASET_IMAGE_PATTERN))


def read_image(image_path: Path):
    encoded_image = np.fromfile(image_path, dtype=np.uint8)
    return cv2.imdecode(encoded_image, cv2.IMREAD_COLOR)


def find_invalid_images(
    dataset_dir: Path,
    detector=None,
) -> list[tuple[Path, str]]:
    if detector is None:
        detector = create_aruco_detector()

    invalid_images = []
    for image_path in find_dataset_images(dataset_dir):
        image = read_image(image_path)
        if image is None:
            invalid_images.append((image_path, "изображение не удалось прочитать"))
            continue

        try:
            detect_aruco_marker_rectangle(image, detector=detector)
        except RuntimeError as error:
            invalid_images.append((image_path, str(error)))

    return invalid_images


def confirm_deletion() -> bool:
    while True:
        answer = input("Удалить проблемные изображения? (y/n): ").strip().lower()
        if answer == "y":
            return True
        if answer == "n":
            return False

        print("Введите y или n.")


def delete_invalid_images(
    invalid_images: list[tuple[Path, str]],
) -> list[tuple[Path, str]]:
    deletion_errors = []
    for image_path, _ in invalid_images:
        try:
            image_path.unlink()
        except OSError as error:
            deletion_errors.append((image_path, str(error)))

    return deletion_errors


def read_metadata(dataset_dir: Path) -> dict:
    metadata_path = dataset_dir / METADATA_FILE_NAME
    with metadata_path.open("r", encoding="utf-8") as metadata_file:
        metadata = json.load(metadata_file)

    if not isinstance(metadata, dict) or not isinstance(metadata.get("classes"), dict):
        raise ValueError("metadata.json не содержит объект classes")

    return metadata


def update_metadata_image_counts(dataset_dir: Path, metadata: dict) -> Path:
    for class_name, class_info in metadata["classes"].items():
        if not isinstance(class_info, dict):
            raise ValueError(f"Некорректные metadata для класса {class_name}")

        directory = class_info.get("directory")
        if not isinstance(directory, str) or not directory.strip():
            raise ValueError(f"Не указан directory для класса {class_name}")

        images_dir = dataset_dir / directory / "images"
        class_info["images_count"] = sum(
            1
            for image_path in images_dir.iterdir()
            if image_path.is_file()
            and image_path.suffix.lower() in DATASET_IMAGE_EXTENSIONS
        ) if images_dir.is_dir() else 0

    metadata_path = dataset_dir / METADATA_FILE_NAME
    temp_metadata_path = metadata_path.with_name(f".{metadata_path.name}.tmp")
    try:
        with temp_metadata_path.open("w", encoding="utf-8") as metadata_file:
            json.dump(metadata, metadata_file, ensure_ascii=False, indent=2)
            metadata_file.write("\n")
        temp_metadata_path.replace(metadata_path)
    except Exception:
        temp_metadata_path.unlink(missing_ok=True)
        raise

    return metadata_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Проверка ArUco-маркеров в несжатых изображениях датасета.",
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=DEFAULT_DATASET_DIR,
        help="Путь к captures/dataset.",
    )
    args = parser.parse_args()

    dataset_dir = args.dataset_dir.resolve()
    image_paths = find_dataset_images(dataset_dir)
    if not image_paths:
        print(f"Изображения не найдены: {dataset_dir / DATASET_IMAGE_PATTERN}")
        return 0

    invalid_images = find_invalid_images(dataset_dir)
    for image_path, reason in invalid_images:
        print(f"[ПРОПУЩЕН] {image_path}: {reason}")

    valid_count = len(image_paths) - len(invalid_images)
    print(
        f"Проверено: {len(image_paths)}; "
        f"с маркерами: {valid_count}; "
        f"проблемных: {len(invalid_images)}"
    )

    if not invalid_images:
        return 0

    if not confirm_deletion():
        print("Проблемные изображения не удалены.")
        return 1

    try:
        metadata = read_metadata(dataset_dir)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"[ОШИБКА METADATA] Проблемные изображения не удалены: {error}")
        return 1

    deletion_errors = delete_invalid_images(invalid_images)
    for image_path, reason in deletion_errors:
        print(f"[ОШИБКА УДАЛЕНИЯ] {image_path}: {reason}")

    deleted_count = len(invalid_images) - len(deletion_errors)
    print(f"Удалено проблемных изображений: {deleted_count}")

    try:
        metadata_path = update_metadata_image_counts(dataset_dir, metadata)
        print(f"Обновлён metadata.json: {metadata_path}")
    except (OSError, ValueError) as error:
        print(f"[ОШИБКА METADATA] Не удалось обновить metadata.json: {error}")
        return 1

    return 1 if deletion_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
