from threading import Lock

import cv2
import numpy as np


OUTPUT_WIDTH = 2550 #CHANGE THIS 
OUTPUT_HEIGHT = 1680 #CHANGE THIS
SAHI_SLICE_SIZE = 1024
SAHI_OVERLAP_RATIO = 0.2
REQUIRED_IDS = (0, 1, 2, 3)
REQUIRED_IDS_SET = set(REQUIRED_IDS)
DETECTION_WIDTH = 960
DETECTION_HEIGHT = 540
_DETECTOR = None
_DETECTOR_LOCK = Lock()


def create_aruco_detector():
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    detector_parameters = cv2.aruco.DetectorParameters()
    return cv2.aruco.ArucoDetector(aruco_dict, detector_parameters)


def _get_detector():
    global _DETECTOR
    if _DETECTOR is None:
        _DETECTOR = _create_detector()
    return _DETECTOR


def _detect_markers(image, detector):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = detector.detectMarkers(gray)

    if ids is None:
        raise RuntimeError("Aruco-маркеры не найдены")

    return corners, ids.flatten()


def _build_src_points(corners, ids):
    marker_points = {
        int(marker_id): marker_corners[0]
        for marker_corners, marker_id in zip(corners, ids)
    }

    missing_ids = REQUIRED_IDS_SET - marker_points.keys()
    if missing_ids:
        raise RuntimeError(f"Не найдены обязательные Aruco-маркеры: {sorted(missing_ids)}")

    return np.array(
        [
            marker_points[0][2],
            marker_points[1][3],
            marker_points[2][0],
            marker_points[3][1],
        ],
        dtype=np.float32,
    )


def detect_aruco_marker_rectangle(image):
    detector = _get_detector()
    with _DETECTOR_LOCK:
        corners, ids = _detect_markers(image, detector)
    return _build_src_points(corners, ids)


def detect_aruco_marker_rectangle_preview(
    image,
    max_width: int = DETECTION_WIDTH,
    max_height: int = DETECTION_HEIGHT,
):
    height, width = image.shape[:2]
    scale = min(max_width / width, max_height / height, 1)
    if scale == 1:
        return detect_aruco_marker_rectangle(image)

    preview_width = max(1, int(width * scale))
    preview_height = max(1, int(height * scale))
    preview_image = cv2.resize(
        image,
        (preview_width, preview_height),
        interpolation=cv2.INTER_AREA,
    )
    return detect_aruco_marker_rectangle(preview_image) / scale


def get_sahi_slice_intervals(
    image_length: int,
    slice_size: int = SAHI_SLICE_SIZE,
    overlap_ratio: float = SAHI_OVERLAP_RATIO,
):
    if image_length <= 0 or slice_size <= 0:
        raise ValueError("Размер изображения и слайса должен быть больше 0")
    if not 0 <= overlap_ratio < 1:
        raise ValueError("Overlap должен быть в диапазоне от 0 до 1")
    if image_length <= slice_size:
        return [(0, image_length)]

    overlap = int(slice_size * overlap_ratio)
    step = slice_size - overlap
    intervals = []
    start = 0

    while True:
        end = start + slice_size
        if end >= image_length:
            last_start = image_length - slice_size
            last_interval = (last_start, image_length)
            if not intervals or intervals[-1] != last_interval:
                intervals.append(last_interval)
            return intervals

        intervals.append((start, end))
        start += step


def _overlap_intervals(slice_intervals):
    return [
        (current_start, previous_end)
        for (_, previous_end), (current_start, _) in zip(
            slice_intervals,
            slice_intervals[1:],
        )
        if current_start < previous_end
    ]


def _project_work_area_polygon(points, inverse_matrix):
    polygon = np.array(points, dtype=np.float32).reshape((-1, 1, 2))
    return cv2.perspectiveTransform(polygon, inverse_matrix).astype(np.int32)


def draw_sahi_overlap_boundaries(
    image,
    rectangle_points,
    output_width: int = OUTPUT_WIDTH,
    output_height: int = OUTPUT_HEIGHT,
    slice_size: int = SAHI_SLICE_SIZE,
    overlap_ratio: float = SAHI_OVERLAP_RATIO,
):
    output_image = draw_aruco_marker_rectangle(image, rectangle_points)
    destination_points = np.array(
        [
            [0, 0],
            [output_width - 1, 0],
            [output_width - 1, output_height - 1],
            [0, output_height - 1],
        ],
        dtype=np.float32,
    )
    inverse_matrix = cv2.getPerspectiveTransform(
        destination_points,
        rectangle_points.astype(np.float32),
    )

    x_overlaps = _overlap_intervals(
        get_sahi_slice_intervals(output_width, slice_size, overlap_ratio)
    )
    y_overlaps = _overlap_intervals(
        get_sahi_slice_intervals(output_height, slice_size, overlap_ratio)
    )

    overlap_color = (0, 165, 255)
    overlay = output_image.copy()
    overlap_polygons = []

    for left, right in x_overlaps:
        overlap_polygons.append(
            _project_work_area_polygon(
                [(left, 0), (right, 0), (right, output_height - 1), (left, output_height - 1)],
                inverse_matrix,
            )
        )

    for top, bottom in y_overlaps:
        overlap_polygons.append(
            _project_work_area_polygon(
                [(0, top), (output_width - 1, top), (output_width - 1, bottom), (0, bottom)],
                inverse_matrix,
            )
        )

    if overlap_polygons:
        for polygon in overlap_polygons:
            cv2.fillPoly(overlay, [polygon], overlap_color)
        output_image = cv2.addWeighted(overlay, 0.2, output_image, 0.8, 0)
        for polygon in overlap_polygons:
            cv2.polylines(
                output_image,
                [polygon],
                isClosed=True,
                color=overlap_color,
                thickness=2,
            )

    return output_image


def apply_perspective_warp(
    image,
    output_width: int = OUTPUT_WIDTH,
    output_height: int = OUTPUT_HEIGHT,
):
    src_points = detect_aruco_marker_rectangle(image)
    dst_points = np.array(
        [
            [0, 0],
            [output_width - 1, 0],
            [output_width - 1, output_height - 1],
            [0, output_height - 1],
        ],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)

    return cv2.warpPerspective(image, matrix, (output_width, output_height))
