from pathlib import Path

import pytest
import requests

from services.predict_service import (
    DEFAULT_PREDICT_URL,
    PredictionError,
    parse_prediction_payload,
    predict_image,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.ok = 200 <= status_code < 400

    def json(self):
        return self.payload


def test_parse_prediction_payload_uses_server_detection_contract():
    result = parse_prediction_payload(
        {
            "image_name": "scan.jpeg",
            "width": 2550,
            "height": 1680,
            "detections": [
                {
                    "class_id": 4,
                    "class_name": "detail_name",
                    "confidence": 0.91,
                    "bbox_xyxy": [100, 120, 300, 360],
                    "bbox_xywh": [100, 120, 200, 240],
                }
            ],
        },
        Path("scan.jpeg"),
    )

    assert result.width == 2550
    assert result.height == 1680
    assert len(result.predictions) == 1
    assert result.predictions[0].category_name == "detail_name"
    assert result.predictions[0].score == pytest.approx(0.91)
    assert result.predictions[0].bbox_xyxy == (100.0, 120.0, 300.0, 360.0)


def test_parse_prediction_payload_accepts_empty_detections():
    result = parse_prediction_payload(
        {
            "image_name": "scan.jpeg",
            "width": 2550,
            "height": 1680,
            "detections": [],
        },
        Path("scan.jpeg"),
    )

    assert result.predictions == []


def test_predict_image_posts_multipart_file_to_local_server(tmp_path, monkeypatch):
    image_path = tmp_path / "scan.jpeg"
    image_path.write_bytes(b"jpeg")
    captured_request = {}

    def fake_post(url, files, timeout):
        captured_request["url"] = url
        captured_request["name"] = files["file"][0]
        captured_request["content"] = files["file"][1].read()
        captured_request["content_type"] = files["file"][2]
        captured_request["timeout"] = timeout
        return FakeResponse(
            {
                "image_name": "scan.jpeg",
                "width": 2550,
                "height": 1680,
                "detections": [],
            }
        )

    monkeypatch.setattr(requests, "post", fake_post)

    result = predict_image(image_path)

    assert result.image_path == image_path
    assert captured_request["url"] == DEFAULT_PREDICT_URL
    assert captured_request["name"] == "scan.jpeg"
    assert captured_request["content"] == b"jpeg"
    assert captured_request["content_type"] == "image/jpeg"


def test_parse_prediction_payload_rejects_invalid_confidence():
    with pytest.raises(PredictionError, match="confidence"):
        parse_prediction_payload(
            {
                "width": 100,
                "height": 100,
                "detections": [
                    {
                        "class_name": "detail",
                        "confidence": 1.5,
                        "bbox_xyxy": [1, 2, 3, 4],
                    }
                ],
            },
            Path("scan.jpeg"),
        )
