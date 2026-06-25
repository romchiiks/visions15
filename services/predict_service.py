from dataclasses import dataclass
from pathlib import Path

from services.model_service import DEFAULT_MODEL_DIR, MODEL_WEIGHTS_FILE_NAME


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = DEFAULT_MODEL_DIR / MODEL_WEIGHTS_FILE_NAME
DEFAULT_EXPORT_ROOT = PROJECT_ROOT / "captures" / "predictions"


class PredictionError(RuntimeError):
    pass


@dataclass(frozen=True)
class Prediction:
    category_name: str
    score: float
    bbox_xyxy: tuple[float, float, float, float]


@dataclass(frozen=True)
class PredictionResult:
    image_path: Path
    export_dir: Path
    visual_path: Path | None
    predictions: list[Prediction]


def predict_image(
    image_path: Path | str,
    model_path: Path | str = DEFAULT_MODEL_PATH,
    export_root: Path | str = DEFAULT_EXPORT_ROOT,
) -> PredictionResult:
    image_path = Path(image_path)
    model_path = Path(model_path)
    export_root = Path(export_root)

    if not image_path.is_file():
        raise PredictionError(f"Изображение не найдено: {image_path}")
    if not model_path.is_file():
        raise PredictionError(f"Файл модели не найден: {model_path}")

    try:
        from sahi import AutoDetectionModel
        from sahi.predict import get_sliced_prediction
    except ImportError as error:
        raise PredictionError("SAHI не установлен. Установите зависимости из requirements.txt") from error

    export_dir = export_root / image_path.stem
    export_dir.mkdir(parents=True, exist_ok=True)

    try:
        detection_model = AutoDetectionModel.from_pretrained(
            model_type="ultralytics",
            model_path=str(model_path),
            confidence_threshold=0.35,
            device="cuda:0",
        )

        result = get_sliced_prediction(
            str(image_path),
            detection_model,
            slice_height=1024,
            slice_width=1024,
            overlap_height_ratio=0.2,
            overlap_width_ratio=0.2,
            postprocess_type="GREEDYNMM",
            postprocess_match_metric="IOS",
            postprocess_match_threshold=0.5,
            postprocess_class_agnostic=False,
        )
    except Exception as error:
        raise PredictionError(f"Не удалось выполнить SAHI prediction: {error}") from error

    predictions = [
        Prediction(
            category_name=str(pred.category.name),
            score=float(pred.score.value),
            bbox_xyxy=tuple(float(value) for value in pred.bbox.to_xyxy()),
        )
        for pred in result.object_prediction_list
    ]

    try:
        result.export_visuals(
            export_dir=str(export_dir),
            hide_conf=False,
            hide_labels=False,
        )
    except Exception as error:
        raise PredictionError(f"Не удалось сохранить визуализацию prediction: {error}") from error

    return PredictionResult(
        image_path=image_path,
        export_dir=export_dir,
        visual_path=find_exported_visual(export_dir),
        predictions=predictions,
    )


def find_exported_visual(export_dir: Path) -> Path | None:
    visual_path = export_dir / "prediction_visual.png"
    if visual_path.is_file():
        return visual_path

    exported_images = [
        path
        for path in export_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]
    if not exported_images:
        return None

    return max(exported_images, key=lambda path: path.stat().st_mtime)
