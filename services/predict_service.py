import os
from dataclasses import dataclass
from pathlib import Path

import requests


DEFAULT_PREDICT_URL = "http://127.0.0.1:8000/predict"
PREDICTION_CONNECT_TIMEOUT_SECONDS = 5
PREDICTION_READ_TIMEOUT_SECONDS = 120


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
    width: int
    height: int
    predictions: list[Prediction]


def predict_image(
    image_path: Path | str,
    predict_url: str | None = None,
) -> PredictionResult:
    image_path = Path(image_path)
    if not image_path.is_file():
        raise PredictionError(f"Изображение не найдено: {image_path}")

    predict_url = predict_url or os.environ.get("VISIONS15_PREDICT_URL", DEFAULT_PREDICT_URL)

    try:
        with image_path.open("rb") as image_file:
            response = requests.post(
                predict_url,
                files={"file": (image_path.name, image_file, "image/jpeg")},
                timeout=(
                    PREDICTION_CONNECT_TIMEOUT_SECONDS,
                    PREDICTION_READ_TIMEOUT_SECONDS,
                ),
            )
    except requests.RequestException as error:
        raise PredictionError(f"Не удалось выполнить распознавание: {error}") from error
    except OSError as error:
        raise PredictionError(f"Не удалось прочитать изображение: {error}") from error

    if not response.ok:
        raise PredictionError(_response_error_message(response))

    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError as error:
        raise PredictionError("Сервер распознавания вернул некорректный JSON") from error

    return parse_prediction_payload(payload, image_path)


def _response_error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError:
        payload = None

    detail = payload.get("detail") if isinstance(payload, dict) else None
    if detail:
        return f"Сервер распознавания вернул ошибку {response.status_code}: {detail}"

    return f"Сервер распознавания вернул ошибку {response.status_code}"


def parse_prediction_payload(payload: dict, image_path: Path | str) -> PredictionResult:
    if not isinstance(payload, dict):
        raise PredictionError("Сервер распознавания должен вернуть JSON-объект")

    try:
        width = int(payload["width"])
        height = int(payload["height"])
    except (KeyError, TypeError, ValueError) as error:
        raise PredictionError("В ответе сервера отсутствуют корректные размеры изображения") from error

    if width <= 0 or height <= 0:
        raise PredictionError("Размеры изображения в ответе сервера должны быть больше нуля")

    raw_detections = payload.get("detections")
    if not isinstance(raw_detections, list):
        raise PredictionError("В ответе сервера detections должен быть списком")

    return PredictionResult(
        image_path=Path(image_path),
        width=width,
        height=height,
        predictions=[parse_prediction(detection) for detection in raw_detections],
    )


def parse_prediction(raw_prediction: dict) -> Prediction:
    if not isinstance(raw_prediction, dict):
        raise PredictionError("Detection должен быть JSON-объектом")

    category_name = raw_prediction.get("class_name")
    score = raw_prediction.get("confidence")
    bbox_xyxy = raw_prediction.get("bbox_xyxy")

    if category_name in (None, ""):
        raise PredictionError("В detection отсутствует class_name")

    try:
        score = float(score)
    except (TypeError, ValueError) as error:
        raise PredictionError("В detection confidence должен быть числом") from error

    if not 0 <= score <= 1:
        raise PredictionError("В detection confidence должен быть от 0 до 1")

    try:
        bbox_tuple = tuple(float(value) for value in bbox_xyxy)
    except (TypeError, ValueError) as error:
        raise PredictionError("В detection bbox_xyxy должен содержать числа") from error

    if len(bbox_tuple) != 4:
        raise PredictionError("В detection bbox_xyxy должен содержать 4 числа")

    return Prediction(
        category_name=str(category_name),
        score=score,
        bbox_xyxy=bbox_tuple,
    )
