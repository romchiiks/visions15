import io
import json
import re
import shutil
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_DIR = PROJECT_ROOT / "captures" / "dataset"
DEFAULT_BACKUP_DATASET_DIR = PROJECT_ROOT / "captures" / "backup_dataset"
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_METADATA_PATH = DEFAULT_DATASET_DIR / "metadata.json"
INVALID_CLASS_NAME_PATTERN = re.compile(r'[<>:"/\\|?*]')
UPLOAD_REQUEST_TIMEOUT_SECONDS = 30


class UploadArchiveError(RuntimeError):
    pass


class UploadRequestError(RuntimeError):
    pass


@dataclass(frozen=True)
class DatasetUpdateArchive:
    path: Path
    metadata: dict
    metadata_path: Path
    remaining_metadata: dict
    backup_class_dirs: list[tuple[Path, Path]]


def upload_selected_classes(
    class_names: Iterable[str],
    dataset_dir: Path | str = DEFAULT_DATASET_DIR,
    backup_dataset_dir: Path | str | None = None,
    env_path: Path | str = DEFAULT_ENV_PATH,
    timeout_seconds: int = UPLOAD_REQUEST_TIMEOUT_SECONDS,
) -> tuple[list[Path], requests.Response]:
    archive = create_dataset_update_archive_result(
        class_names,
        dataset_dir=dataset_dir,
        backup_dataset_dir=backup_dataset_dir,
        finalize_dataset=False,
    )
    response = upload_archive(
        archive.path,
        env_path=env_path,
        timeout_seconds=timeout_seconds,
    )
    finalize_dataset_update_archive(archive)

    return [archive.path], response


def create_class_archives(
    class_names: Iterable[str],
    dataset_dir: Path | str = DEFAULT_DATASET_DIR,
    backup_dataset_dir: Path | str | None = None,
) -> list[Path]:
    return [
        create_dataset_update_archive(
            class_names,
            dataset_dir=dataset_dir,
            backup_dataset_dir=backup_dataset_dir,
        )
    ]


def create_dataset_update_archive(
    class_names: Iterable[str],
    dataset_dir: Path | str = DEFAULT_DATASET_DIR,
    backup_dataset_dir: Path | str | None = None,
) -> Path:
    return create_dataset_update_archive_result(
        class_names,
        dataset_dir=dataset_dir,
        backup_dataset_dir=backup_dataset_dir,
    ).path


def create_dataset_update_archive_result(
    class_names: Iterable[str],
    dataset_dir: Path | str = DEFAULT_DATASET_DIR,
    backup_dataset_dir: Path | str | None = None,
    finalize_dataset: bool = True,
) -> DatasetUpdateArchive:
    dataset_dir = Path(dataset_dir).resolve()
    backup_dataset_dir = resolve_backup_dataset_dir(dataset_dir, backup_dataset_dir)
    metadata_path = dataset_dir / "metadata.json"
    metadata = read_metadata(metadata_path)
    dataset_update_name = validate_dataset_update_name(read_dataset_project_name(metadata))
    selected_class_names = unique_class_names(class_names)
    if not selected_class_names:
        raise ValueError("Классы не выбраны")

    metadata_classes = read_metadata_classes(metadata)
    missing_class_names = [
        class_name
        for class_name in selected_class_names
        if class_name not in metadata_classes
    ]
    if missing_class_names:
        raise ValueError(
            "metadata.json: классы не найдены: "
            + ", ".join(missing_class_names)
        )

    class_dirs = []
    for class_name in selected_class_names:
        class_dir = resolve_class_dir(dataset_dir, class_name)
        if not class_dir.is_dir():
            raise FileNotFoundError(f"Папка класса не найдена: {class_dir}")
        class_dirs.append((class_name, class_dir))

    archive_path = dataset_dir / f"{dataset_update_name}.tar.gz"
    archive_metadata = metadata_with_classes(metadata, selected_class_names)
    remaining_metadata = metadata_without_classes(metadata, selected_class_names)
    backup_class_dirs = prepare_backup_class_dirs(class_dirs, backup_dataset_dir)

    try:
        with tarfile.open(archive_path, "w:gz") as archive:
            add_metadata_to_archive(
                archive,
                archive_metadata,
                f"{dataset_update_name}/metadata.json",
            )
            for class_name, class_dir in class_dirs:
                archive.add(class_dir, arcname=f"{dataset_update_name}/{class_name}")
    except tarfile.TarError as error:
        raise UploadArchiveError(f"Не удалось создать архив {archive_path}") from error

    archive = DatasetUpdateArchive(
        path=archive_path,
        metadata=archive_metadata,
        metadata_path=metadata_path,
        remaining_metadata=remaining_metadata,
        backup_class_dirs=backup_class_dirs,
    )
    if finalize_dataset:
        finalize_dataset_update_archive(archive)

    return archive


