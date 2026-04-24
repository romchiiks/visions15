"""
Image collection screen - captures images for dataset collection.
Displays camera feed with a visual frame and provides controls for capturing images.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QImage, QPixmap
import os


class ImageCollectionScreen(QWidget):
    """
    Screen for collecting images for dataset.
    
    Signals:
        back_clicked: Emitted when back button is clicked
    """
    
    back_clicked = Signal()
    
    def __init__(self, camera_service):
        """
        Initialize the image collection screen.
        
        Args:
            camera_service: Instance of CameraService for capturing images
        """
        super().__init__()
        self.camera_service = camera_service
        self.image_counter = 0
        self.auto_capture_timer = None
        self.is_capturing = False
        self.dataset_folder = "dataset_temp"
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Сбор изображений / Image Collection")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Camera display area with frame
        camera_layout = QHBoxLayout()
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(500, 375)
        self.camera_label.setStyleSheet(
            "border: 3px solid #333; background-color: #000;"
        )
        camera_layout.addWidget(self.camera_label, 1)
        layout.addLayout(camera_layout)
        
        # Counter display
        counter_layout = QHBoxLayout()
        counter_label = QLabel("Снимков / Images captured:")
        counter_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.counter_display = QLabel("0")
        counter_font = QFont()
        counter_font.setPointSize(14)
        counter_font.setBold(True)
        self.counter_display.setFont(counter_font)
        self.counter_display.setStyleSheet("color: #007acc; font-weight: bold;")
        counter_layout.addWidget(counter_label)
        counter_layout.addWidget(self.counter_display)
        counter_layout.addStretch()
        layout.addLayout(counter_layout)
        
        # Control buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Start button
        self.start_btn = self._create_button("Старт\nStart", 100)
        self.start_btn.clicked.connect(self._on_start_clicked)
        buttons_layout.addWidget(self.start_btn)
        
        # Pause button
        self.pause_btn = self._create_button("Пауза\nPause", 100)
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        self.pause_btn.setEnabled(False)
        buttons_layout.addWidget(self.pause_btn)
        
        # Stop button
        self.stop_btn = self._create_button("Стоп\nStop", 100)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)
        
        # Take Photo button
        self.photo_btn = self._create_button("Снимок\nTake Photo", 100)
        self.photo_btn.clicked.connect(self._on_photo_clicked)
        buttons_layout.addWidget(self.photo_btn)
        
        layout.addLayout(buttons_layout)
        
        # Back button
        back_btn = self._create_button("Назад\nBack", 80)
        back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back_btn)
        
        self.setLayout(layout)
    
    def _create_button(self, text: str, min_height: int) -> QPushButton:
        """
        Create a styled button.
        
        Args:
            text: Button text
            min_height: Minimum height
        
        Returns:
            Configured QPushButton
        """
        btn = QPushButton(text)
        btn.setMinimumHeight(min_height)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        btn.setFont(font)
        btn.setCursor(Qt.PointingHandCursor)
        return btn
    
    def _connect_signals(self):
        """Connect camera signals."""
        self.camera_service.frame_ready.connect(self._on_frame_ready)
    
    def _on_frame_ready(self, frame):
        """
        Handle incoming camera frame.
        
        Args:
            frame: OpenCV frame (numpy array)
        """
        # Draw visual frame on the image
        from utils import draw_frame_rect, cv2_to_qimage
        
        frame_with_rect = draw_frame_rect(frame, thickness=3, color=(0, 255, 0))
        q_image = cv2_to_qimage(frame_with_rect)
        
        # Scale to fit label
        pixmap = QPixmap.fromImage(q_image)
        scaled = pixmap.scaledToHeight(
            self.camera_label.height(),
            Qt.SmoothTransformation
        )
        self.camera_label.setPixmap(scaled)
    
    def _on_photo_clicked(self):
        """Handle take photo button click."""
        frame = self.camera_service.capture_frame()
        if frame is None:
            QMessageBox.warning(
                self,
                "Ошибка / Error",
                "Не удалось захватить кадр\n\nFailed to capture frame"
            )
            return
        
        saved_path = self.camera_service.save_image(frame, self.dataset_folder)
        if saved_path:
            self.image_counter += 1
            self.counter_display.setText(str(self.image_counter))
    
    def _on_start_clicked(self):
        """Handle start button click - begins automatic capture."""
        self.is_capturing = True
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        
        # Start auto-capture timer (1 second interval)
        self.auto_capture_timer = QTimer()
        self.auto_capture_timer.timeout.connect(self._on_auto_capture_timer)
        self.auto_capture_timer.start(1000)  # 1 second
    
    def _on_pause_clicked(self):
        """Handle pause button click."""
        if self.auto_capture_timer:
            self.auto_capture_timer.stop()
        self.is_capturing = False
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
    
    def _on_stop_clicked(self):
        """Handle stop button click."""
        if self.auto_capture_timer:
            self.auto_capture_timer.stop()
        
        self.is_capturing = False
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        # Show API call dialog
        self._show_api_dialog("/upload_images")
    
    def _on_auto_capture_timer(self):
        """Handle automatic capture timer tick."""
        if self.is_capturing:
            self._on_photo_clicked()
    
    def _show_api_dialog(self, endpoint: str):
        """
        Show a dialog simulating an API call.
        
        Args:
            endpoint: API endpoint (e.g., '/upload_images')
        """
        QMessageBox.information(
            self,
            "Вызов API / API Call",
            f"Вызов API: {endpoint}\n\nСнимков загружено: {self.image_counter}\n"
            f"Images uploaded: {self.image_counter}",
            QMessageBox.Ok
        )
    
    def showEvent(self, event):
        """Override show event to start camera stream."""
        super().showEvent(event)
        self.camera_service.start_stream()
    
    def hideEvent(self, event):
        """Override hide event to stop camera stream."""
        super().hideEvent(event)
        self.camera_service.stop_stream()
    
    def reset(self):
        """Reset the screen for a new collection session."""
        self.image_counter = 0
        self.counter_display.setText("0")
        self.is_capturing = False
        if self.auto_capture_timer:
            self.auto_capture_timer.stop()
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
