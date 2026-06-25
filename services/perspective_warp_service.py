from threading import Lock

import cv2
import numpy as np


OUTPUT_WIDTH = 1000
OUTPUT_HEIGHT = 700
REQUIRED_IDS = (0, 1, 2, 3)
REQUIRED_IDS_SET = set(REQUIRED_IDS)
DETECTION_WIDTH = 960
DETECTION_HEIGHT = 540
_DETECTOR = None
_DETECTOR_LOCK = Lock()


def _create_detector():
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
