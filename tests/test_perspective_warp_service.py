import numpy as np
import pytest

from services.perspective_warp_service import detect_aruco_marker_rectangle


class FakeDetector:
    def __init__(self, marker_ids):
        self.marker_ids = marker_ids

    def detectMarkers(self, gray):
        corners = [
            np.array(
                [[[0, 0], [1, 0], [1, 1], [0, 1]]],
                dtype=np.float32,
            )
            for _ in self.marker_ids
        ]
        ids = np.array(self.marker_ids, dtype=np.int32).reshape(-1, 1)
        return corners, ids, []


def test_detect_marker_rectangle_accepts_reused_detector():
    image = np.zeros((10, 10, 3), dtype=np.uint8)

    rectangle = detect_aruco_marker_rectangle(
        image,
        detector=FakeDetector([0, 1, 2, 3]),
    )

    assert rectangle.shape == (4, 2)


def test_detect_marker_rectangle_rejects_frame_with_missing_marker():
    image = np.zeros((10, 10, 3), dtype=np.uint8)

    with pytest.raises(RuntimeError, match=r"\[3\]"):
        detect_aruco_marker_rectangle(
            image,
            detector=FakeDetector([0, 1, 2]),
        )
