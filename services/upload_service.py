import json
import re
import tarfile
from pathlib import Path
from typing import Iterable

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_DIR = PROJECT_ROOT / "captures" / "dataset"
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_METADATA_PATH = DEFAULT_DATASET_DIR / "metadata.json"
INVALID_CLASS_NAME_PATTERN = re.compile(r'[<>:"/\\|?*]')
UPLOAD_REQUEST_TIMEOUT_SECONDS = 30


class UploadArchiveError(RuntimeError):
    pass


class UploadRequestError(RuntimeError):
    pass


def create_class_archives(
    class_names: Iterable[str],
    dataset_dir: Path | str = DEFAULT_DATASET_DIR,
) -> list[Path]:
    return [
        create_class_archive(class_name, dataset_dir=dataset_dir)
        for class_name in class_names
    ]


def create_class_archive(
    class_name: str,
    dataset_dir: Path | str = DEFAULT_DATASET_DIR,
) -> Path:
    dataset_dir = Path(dataset_dir).resolve()
    class_name = validate_class_name(class_name)
    class_dir = resolve_class_dir(dataset_dir, class_name)
    if not class_dir.is_dir():
        raise FileNotFoundError(f"Папка класса не найдена: {class_dir}")

    archive_path = dataset_dir / f"{class_name}.tar.gz"

    try:
        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(class_dir, arcname=class_name)
    except tarfile.TarError as error:
        raise UploadArchiveError(f"Не удалось создать архив {archive_path}") from error

    return archive_path


def upload_project_from_metadata(
    metadata_path: Path | str = DEFAULT_METADATA_PATH,
    env_path: Path | str = DEFAULT_ENV_PATH,
    timeout_seconds: int = UPLOAD_REQUEST_TIMEOUT_SECONDS,
) -> requests.Response:
    metadata = read_metadata(metadata_path)
    api_url = read_env_value("API_URL", env_path)
    api_key = read_env_value("API_KEY", env_path)
    if not api_url:
        raise UploadRequestError("API_URL не найден в .env")
    if not api_key:
        raise UploadRequestError("API_KEY не найден в .env")

    payload = {
        "project_name": read_dataset_project_name(metadata),
        "classes": read_metadata_class_names(metadata),
    }

    try:
        response = requests.post(
            build_projects_url(api_url),
            headers={
                "Content-Type": "application/json",
                "X-API-Key": api_key,
            },
            json=payload,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise UploadRequestError(f"Не удалось создать проект: {error}") from error

    return response


def read_metadata(metadata_path: Path | str) -> dict:
    metadata_path = Path(metadata_path)
    if not metadata_path.exists() or metadata_path.stat().st_size == 0:
        raise FileNotFoundError(f"metadata.json не найден: {metadata_path}")

    with metadata_path.open("r", encoding="utf-8") as metadata_file:
        metadata = json.load(metadata_file)

    if not isinstance(metadata, dict):
        raise ValueError("metadata.json должен содержать JSON-объект")

    return metadata


def read_dataset_project_name(metadata: dict) -> str:
    dataset_update = metadata.get("dataset_update", {})
    if not isinstance(dataset_update, dict):
        raise ValueError("metadata.json: dataset_update должен быть объектом")

    project_name = str(dataset_update.get("name", "")).strip()
    if not project_name:
        raise ValueError("metadata.json: dataset_update.name не заполнен")

    return project_name


def read_metadata_class_names(metadata: dict) -> list[str]:
    classes = metadata.get("classes", {})
    if not isinstance(classes, dict):
        raise ValueError("metadata.json: classes должен быть объектом")

    class_names = [str(class_name) for class_name in classes.keys()]
    if not class_names:
        raise ValueError("metadata.json: classes пустой")

    return class_names


def build_projects_url(api_url: str) -> str:
    api_url = api_url.strip().rstrip("/")
    if not api_url:
        raise UploadRequestError("API_URL не должен быть пустым")
    if not re.match(r"^https?://", api_url):
        api_url = f"http://{api_url}"

    return f"{api_url}/projects"


def read_env_value(target_key: str, env_path: Path | str = DEFAULT_ENV_PATH) -> str | None:
    env_path = Path(env_path)
    if not env_path.exists() or env_path.stat().st_size == 0:
        return None

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue
        if stripped_line.startswith("export "):
            stripped_line = stripped_line[len("export ") :].lstrip()
        if "=" not in stripped_line:
            continue

        key, value = stripped_line.split("=", 1)
        if key.strip() == target_key:
            return parse_env_value(value.strip())

    return None


def parse_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ['"', "'"]:
        value = value[1:-1]

    return value.replace('\\"', '"').replace("\\\\", "\\")


def validate_class_name(class_name: str) -> str:
    class_name = str(class_name).strip()
    if not class_name:
        raise ValueError("Название класса не должно быть пустым")
    if class_name in {".", ".."}:
        raise ValueError("Некорректное название класса")
    if INVALID_CLASS_NAME_PATTERN.search(class_name):
        raise ValueError('Название класса не должно содержать символы <>:"/\\|?*')

    return class_name


def resolve_class_dir(dataset_dir: Path, class_name: str) -> Path:
    class_dir = (dataset_dir / class_name).resolve()
    try:
        class_dir.relative_to(dataset_dir)
    except ValueError:
        raise ValueError("Папка класса должна находиться внутри папки датасета") from None

    return class_dir
