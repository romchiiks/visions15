import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from services.model_service import DEFAULT_MODEL_DIR, MODEL_WEIGHTS_FILE_NAME


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = DEFAULT_MODEL_DIR / MODEL_WEIGHTS_FILE_NAME
DEFAULT_EXPORT_ROOT = PROJECT_ROOT / "captures" / "predictions"
DEFAULT_YOLO_PYTHON = Path("/mnt/IR_AI/venvs/yolo-venv/bin/python")
YOLO_CLI_PATH = PROJECT_ROOT / "services" / "yolo_cli.py"
PREDICTION_TIMEOUT_SECONDS = 120


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
    yolo_python: Path | str | None = None,
) -> PredictionResult:
    image_path = Path(image_path)
    model_path = Path(model_path)
    export_root = Path(export_root)
    yolo_python = Path(yolo_python or os.environ.get("VISIONS15_YOLO_PYTHON", DEFAULT_YOLO_PYTHON))

    if not image_path.is_file():
        raise PredictionError(f"Изображение не найдено: {image_path}")
    if not model_path.is_file():
        raise PredictionError(f"Файл модели не найден: {model_path}")
    if not yolo_python.is_file():
        raise PredictionError(f"Python YOLO venv не найден: {yolo_python}")
    if not YOLO_CLI_PATH.is_file():
        raise PredictionError(f"YOLO CLI не найден: {YOLO_CLI_PATH}")

    export_dir = export_root / image_path.stem
    export_dir.mkdir(parents=True, exist_ok=True)

    command = [
        str(yolo_python),
        str(YOLO_CLI_PATH),
        str(image_path),
        "--model",
        str(model_path),
        "--export-dir",
        str(export_dir),
        "--device",
        os.environ.get("VISIONS15_YOLO_DEVICE", "cuda:0"),
        "--confidence",
        os.environ.get("VISIONS15_YOLO_CONFIDENCE", "0.35"),
    ]

    try:
        completed_process = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            text=True,
            capture_output=True,
            timeout=PREDICTION_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise PredictionError("YOLO inference превысил лимит ожидания") from error
    except OSError as error:
        raise PredictionError(f"Не удалось запустить YOLO inference: {error}") from error

    if completed_process.returncode != 0:
        message = completed_process.stderr.strip() or completed_process.stdout.strip()
        raise PredictionError(f"YOLO inference завершился с ошибкой: {message}")

    payload = load_prediction_payload(completed_process.stdout)

    return parse_prediction_payload(payload, image_path, export_dir)


def load_prediction_payload(stdout: str) -> dict:
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        pass

    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue

    raise PredictionError("YOLO inference вернул некорректный JSON")


def parse_prediction_payload(payload: dict, image_path: Path, export_dir: Path) -> PredictionResult:
    if not isinstance(payload, dict):
        raise PredictionError("YOLO inference должен вернуть JSON-объект")

    raw_predictions = payload.get("predictions", [])
    if not isinstance(raw_predictions, list):
        raise PredictionError("YOLO inference: predictions должен быть списком")

    predictions = []
    for raw_prediction in raw_predictions:
        predictions.append(parse_prediction(raw_prediction))

    visual_path = parse_optional_path(payload.get("visual_path"))

    return PredictionResult(
        image_path=image_path,
        export_dir=export_dir,
        visual_path=visual_path,
        predictions=predictions,
    )


def parse_prediction(raw_prediction: dict) -> Prediction:
    if not isinstance(raw_prediction, dict):
        raise PredictionError("YOLO inference: prediction должен быть JSON-объектом")

    category_name = raw_prediction.get("category_name", raw_prediction.get("name"))
    score = raw_prediction.get("score", raw_prediction.get("confidence"))
    bbox_xyxy = raw_prediction.get("bbox_xyxy")

    if category_name in (None, ""):
        raise PredictionError("YOLO inference: category_name не найден")
    if bbox_xyxy is None:
        raise PredictionError("YOLO inference: bbox_xyxy не найден")

    try:
        bbox_tuple = tuple(float(value) for value in bbox_xyxy)
    except (TypeError, ValueError) as error:
        raise PredictionError("YOLO inference: bbox_xyxy должен содержать числа") from error

    if len(bbox_tuple) != 4:
        raise PredictionError("YOLO inference: bbox_xyxy должен содержать 4 числа")

    try:
        score = float(score)
    except (TypeError, ValueError) as error:
        raise PredictionError("YOLO inference: score должен быть числом") from error

    return Prediction(
        category_name=str(category_name),
        score=score,
        bbox_xyxy=bbox_tuple,
    )


def parse_optional_path(value) -> Path | None:
    if value in (None, ""):
        return None

    path = Path(value)
    if path.is_file():
        return path

    return None


if __name__ == "__main__":
    try:
        result = predict_image(sys.argv[1])
    except (IndexError, PredictionError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error

    print(
        json.dumps(
            {
                "image_path": str(result.image_path),
                "export_dir": str(result.export_dir),
                "visual_path": str(result.visual_path) if result.visual_path else None,
                "predictions": [
                    {
                        "category_name": prediction.category_name,
                        "score": prediction.score,
                        "bbox_xyxy": list(prediction.bbox_xyxy),
                    }
                    for prediction in result.predictions
                ],
            },
            ensure_ascii=False,
        )
    )
