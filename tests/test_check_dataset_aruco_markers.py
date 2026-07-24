from pathlib import Path

import numpy as np

from tests import check_dataset_aruco_markers


def create_dataset_image(dataset_dir: Path, class_name: str, file_name: str) -> Path:
    images_dir = dataset_dir / class_name / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    image_path = images_dir / file_name
    image_path.write_bytes(b"image")
    return image_path


def test_find_dataset_images_returns_only_jpeg_files_in_class_images(tmp_path):
    first_image = create_dataset_image(tmp_path, "class-a", "first.jpeg")
    second_image = create_dataset_image(tmp_path, "class-b", "second.jpeg")
    create_dataset_image(tmp_path, "class-a", "ignored.jpg")
    (tmp_path / "root.jpeg").write_bytes(b"image")

    assert check_dataset_aruco_markers.find_dataset_images(tmp_path) == [
        first_image,
        second_image,
    ]


def test_find_invalid_images_reports_missing_markers(tmp_path, monkeypatch):
    valid_image = create_dataset_image(tmp_path, "class-a", "valid.jpeg")
    invalid_image = create_dataset_image(tmp_path, "class-a", "invalid.jpeg")
    images = {
        valid_image: np.zeros((1, 1, 3), dtype=np.uint8),
        invalid_image: np.ones((1, 1, 3), dtype=np.uint8),
    }

    monkeypatch.setattr(
        check_dataset_aruco_markers,
        "read_image",
        images.__getitem__,
    )

    def detect_markers(image, detector):
        if image[0, 0, 0] == 1:
            raise RuntimeError("Не найдены обязательные Aruco-маркеры: [3]")

    monkeypatch.setattr(
        check_dataset_aruco_markers,
        "detect_aruco_marker_rectangle",
        detect_markers,
    )

    assert check_dataset_aruco_markers.find_invalid_images(
        tmp_path,
        detector=object(),
    ) == [
        (
            invalid_image,
            "Не найдены обязательные Aruco-маркеры: [3]",
        )
    ]
