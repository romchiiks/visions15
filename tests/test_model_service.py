import json
import zipfile

from services.model_service import (
    DEFAULT_MODEL_WEIGHTS_PATH,
    MODEL_MANIFEST_FILE_NAME,
    MODEL_WEIGHTS_FILE_NAME,
    extract_model_archive,
    has_local_model_files,
)


def test_default_model_weights_path_points_to_local_yolo_gpio_server():
    assert str(DEFAULT_MODEL_WEIGHTS_PATH) == "/mnt/IR_AI/local-yolo-gpio-server/model/model.pt"


def test_extract_model_archive_keeps_manifest_and_weights_in_separate_paths(tmp_path):
    archive_path = tmp_path / "latest.zip"
    model_dir = tmp_path / "local-model"
    model_weights_path = tmp_path / "external-model" / MODEL_WEIGHTS_FILE_NAME

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(MODEL_MANIFEST_FILE_NAME, json.dumps({"version": "2026.07.17"}))
        archive.writestr(MODEL_WEIGHTS_FILE_NAME, b"weights")

    extract_model_archive(archive_path, model_dir, model_weights_path)

    assert json.loads((model_dir / MODEL_MANIFEST_FILE_NAME).read_text(encoding="utf-8")) == {
        "version": "2026.07.17"
    }
    assert model_weights_path.read_bytes() == b"weights"
    assert not (model_dir / MODEL_WEIGHTS_FILE_NAME).exists()
    assert has_local_model_files(model_dir, model_weights_path)
