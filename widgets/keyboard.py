"""
On-screen keyboard widget for touchscreen text input.
Provides a-z, 0-9, special characters, and backspace.
"""

from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton, QLineEdit, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class OnScreenKeyboard(QWidget):
    """
    Touchscreen keyboard for text input.
    
    Signals:
        text_changed: Emitted when text is updated
    """
    
    text_changed = Signal(str)
    
    def __init__(self, parent=None):
        """Initialize the keyboard."""
        super().__init__(parent)
        self.input_field = None
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the keyboard UI."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Input field (optional, can be provided from outside)
        self.input_field = QLineEdit()
        self.input_field.setMinimumHeight(40)
        input_font = QFont()
        input_font.setPointSize(14)
        self.input_field.setFont(input_font)
        self.input_field.setReadOnly(True)  # Read-only, keyboard controls input
        main_layout.addWidget(self.input_field)
        
        # Keyboard grid
        keyboard_layout = QGridLayout()
        keyboard_layout.setSpacing(4)
        
        # Define keyboard layout (rows and columns)
        keyboard = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M'],
            ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
            ['-', '_'],
        ]
        
        # Add alphabet buttons
        row = 0
        for key_row in keyboard:
            col = 0
            for key in key_row:
                btn = self._create_key_button(key)
                btn.clicked.connect(lambda checked=False, k=key: self._on_key_pressed(k))
                keyboard_layout.addWidget(btn, row, col)
                col += 1
            row += 1
        
        main_layout.addLayout(keyboard_layout)
        
        # Control buttons row
        control_layout = QGridLayout()
        control_layout.setSpacing(4)
        
        # Backspace button (wide)
        backspace_btn = QPushButton("← Стереть / Backspace")
        backspace_btn.setMinimumHeight(50)
        backspace_font = QFont()
        backspace_font.setPointSize(11)
        backspace_font.setBold(True)
        backspace_btn.setFont(backspace_font)
        backspace_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #ac2925;
            }
        """)
        backspace_btn.clicked.connect(self._on_backspace_pressed)
        control_layout.addWidget(backspace_btn, 0, 0, 1, 5)
        
        # Clear button
        clear_btn = QPushButton("✕ Очистить / Clear")
        clear_btn.setMinimumHeight(50)
        clear_btn.setFont(backspace_font)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0ad4e;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #ec971f;
            }
        """)
        clear_btn.clicked.connect(self._on_clear_pressed)
        control_layout.addWidget(clear_btn, 0, 5, 1, 5)
        
        main_layout.addLayout(control_layout)
        self.setLayout(main_layout)
    
    def _create_key_button(self, key: str) -> QPushButton:
        """
        Create a styled keyboard button.
        
        Args:
            key: The character on the button
        
        Returns:
            Configured QPushButton
        """
        btn = QPushButton(key)
        btn.setMinimumHeight(45)
        btn.setMinimumWidth(45)
        
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        btn.setFont(font)
        
        btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:hover {
                background-color: #1084d7;
            }
        """)
        
        btn.setCursor(Qt.PointingHandCursor)
        return btn
    
    def _on_key_pressed(self, key: str):
        """
        Handle key button press.
        
        Args:
            key: The character pressed
        """
        current_text = self.input_field.text()
        new_text = current_text + key.lower()
        self.input_field.setText(new_text)
        self.text_changed.emit(new_text)
    
    def _on_backspace_pressed(self):
        """Handle backspace button press."""
        current_text = self.input_field.text()
        if current_text:
            new_text = current_text[:-1]
            self.input_field.setText(new_text)
            self.text_changed.emit(new_text)
    
    def _on_clear_pressed(self):
        """Handle clear button press."""
        self.input_field.setText("")
        self.text_changed.emit("")
    
    def set_text(self, text: str):
        """
        Set the input field text programmatically.
        
        Args:
            text: The text to set
        """
        self.input_field.setText(text)
        self.text_changed.emit(text)
    
    def get_text(self) -> str:
        """
        Get the current input field text.
        
        Returns:
            Current text in input field
        """
        return self.input_field.text()
    
    def clear(self):
        """Clear the input field."""
        self.input_field.setText("")
        self.text_changed.emit("")
    
    def set_external_field(self, line_edit: QLineEdit):
        """
        Connect keyboard to an external QLineEdit instead of internal field.
        
        Args:
            line_edit: QLineEdit widget to control
        """
        self.input_field = line_edit
        # Make external field look read-only from keyboard perspective
        self.input_field.setReadOnly(True)
