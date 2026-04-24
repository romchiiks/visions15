"""
Part selection screen - allows user to select a part from a list.
Includes on-screen keyboard for search functionality.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QLabel, QLineEdit, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from widgets.keyboard import OnScreenKeyboard


class PartSelectionScreen(QWidget):
    """
    Screen for selecting a part.
    
    Signals:
        part_selected: Emitted when a part is selected
        custom_part_requested: Emitted when user wants to add custom part
        back_clicked: Emitted when back button is clicked
    """
    
    part_selected = Signal(dict)  # Emits selected part data
    custom_part_requested = Signal()  # Emitted to go to custom part input
    back_clicked = Signal()
    
    def __init__(self):
        """Initialize the part selection screen."""
        super().__init__()
        self.parts_data = self._get_sample_parts()
        self.filtered_parts_indices = list(range(len(self.parts_data)))
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Выбор детали / Select Part")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Search section with keyboard
        search_section_layout = QVBoxLayout()
        search_section_layout.setSpacing(5)
        
        # Search label
        search_label = QLabel("Поиск / Search:")
        search_label.setFont(QFont("Arial", 12, QFont.Bold))
        search_section_layout.addWidget(search_label)
        
        # On-screen keyboard for search
        self.keyboard = OnScreenKeyboard()
        self.keyboard.text_changed.connect(self._on_search_text_changed)
        search_section_layout.addWidget(self.keyboard)
        
        layout.addLayout(search_section_layout)
        
        # Parts table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "Наименование / Name",
            "Код / Code",
            "Описание / Description"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        self._refresh_table()
        
        self.table.resizeColumnsToContents()
        layout.addWidget(self.table, 1)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Select button
        select_btn = self._create_button("Выбрать\nSelect", 100)
        select_btn.clicked.connect(self._on_select_clicked)
        buttons_layout.addWidget(select_btn)
        
        # Add Custom Part button
        custom_btn = self._create_button("+ Своя\nCustom", 100)
        custom_btn.clicked.connect(self.custom_part_requested.emit)
        buttons_layout.addWidget(custom_btn)
        
        # Back button
        back_btn = self._create_button("Назад\nBack", 100)
        back_btn.clicked.connect(self.back_clicked.emit)
        buttons_layout.addWidget(back_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def _refresh_table(self):
        """Refresh table with filtered parts."""
        # Clear table
        self.table.setRowCount(0)
        
        # Add filtered parts
        for row_idx, part_idx in enumerate(self.filtered_parts_indices):
            part = self.parts_data[part_idx]
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(part["name"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(part["code"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(part["description"]))
            self.table.setRowHeight(row_idx, 40)
    
    def _on_search_text_changed(self, search_text: str):
        """
        Handle search text change and filter table.
        
        Args:
            search_text: Current search text
        """
        search_lower = search_text.lower()
        
        # Filter parts based on search text
        if not search_text:
            # Show all if search is empty
            self.filtered_parts_indices = list(range(len(self.parts_data)))
        else:
            # Filter by name or code
            self.filtered_parts_indices = [
                idx for idx, part in enumerate(self.parts_data)
                if search_lower in part["name"].lower() or 
                   search_lower in part["code"].lower()
            ]
        
        # Refresh table display
        self._refresh_table()
    
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
    
    def _on_select_clicked(self):
        """Handle select button click."""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            return
        
        # Get the actual part index from filtered list
        display_row = selected_rows[0].row()
        actual_part_idx = self.filtered_parts_indices[display_row]
        selected_part = self.parts_data[actual_part_idx]
        self.part_selected.emit(selected_part)
    
    @staticmethod
    def _get_sample_parts() -> list:
        """
        Get sample parts data for the table.
        
        Returns:
            List of part dictionaries
        """
        return [
            {
                "name": "Резистор 10кОм / 10K Resistor",
                "code": "R001",
                "description": "Углеродный пленочный / Carbon film"
            },
            {
                "name": "Конденсатор 100мкФ / 100uF Capacitor",
                "code": "C001",
                "description": "Электролитический / Electrolytic"
            },
            {
                "name": "Светодиод красный / Red LED",
                "code": "LED001",
                "description": "3мм, 20mA / 3mm, 20mA"
            },
            {
                "name": "Микросхема 555 / 555 Timer IC",
                "code": "IC001",
                "description": "DIP8 корпус / package"
            },
            {
                "name": "Кварцевый кристалл 8МГц / 8MHz Crystal",
                "code": "X001",
                "description": "HC-49U корпус / package"
            },
        ]
