"""
Main screen widget - the primary interface for the application.
Displays a table of captured parts and provides buttons for scanning, adding parts, and viewing images.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QLabel, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class MainScreen(QWidget):
    """
    Main application screen with table and control buttons.
    
    Signals:
        scan_clicked: Emitted when scan button is clicked
        add_part_clicked: Emitted when add part button is clicked
        show_image_clicked: Emitted when show image button is clicked
    """
    
    # Signals for navigation
    scan_clicked = Signal()
    add_part_clicked = Signal()
    show_image_clicked = Signal()
    
    def __init__(self):
        """Initialize the main screen."""
        super().__init__()
        self.undefined_objects_count = 0
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Сканер деталей / Parts Scanner")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Table for captured parts
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Наименование / Name", 
            "Код / Code", 
            "Количество / Qty", 
            "Штрихкод / Barcode"
        ])
        self.table.setRowCount(0)
        self.table.resizeColumnsToContents()
        self.table.setMinimumHeight(300)
        main_layout.addWidget(self.table)
        
        # Status line
        self.status_label = QLabel(f"Неопределенные объекты: {self.undefined_objects_count}")
        status_font = QFont()
        status_font.setPointSize(12)
        self.status_label.setFont(status_font)
        main_layout.addWidget(self.status_label)
        
        # Buttons layout (horizontal)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Scan button
        self.scan_btn = self._create_button("Сканировать\nScan", 120)
        self.scan_btn.clicked.connect(self.scan_clicked.emit)
        buttons_layout.addWidget(self.scan_btn)
        
        # Add Part button
        self.add_part_btn = self._create_button("Добавить деталь\nAdd Part", 120)
        self.add_part_btn.clicked.connect(self.add_part_clicked.emit)
        buttons_layout.addWidget(self.add_part_btn)
        
        # Show Image button
        self.show_image_btn = self._create_button("Показать\nизображение\nShow Image", 120)
        self.show_image_btn.clicked.connect(self.show_image_clicked.emit)
        buttons_layout.addWidget(self.show_image_btn)
        
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)
    
    def _create_button(self, text: str, min_height: int) -> QPushButton:
        """
        Create a styled button for touchscreen use.
        
        Args:
            text: Button text
            min_height: Minimum height for touchscreen friendliness
        
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
    
    def add_table_row(self, name: str, code: str, qty: str, barcode: str):
        """
        Add a row to the parts table.
        
        Args:
            name: Part name
            code: Part code
            qty: Quantity
            barcode: Barcode value
        """
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        
        self.table.setItem(row_position, 0, QTableWidgetItem(name))
        self.table.setItem(row_position, 1, QTableWidgetItem(code))
        self.table.setItem(row_position, 2, QTableWidgetItem(qty))
        self.table.setItem(row_position, 3, QTableWidgetItem(barcode))
        
        # Set row height for better touch interaction
        self.table.setRowHeight(row_position, 40)
    
    def clear_table(self):
        """Clear all rows from the table."""
        self.table.setRowCount(0)
    
    def set_undefined_objects_count(self, count: int):
        """
        Update the undefined objects counter.
        
        Args:
            count: Number of undefined objects
        """
        self.undefined_objects_count = count
        self.status_label.setText(f"Неопределенные объекты: {self.undefined_objects_count}")
    
    def show_api_call_dialog(self, endpoint: str):
        """
        Show a dialog simulating an API call.
        
        Args:
            endpoint: API endpoint (e.g., '/infer')
        """
        QMessageBox.information(
            self,
            "Вызов API / API Call",
            f"Вызов API: {endpoint}\n\nAPI Call: {endpoint}",
            QMessageBox.Ok
        )