def finalize_dataset_update_archive(archive: DatasetUpdateArchive) -> None:
    move_class_dirs_to_backup(archive.backup_class_dirs)
    write_metadata(archive.metadata_path, archive.remaining_metadata)


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
    class_names: Iterable[str] | None = None,
) -> requests.Response:
    metadata = read_metadata(metadata_path)
    return upload_project(
        metadata,
        env_path=env_path,
        timeout_seconds=timeout_seconds,
        class_names=class_names,
    )


def upload_project(
    metadata: dict,
    env_path: Path | str = DEFAULT_ENV_PATH,
    timeout_seconds: int = UPLOAD_REQUEST_TIMEOUT_SECONDS,
    class_names: Iterable[str] | None = None,
) -> requests.Response:
    api_url = read_env_value("API_URL", env_path)
    api_key = read_env_value("API_KEY", env_path)
    if not api_url:
        raise UploadRequestError("API_URL не найден в .env")
    if not api_key:
        raise UploadRequestError("API_KEY не найден в .env")

    payload = {
        "project_name": read_dataset_project_name(metadata),
        "classes": read_project_class_names(metadata, class_names),
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


def upload_archive(
    archive_path: Path | str,
    env_path: Path | str = DEFAULT_ENV_PATH,
    timeout_seconds: int = UPLOAD_REQUEST_TIMEOUT_SECONDS,
) -> requests.Response:
    archive_path = Path(archive_path)
    api_url = read_env_value("API_URL", env_path)
    api_key = read_env_value("API_KEY", env_path)
    if not api_url:
        raise UploadRequestError("API_URL не найден в .env")
    if not api_key:
        raise UploadRequestError("API_KEY не найден в .env")
    if not archive_path.is_file():
        raise FileNotFoundError(f"Архив не найден: {archive_path}")

    try:
        with archive_path.open("rb") as archive_file:
            response = requests.post(
                build_archive_upload_url(api_url),
                headers={"X-API-Key": api_key},
                files={"archive": (archive_path.name, archive_file)},
                timeout=timeout_seconds,
            )
        response.raise_for_status()
    except requests.RequestException as error:
        raise UploadRequestError(f"Не удалось выгрузить архив: {error}") from error

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


def write_metadata(metadata_path: Path | str, metadata: dict) -> None:
    metadata_path = Path(metadata_path)
    with metadata_path.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, ensure_ascii=False, indent=2)
        metadata_file.write("\n")


def read_dataset_project_name(metadata: dict) -> str:
    dataset_update = metadata.get("dataset_update", {})
    if not isinstance(dataset_update, dict):
        raise ValueError("metadata.json: dataset_update должен быть объектом")

    project_name = str(dataset_update.get("name", "")).strip()
    if not project_name:
        raise ValueError("metadata.json: dataset_update.name не заполнен")

    return project_name


def read_metadata_class_names(metadata: dict) -> list[str]:
    classes = read_metadata_classes(metadata)
    class_names = [str(class_name) for class_name in classes.keys()]
    if not class_names:
        raise ValueError("metadata.json: classes пустой")

    return class_names


def read_project_class_names(
    metadata: dict,
    class_names: Iterable[str] | None = None,
) -> list[str]:
    metadata_class_names = read_metadata_class_names(metadata)
    if class_names is None:
        return metadata_class_names

    metadata_class_names_set = set(metadata_class_names)
    project_class_names = [
        class_name
        for class_name in unique_class_names(class_names)
        if class_name in metadata_class_names_set
    ]
    if not project_class_names:
        raise ValueError("metadata.json: выбранные классы отсутствуют в classes")

    return project_class_names


def read_metadata_classes(metadata: dict) -> dict:
    classes = metadata.get("classes", {})
    if not isinstance(classes, dict):
        raise ValueError("metadata.json: classes должен быть объектом")

    return classes


