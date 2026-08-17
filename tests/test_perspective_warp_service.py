import numpy as np
import pytest

from services.perspective_warp_service import (
    detect_aruco_marker_rectangle,
    draw_sahi_overlap_boundaries,
    get_sahi_slice_intervals,
)


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


def test_sahi_slice_intervals_match_server_work_area():
    assert get_sahi_slice_intervals(2550) == [
        (0, 1024),
        (820, 1844),
        (1526, 2550),
    ]
    assert get_sahi_slice_intervals(1680) == [
        (0, 1024),
        (656, 1680),
    ]


def test_draw_sahi_overlap_boundaries_projects_overlap_into_marker_area():
    image = np.zeros((80, 120, 3), dtype=np.uint8)
    rectangle = np.array(
        [[10, 10], [109, 10], [109, 69], [10, 69]],
        dtype=np.float32,
    )

    rendered = draw_sahi_overlap_boundaries(
        image,
        rectangle,
        output_width=100,
        output_height=60,
        slice_size=40,
        overlap_ratio=0.25,
    )

    assert rendered.shape == image.shape
    assert rendered[35, 45].any()
    assert not rendered[5, 5].any()
