"""
Custom part input screen - allows user to enter a custom part name using on-screen keyboard.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from widgets.keyboard import OnScreenKeyboard


class CustomPartInputScreen(QWidget):
    """
    Screen for entering a custom part name using on-screen keyboard.
    
    Signals:
        part_name_entered: Emitted when user confirms a part name
        back_clicked: Emitted when back button is clicked
    """
    
    part_name_entered = Signal(str)  # Emits the entered part name
    back_clicked = Signal()
    
    def __init__(self):
        """Initialize the custom part input screen."""
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Введите название детали\nEnter Part Name")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Используйте клавиатуру ниже\nUse the keyboard below"
        )
        instructions.setFont(QFont("Arial", 12))
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)
        
        # On-screen keyboard
        self.keyboard = OnScreenKeyboard()
        layout.addWidget(self.keyboard, 1)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Confirm button
        confirm_btn = self._create_button("✓ Готово\nDone", 100)
        confirm_btn.clicked.connect(self._on_confirm_clicked)
        buttons_layout.addWidget(confirm_btn)
        
        # Back button
        back_btn = self._create_button("← Назад\nBack", 100)
        back_btn.clicked.connect(self.back_clicked.emit)
        buttons_layout.addWidget(back_btn)
        
        layout.addLayout(buttons_layout)
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
        font.setPointSize(12)
        font.setBold(True)
        btn.setFont(font)
        btn.setCursor(Qt.PointingHandCursor)
        return btn
    
    def _on_confirm_clicked(self):
        """Handle confirm button click."""
        part_name = self.keyboard.get_text().strip()
        if part_name:
            self.part_name_entered.emit(part_name)
            self.keyboard.clear()
        else:
            # Could show a warning, but for now just ignore
            pass
    
    def reset(self):
        """Reset the screen for a new entry."""
        self.keyboard.clear()
    
    def get_entered_text(self) -> str:
        """
        Get the currently entered text.
        
        Returns:
            Entered text from keyboard
        """
        return self.keyboard.get_text()