def metadata_with_classes(metadata: dict, class_names: Iterable[str]) -> dict:
    classes = read_metadata_classes(metadata)
    return {
        **metadata,
        "classes": {
            class_name: classes[class_name]
            for class_name in class_names
        },
    }


def metadata_without_classes(metadata: dict, class_names: Iterable[str]) -> dict:
    classes = read_metadata_classes(metadata)
    excluded_class_names = set(class_names)
    return {
        **metadata,
        "classes": {
            class_name: class_data
            for class_name, class_data in classes.items()
            if class_name not in excluded_class_names
        },
    }


def resolve_backup_dataset_dir(
    dataset_dir: Path,
    backup_dataset_dir: Path | str | None = None,
) -> Path:
    if backup_dataset_dir is None:
        return (dataset_dir.parent / DEFAULT_BACKUP_DATASET_DIR.name).resolve()

    return Path(backup_dataset_dir).resolve()


def prepare_backup_class_dirs(
    class_dirs: Iterable[tuple[str, Path]],
    backup_dataset_dir: Path,
) -> list[tuple[Path, Path]]:
    backup_class_dirs = []
    reserved_destinations = set()
    for class_name, class_dir in class_dirs:
        destination_dir = unique_backup_class_dir(
            backup_dataset_dir,
            class_name,
            reserved_destinations,
        )
        backup_class_dirs.append((class_dir, destination_dir))
        reserved_destinations.add(destination_dir)

    return backup_class_dirs


def unique_backup_class_dir(
    backup_dataset_dir: Path,
    class_name: str,
    reserved_destinations: set[Path],
) -> Path:
    destination_dir = backup_dataset_dir / class_name
    suffix = 1
    while destination_dir.exists() or destination_dir in reserved_destinations:
        destination_dir = backup_dataset_dir / f"{class_name}_{suffix}"
        suffix += 1

    return destination_dir


def move_class_dirs_to_backup(class_dirs: Iterable[tuple[Path, Path]]) -> None:
    class_dirs = list(class_dirs)
    if not class_dirs:
        return

    class_dirs[0][1].parent.mkdir(parents=True, exist_ok=True)
    for class_dir, destination_dir in class_dirs:
        shutil.move(str(class_dir), str(destination_dir))


def add_metadata_to_archive(
    archive: tarfile.TarFile,
    metadata: dict,
    arcname: str,
) -> None:
    metadata_bytes = (
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    tar_info = tarfile.TarInfo(arcname)
    tar_info.size = len(metadata_bytes)
    archive.addfile(tar_info, io.BytesIO(metadata_bytes))


def build_projects_url(api_url: str) -> str:
    api_url = api_url.strip().rstrip("/")
    if not api_url:
        raise UploadRequestError("API_URL не должен быть пустым")
    if not re.match(r"^https?://", api_url):
        api_url = f"http://{api_url}"

    return f"{api_url}/projects"


def build_archive_upload_url(api_url: str) -> str:
    api_url = api_url.strip().rstrip("/")
    if not api_url:
        raise UploadRequestError("API_URL не должен быть пустым")
    if not re.match(r"^https?://", api_url):
        api_url = f"http://{api_url}"

    return f"{api_url}/uploads/archive"


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


def unique_class_names(class_names: Iterable[str]) -> list[str]:
    unique_names = []
    seen_names = set()
    for class_name in class_names:
        class_name = validate_class_name(class_name)
        if class_name in seen_names:
            continue
        unique_names.append(class_name)
        seen_names.add(class_name)

    return unique_names


def validate_dataset_update_name(dataset_update_name: str) -> str:
    dataset_update_name = str(dataset_update_name).strip()
    if not dataset_update_name:
        raise ValueError("metadata.json: dataset_update.name не заполнен")
    if dataset_update_name in {".", ".."}:
        raise ValueError("metadata.json: dataset_update.name некорректен")
    if INVALID_CLASS_NAME_PATTERN.search(dataset_update_name):
        raise ValueError('metadata.json: dataset_update.name не должен содержать символы <>:"/\\|?*')

    return dataset_update_name


def resolve_class_dir(dataset_dir: Path, class_name: str) -> Path:
    class_dir = (dataset_dir / class_name).resolve()
    try:
        class_dir.relative_to(dataset_dir)
    except ValueError:
        raise ValueError("Папка класса должна находиться внутри папки датасета") from None

    return class_dir
