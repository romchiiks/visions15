"""
Main application class - orchestrates all screens and navigation.
This is the entry point for the PySide6 touchscreen application.
"""

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import sys
import os

from camera_service import CameraService
from screens import (
    MainScreen,
    ImageViewerScreen,
    PartSelectionScreen,
    ImageCollectionScreen,
    CustomPartInputScreen
)


class VisionScannerApp(QMainWindow):
    """
    Main application window managing all screens and navigation.
    Uses QStackedWidget for screen switching.
    """
    
    # Screen constants
    SCREEN_MAIN = 0
    SCREEN_IMAGE_VIEWER = 1
    SCREEN_PART_SELECTION = 2
    SCREEN_IMAGE_COLLECTION = 3
    SCREEN_CUSTOM_PART_INPUT = 4
    
    def __init__(self):
        """Initialize the application."""
        super().__init__()
        
        # Initialize camera service (shared across all screens)
        self.camera_service = CameraService()
        
        # Track last captured image
        self.last_image_path = None
        
        # Setup window
        self.setWindowTitle("Сканер видения / Vision Scanner")
        self.setGeometry(100, 100, 1024, 768)
        
        # Set font for better readability on touchscreen
        font = QFont()
        font.setPointSize(11)
        QApplication.setFont(font)
        
        # Initialize screens
        self._init_screens()
        
        # Connect signals for navigation
        self._connect_signals()
    
    def _init_screens(self):
        """Initialize all screens and add to stacked widget."""
        # Create stacked widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create and add screens
        self.main_screen = MainScreen()
        self.image_viewer_screen = ImageViewerScreen()
        self.part_selection_screen = PartSelectionScreen()
        self.image_collection_screen = ImageCollectionScreen(self.camera_service)
        self.custom_part_input_screen = CustomPartInputScreen()
        
        self.stacked_widget.addWidget(self.main_screen)  # Index 0
        self.stacked_widget.addWidget(self.image_viewer_screen)  # Index 1
        self.stacked_widget.addWidget(self.part_selection_screen)  # Index 2
        self.stacked_widget.addWidget(self.image_collection_screen)  # Index 3
        self.stacked_widget.addWidget(self.custom_part_input_screen)  # Index 4
        
        # Show main screen by default
        self.stacked_widget.setCurrentIndex(self.SCREEN_MAIN)
    
    def _connect_signals(self):
        """Connect signals from all screens."""
        # Main screen signals
        self.main_screen.scan_clicked.connect(self._on_main_scan_clicked)
        self.main_screen.add_part_clicked.connect(self._on_main_add_part_clicked)
        self.main_screen.show_image_clicked.connect(self._on_main_show_image_clicked)
        
        # Image viewer signals
        self.image_viewer_screen.back_clicked.connect(self._go_to_main)
        
        # Part selection signals
        self.part_selection_screen.part_selected.connect(self._on_part_selected)
        self.part_selection_screen.custom_part_requested.connect(self._on_custom_part_requested)
        self.part_selection_screen.back_clicked.connect(self._go_to_main)
        
        # Image collection signals
        self.image_collection_screen.back_clicked.connect(self._on_image_collection_back)
        
        # Custom part input signals
        self.custom_part_input_screen.part_name_entered.connect(self._on_custom_part_name_entered)
        self.custom_part_input_screen.back_clicked.connect(self._go_to_part_selection)
        
        # Camera service signals
        self.camera_service.camera_error.connect(self._on_camera_error)
    
    def _on_main_scan_clicked(self):
        """Handle scan button from main screen."""
        # Capture image
        frame = self.camera_service.capture_frame()
        if frame is None:
            QMessageBox.warning(
                self,
                "Ошибка / Error",
                "Не удалось захватить изображение\n\nFailed to capture image"
            )
            return
        
        # Save image
        saved_path = self.camera_service.save_image(frame, "captures")
        if saved_path:
            self.last_image_path = saved_path
        
        # Show API dialog
        self.main_screen.show_api_call_dialog("/infer")
    
    def _on_main_add_part_clicked(self):
        """Handle add part button from main screen - go to part selection."""
        self.stacked_widget.setCurrentIndex(self.SCREEN_PART_SELECTION)
    
    def _on_main_show_image_clicked(self):
        """Handle show image button from main screen."""
        if self.last_image_path is None:
            QMessageBox.information(
                self,
                "Информация / Information",
                "Нет сохраненных изображений\n\nNo saved images yet"
            )
            return
        
        self.image_viewer_screen.display_image(self.last_image_path)
        self.stacked_widget.setCurrentIndex(self.SCREEN_IMAGE_VIEWER)
    
    def _on_part_selected(self, part_data: dict):
        """
        Handle part selection from part selection screen.
        Navigates to image collection screen.
        
        Args:
            part_data: Dictionary with selected part information
        """
        # Reset image collection screen for new session
        self.image_collection_screen.reset()
        
        # Navigate to image collection
        self.stacked_widget.setCurrentIndex(self.SCREEN_IMAGE_COLLECTION)
    
    def _on_image_collection_back(self):
        """Handle back button from image collection screen."""
        self._go_to_main()
    
    def _on_custom_part_requested(self):
        """Handle request to add custom part - navigate to input screen."""
        self.custom_part_input_screen.reset()
        self.stacked_widget.setCurrentIndex(self.SCREEN_CUSTOM_PART_INPUT)
    
    def _on_custom_part_name_entered(self, part_name: str):
        """
        Handle custom part name entry.
        
        Args:
            part_name: The entered part name
        """
        # Create a custom part dict
        custom_part = {
            "name": part_name,
            "code": f"CUSTOM_{part_name.upper()[:4]}",
            "description": "Custom part added by user"
        }
        
        # Proceed with image collection for this part
        self._on_part_selected(custom_part)
    
    def _go_to_part_selection(self):
        """Navigate to part selection screen."""
        self.stacked_widget.setCurrentIndex(self.SCREEN_PART_SELECTION)
    
    def _go_to_main(self):
        """Navigate back to main screen."""
        self.stacked_widget.setCurrentIndex(self.SCREEN_MAIN)
    
    def _on_camera_error(self, error_message: str):
        """
        Handle camera errors.
        
        Args:
            error_message: Error message to display
        """
        QMessageBox.critical(
            self,
            "Ошибка камеры / Camera Error",
            error_message
        )
    
    def closeEvent(self, event):
        """
        Handle application close event.
        Cleanup camera resources gracefully.
        """
        self.camera_service.cleanup()
        event.accept()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = VisionScannerApp()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
