import json
import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_DIR = PROJECT_ROOT / "model"
MODEL_MANIFEST_FILE_NAME = "manifest.json"
MODEL_WEIGHTS_FILE_NAME = "model.pt"
MODEL_MANIFEST_TIMEOUT_SECONDS = 30
MODEL_DOWNLOAD_TIMEOUT_SECONDS = 120


class ModelUpdateError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelUpdateResult:
    status: str
    version: str
    local_version: str | None = None
    remote_version: str | None = None


def update_model_files(
    api_url: str,
    api_key: str,
    model_dir: Path | str = DEFAULT_MODEL_DIR,
) -> ModelUpdateResult:
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    if not has_local_model_files(model_dir):
        version = download_and_extract_latest_model(api_url, api_key, model_dir)
        return ModelUpdateResult(status="downloaded", version=version)

    try:
        local_manifest = read_json_file(model_dir / MODEL_MANIFEST_FILE_NAME)
        local_version = read_manifest_version(local_manifest, "local manifest.json")
    except (OSError, json.JSONDecodeError, ValueError):
        version = download_and_extract_latest_model(api_url, api_key, model_dir)
        return ModelUpdateResult(status="recovered", version=version)

    remote_manifest = request_model_manifest(api_url, api_key)
    remote_version = read_manifest_version(remote_manifest, "remote manifest.json")

    if local_version == remote_version:
        return ModelUpdateResult(status="current", version=local_version)

    version = download_and_extract_latest_model(api_url, api_key, model_dir)
    return ModelUpdateResult(
        status="updated",
        version=version,
        local_version=local_version,
        remote_version=remote_version,
    )


def has_local_model_files(model_dir: Path) -> bool:
    return (
        (model_dir / MODEL_MANIFEST_FILE_NAME).is_file()
        and (model_dir / MODEL_WEIGHTS_FILE_NAME).is_file()
    )


def request_model_manifest(api_url: str, api_key: str) -> dict:
    try:
        response = requests.get(
            build_model_manifest_url(api_url),
            headers={"X-API-Key": api_key},
            timeout=MODEL_MANIFEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        raise ModelUpdateError(f"Не удалось получить manifest.json: {error}") from error


def download_and_extract_latest_model(api_url: str, api_key: str, model_dir: Path) -> str:
    archive_path = download_latest_model_archive(api_url, api_key)
    try:
        extract_model_archive(archive_path, model_dir)
    finally:
        archive_path.unlink(missing_ok=True)

    manifest = read_json_file(model_dir / MODEL_MANIFEST_FILE_NAME)
    return read_manifest_version(manifest, "manifest.json")


def download_latest_model_archive(api_url: str, api_key: str) -> Path:
    temp_archive_path = None

    try:
        with tempfile.NamedTemporaryFile(
            prefix="model-latest-",
            suffix=".zip",
            delete=False,
        ) as temp_archive:
            temp_archive_path = Path(temp_archive.name)

        with requests.get(
            build_model_latest_url(api_url),
            headers={"X-API-Key": api_key},
            stream=True,
            timeout=MODEL_DOWNLOAD_TIMEOUT_SECONDS,
        ) as response:
            response.raise_for_status()
            with temp_archive_path.open("wb") as temp_archive:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        temp_archive.write(chunk)

        return temp_archive_path
    except requests.RequestException as error:
        if temp_archive_path is not None:
            temp_archive_path.unlink(missing_ok=True)
        raise ModelUpdateError(f"Не удалось скачать модель: {error}") from error
    except OSError:
        if temp_archive_path is not None:
            temp_archive_path.unlink(missing_ok=True)
        raise


def extract_model_archive(archive_path: Path, model_dir: Path) -> None:
    try:
        with zipfile.ZipFile(archive_path) as archive:
            manifest_member = find_zip_member(archive, MODEL_MANIFEST_FILE_NAME)
            model_member = find_zip_member(archive, MODEL_WEIGHTS_FILE_NAME)

            with tempfile.TemporaryDirectory(dir=model_dir) as temp_dir:
                temp_dir = Path(temp_dir)
                temp_manifest_path = temp_dir / MODEL_MANIFEST_FILE_NAME
                temp_model_path = temp_dir / MODEL_WEIGHTS_FILE_NAME

                write_zip_member(archive, manifest_member, temp_manifest_path)
                write_zip_member(archive, model_member, temp_model_path)

                temp_manifest_path.replace(model_dir / MODEL_MANIFEST_FILE_NAME)
                temp_model_path.replace(model_dir / MODEL_WEIGHTS_FILE_NAME)
    except zipfile.BadZipFile as error:
        raise ModelUpdateError(f"Некорректный архив модели: {archive_path}") from error


def find_zip_member(archive: zipfile.ZipFile, file_name: str) -> zipfile.ZipInfo:
    for member in archive.infolist():
        if member.is_dir():
            continue
        member_name = member.filename.replace("\\", "/").rstrip("/").split("/")[-1]
        if member_name == file_name:
            return member

    raise ModelUpdateError(f"В архиве не найден {file_name}")


def write_zip_member(archive: zipfile.ZipFile, member: zipfile.ZipInfo, target_path: Path) -> None:
    with archive.open(member) as source:
        with target_path.open("wb") as target:
            shutil.copyfileobj(source, target)


def read_json_file(file_path: Path) -> dict:
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def read_manifest_version(manifest: dict, manifest_name: str) -> str:
    if not isinstance(manifest, dict):
        raise ValueError(f"{manifest_name}: ожидался JSON-объект")

    version = manifest.get("version")
    if version in (None, ""):
        raise ValueError(f"{manifest_name}: version не найден")

    return str(version)


def build_model_manifest_url(api_url: str) -> str:
    return f"{normalize_api_url(api_url)}/model/manifest"


def build_model_latest_url(api_url: str) -> str:
    return f"{normalize_api_url(api_url)}/model/latest"


def normalize_api_url(api_url: str) -> str:
    api_url = api_url.strip().rstrip("/")
    if not api_url:
        raise ModelUpdateError("API_URL не должен быть пустым")
    if not re.match(r"^https?://", api_url):
        api_url = f"http://{api_url}"

    return api_url
