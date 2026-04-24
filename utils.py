"""
Utility functions for image handling and UI operations.
"""

import cv2
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt
import numpy as np


def cv2_to_qimage(cv_image) -> QImage:
    """
    Convert OpenCV image (numpy array) to Qt QImage.
    
    Args:
        cv_image: Numpy array from cv2
    
    Returns:
        QImage object
    """
    if cv_image is None:
        return QImage()
    
    height, width, channel = cv_image.shape
    bytes_per_line = 3 * width
    
    # Convert BGR to RGB
    cv_image_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    
    # Convert to QImage
    q_image = QImage(cv_image_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
    return q_image


def load_image_from_file(filepath: str) -> QPixmap:
    """
    Load an image from file and convert to QPixmap.
    
    Args:
        filepath: Path to image file
    
    Returns:
        QPixmap object
    """
    return QPixmap(filepath)


def draw_frame_rect(frame, thickness: int = 3, color: tuple = (0, 255, 0)):
    """
    Draw a rectangle frame on the image to show the capture area.
    
    Args:
        frame: Image array
        thickness: Border thickness in pixels
        color: RGB color tuple
    
    Returns:
        Modified frame with rectangle drawn
    """
    if frame is None:
        return None
    
    frame_copy = frame.copy()
    height, width = frame.shape[:2]
    
    # Calculate inset for the frame rectangle
    margin = 30
    x1, y1 = margin, margin
    x2, y2 = width - margin, height - margin
    
    # Draw rectangle (OpenCV uses BGR, not RGB)
    bgr_color = (color[2], color[1], color[0])
    cv2.rectangle(frame_copy, (x1, y1), (x2, y2), bgr_color, thickness)
    
    return frame_copy
