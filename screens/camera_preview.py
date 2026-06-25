from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel


PREVIEW_WIDTH = 1280
PREVIEW_HEIGHT = 720
MARKER_COLOR_BGR = (0, 255, 0)
MARKER_THICKNESS = 3


def show_camera_frame(
    camera_label: QLabel,
    frame,
    marker_rectangle=None,
    max_width: int = PREVIEW_WIDTH,
    max_height: int = PREVIEW_HEIGHT,
) -> None:
    preview_frame, scale = create_preview_frame(
        camera_label,
        frame,
        max_width=max_width,
        max_height=max_height,
    )
    if marker_rectangle is not None:
        preview_frame = draw_marker_rectangle(preview_frame, marker_rectangle, scale)

    height, width = preview_frame.shape[:2]
    image = QImage(
        preview_frame.data,
        width,
        height,
        preview_frame.strides[0],
        QImage.Format_BGR888,
    )

    camera_label.setText("")
    camera_label.setPixmap(QPixmap.fromImage(image))


def create_preview_frame(
    camera_label: QLabel,
    frame,
    max_width: int = PREVIEW_WIDTH,
    max_height: int = PREVIEW_HEIGHT,
):
    height, width = frame.shape[:2]
    label_width = max(1, camera_label.width())
    label_height = max(1, camera_label.height())
    scale = min(
        label_width / width,
        label_height / height,
        max_width / width,
        max_height / height,
        1,
    )

    if scale == 1:
        return np.ascontiguousarray(frame), scale

    preview_width = max(1, int(width * scale))
    preview_height = max(1, int(height * scale))
    return (
        cv2.resize(
            frame,
            (preview_width, preview_height),
            interpolation=cv2.INTER_AREA,
        ),
        scale,
    )


def draw_marker_rectangle(frame, rectangle_points, scale: float):
    output_frame = frame.copy()
    points = (rectangle_points * scale).astype(np.int32).reshape((-1, 1, 2))
    cv2.polylines(
        output_frame,
        [points],
        isClosed=True,
        color=MARKER_COLOR_BGR,
        thickness=MARKER_THICKNESS,
    )
    return output_frame
