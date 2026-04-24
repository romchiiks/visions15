"""
Image viewer screen - displays the last captured image.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap


class ImageViewerScreen(QWidget):
    """
    Screen for viewing the last captured image.
    
    Signals:
        back_clicked: Emitted when back button is clicked
    """
    
    back_clicked = Signal()
    
    def __init__(self):
        """Initialize the image viewer screen."""
        super().__init__()
        self.current_image_path = None
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Просмотр изображения / View Image")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Image display label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(400)
        self.image_label.setStyleSheet("border: 2px solid #ccc; background-color: #f0f0f0;")
        layout.addWidget(self.image_label, 1)
        
        # Back button
        back_btn = QPushButton("Назад / Back")
        back_btn.setMinimumHeight(80)
        back_font = QFont()
        back_font.setPointSize(14)
        back_font.setBold(True)
        back_btn.setFont(back_font)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back_btn)
        
        self.setLayout(layout)
    
    def display_image(self, image_path: str):
        """
        Display an image from file path.
        
        Args:
            image_path: Path to the image file
        """
        self.current_image_path = image_path
        pixmap = QPixmap(image_path)
        
        if not pixmap.isNull():
            # Scale pixmap to fit the label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaledToHeight(
                self.image_label.height() - 20,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("Не удалось загрузить изображение\n\nFailed to load image")
    
    def clear_display(self):
        """Clear the displayed image."""
        self.image_label.clear()
        self.current_image_path = None
