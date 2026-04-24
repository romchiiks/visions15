"""
Camera service module for handling video capture and image processing.
Uses OpenCV (cv2) for camera interaction.
Designed to handle a single camera instance across the entire application.
"""

import cv2
import threading
from PySide6.QtCore import QObject, Signal, QTimer
from typing import Optional
from datetime import datetime
import os


class CameraService(QObject):
    """
    Manages camera capture and provides frames to the application.
    Runs in a separate thread to avoid blocking the UI.
    """
    
    # Signals
    frame_ready = Signal(object)  # Emits the captured frame (numpy array)
    camera_error = Signal(str)     # Emits error messages
    
    def __init__(self):
        """Initialize the camera service."""
        super().__init__()
        self.cap = None
        self.is_running = False
        self.camera_thread = None
        self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize the camera device."""
        try:
            self.cap = cv2.VideoCapture(1)
            if not self.cap.isOpened():
                self.camera_error.emit("Не удалось открыть камеру / Failed to open camera")
                return
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
        except Exception as e:
            self.camera_error.emit(f"Ошибка инициализации камеры / Camera initialization error: {str(e)}")
    
    def start_stream(self):
        """Start the camera stream in a separate thread."""
        if not self.cap or not self.cap.isOpened():
            self.camera_error.emit("Камера не инициализирована / Camera not initialized")
            return
        
        if self.is_running:
            return
        
        self.is_running = True
        self.camera_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.camera_thread.start()
    
    def stop_stream(self):
        """Stop the camera stream."""
        self.is_running = False
        if self.camera_thread:
            self.camera_thread.join(timeout=2)
    
    def _capture_loop(self):
        """Main capture loop running in a separate thread."""
        while self.is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.frame_ready.emit(frame)
            else:
                break
    
    def capture_frame(self) -> Optional[object]:
        """Capture a single frame from the camera."""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None
    
    def save_image(self, frame, folder: str) -> Optional[str]:
        """
        Save a frame to disk.
        
        Args:
            frame: Numpy array (cv2 frame)
            folder: Directory to save the image
        
        Returns:
            Path to saved image or None if failed
        """
        try:
            os.makedirs(folder, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = os.path.join(folder, f"{timestamp}.jpg")
            cv2.imwrite(filename, frame)
            return filename
        except Exception as e:
            self.camera_error.emit(f"Ошибка сохранения изображения / Image save error: {str(e)}")
            return None
    
    def cleanup(self):
        """Release camera resources."""
        self.stop_stream()
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()
