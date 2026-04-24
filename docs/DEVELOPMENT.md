# Development Tips & Best Practices

## Code Organization Principles

### 1. Screen Design Pattern

Every screen should follow this structure:

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class MyNewScreen(QWidget):
    """
    Description of what this screen does.
    
    Signals:
        signal_name: What it emits and when
    """
    
    # Define signals at top
    back_clicked = Signal()
    data_ready = Signal(dict)
    
    def __init__(self, dependencies=None):
        """
        Initialize the screen.
        
        Args:
            dependencies: Any services or data needed
        """
        super().__init__()
        self.dependencies = dependencies
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Build UI here
        
        self.setLayout(layout)
    
    def _create_button(self, text: str, min_height: int) -> QPushButton:
        """Helper for consistent button styling."""
        btn = QPushButton(text)
        btn.setMinimumHeight(min_height)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        btn.setFont(font)
        return btn
```

### 2. Signal Naming Convention

```python
# Good signal names (past tense for actions)
scan_clicked = Signal()
image_selected = Signal(str)
error_occurred = Signal(str)

# For data emission
image_ready = Signal(object)  # numpy array
part_selected = Signal(dict)  # dictionary with data
```

### 3. Organization Model

```
Core Services
├── camera_service.py          # External device interaction
├── api_service.py             # (Future) API communication
└── database_service.py        # (Future) Data persistence

Application Logic
└── main.py                    # Navigation & coordination

User Interface
└── screens/
    ├── screen1.py            # Each screen = one widget
    ├── screen2.py
    └── screen_n.py

Configuration & Utilities
├── config.py                 # Settings
└── utils.py                  # Reusable functions
```

---

## Common Extensions

### Adding a New Screen

**Step 1**: Create the screen file

```python
# screens/new_feature_screen.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class NewFeatureScreen(QWidget):
    back_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Feature Name")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back_btn)
        
        self.setLayout(layout)
```

**Step 2**: Register in main.py

```python
# In VisionScannerApp._init_screens()

from screens import NewFeatureScreen

# Add screen constant
SCREEN_NEW_FEATURE = 4  # Next available index

# Create and add widget
self.new_feature_screen = NewFeatureScreen()
self.stacked_widget.addWidget(self.new_feature_screen)  # Index 4
```

**Step 3**: Connect signals

```python
# In VisionScannerApp._connect_signals()

self.new_feature_screen.back_clicked.connect(self._go_to_main)
# Add other navigation as needed
```

**Step 4**: Add navigation method

```python
# In VisionScannerApp

def _on_new_feature_clicked(self):
    """Navigate to new feature screen."""
    self.stacked_widget.setCurrentIndex(self.SCREEN_NEW_FEATURE)
```

### Connecting Real API

**Instead of**:
```python
QMessageBox.information(self, "API Call", "Вызов API: /infer")
```

**Use this pattern**:
```python
import requests
import json
from urllib.error import URLError

def _call_inference_api(self, image_path: str):
    """
    Call the inference API with an image.
    
    Args:
        image_path: Path to image file
    """
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(
                "http://your-api.com/infer",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            self._handle_inference_result(result)
        else:
            self.camera_service.camera_error.emit(
                f"API Error: {response.status_code}"
            )
    
    except requests.Timeout:
        self.camera_service.camera_error.emit("API Timeout")
    except Exception as e:
        self.camera_service.camera_error.emit(f"API Error: {str(e)}")

def _handle_inference_result(self, result: dict):
    """Process API response."""
    QMessageBox.information(
        self,
        "Success",
        f"Detected objects: {result.get('count', 0)}"
    )
```

### Adding a Service (Database, API, etc.)

**Pattern**:

```python
# services/my_service.py

from PySide6.QtCore import QObject, Signal

class MyService(QObject):
    """Handles external service interaction (database, API, etc.)"""
    
    # Signals for error reporting
    error_occurred = Signal(str)
    
    # Signals for data events
    data_received = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self._initialize()
    
    def _initialize(self):
        """Initialize the service."""
        pass
    
    def fetch_data(self, query: str):
        """
        Fetch data from service.
        
        Args:
            query: Search query or ID
        """
        try:
            # Do work here
            result = {}
            self.data_received.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def cleanup(self):
        """Clean up service resources."""
        pass
    
    def __del__(self):
        """Ensure cleanup on deletion."""
        self.cleanup()
```

**Use in main.py**:

```python
from services.my_service import MyService

class VisionScannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.my_service = MyService()
        self.my_service.error_occurred.connect(self._on_service_error)
        # ... rest of init
    
    def _on_service_error(self, error: str):
        QMessageBox.critical(self, "Error", error)
    
    def closeEvent(self, event):
        self.camera_service.cleanup()
        self.my_service.cleanup()  # Add service cleanup
        event.accept()
```

### Custom Button Wrapper

```python
# In utils.py

from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

class TouchButton(QPushButton):
    """Touchscreen-optimized button with consistent styling."""
    
    def __init__(self, text: str, min_height: int = 80, font_size: int = 12):
        super().__init__(text)
        self.setMinimumHeight(min_height)
        
        font = QFont()
        font.setPointSize(font_size)
        font.setBold(True)
        self.setFont(font)
        
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            TouchButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            TouchButton:pressed {
                background-color: #005a9e;
            }
            TouchButton:hover {
                background-color: #1084d7;
            }
        """)

# Usage in screens:
btn = TouchButton("Click Me", min_height=100, font_size=14)
```

### Global Stylesheet

```python
# In main.py, VisionScannerApp.__init__()

def _setup_global_style(self):
    """Configure global application styling."""
    stylesheet = """
        QWidget {
            font-family: Arial, sans-serif;
            font-size: 11pt;
        }
        
        QPushButton {
            background-color: #007acc;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QTableWidget {
            background-color: white;
            alternate-background-color: #f5f5f5;
            gridline-color: #ddd;
        }
        
        QHeaderView::section {
            background-color: #e0e0e0;
            padding: 4px;
            border: 1px solid #999;
            font-weight: bold;
        }
    """
    
    QApplication.setStyle("Fusion")  # Use Fusion style
    self.setStyleSheet(stylesheet)

# Call in __init__:
self._setup_global_style()
```

---

## Debugging Tips

### Enable Logging

```python
# Add to config.py

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("VisionScanner")
```

### Log Important Events

```python
# In main.py

import logging
logger = logging.getLogger("VisionScanner")

def _on_main_scan_clicked(self):
    logger.info("Scan button clicked")
    frame = self.camera_service.capture_frame()
    if frame is None:
        logger.error("Failed to capture frame")
        return
    logger.debug(f"Frame size: {frame.shape}")
    # ... rest
```

### Test Camera

```python
import cv2

cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print(f"✓ Camera working. Frame shape: {frame.shape}")
    else:
        print("✗ Camera opened but cannot read frames")
else:
    print("✗ Camera not accessible")
cap.release()
```

### Test UI Thread Blocking

```python
# Add to screen init
import time

def test_blocking(self):
    """This blocks the UI - DON'T do this!"""
    time.sleep(5)  # WRONG

# Use timer instead:
def do_something_later(self):
    """This doesn't block the UI - DO this!"""
    timer = QTimer()
    timer.singleShot(5000, self.my_callback)

def my_callback(self):
    print("Called after 5 seconds")
```

---

## Performance Tips

### Image Processing in Background

```python
import threading

def process_image_background(self, image_path: str):
    """Process image in background thread."""
    def _process():
        # Expensive operation
        processed = heavy_computation(image_path)
        self.image_ready.emit(processed)
    
    thread = threading.Thread(target=_process, daemon=True)
    thread.start()
```

### Optimized Frame Scaling

```python
from PySide6.QtGui import QPixmap

def display_frame(self, frame):
    """Display frame efficiently."""
    pixmap = QPixmap.fromImage(cv2_to_qimage(frame))
    
    # Scale to display size, not full resolution
    max_height = self.label.height()
    scaled = pixmap.scaledToHeight(
        max_height,
        Qt.SmoothTransformation  # Best quality
    )
    
    self.label.setPixmap(scaled)
```

### Memory Management

```python
# Store images efficiently
self.last_pixmap = None  # Not full frame

# Clear old images
def cleanup_old_files(self, folder: str, hours: int = 24):
    """Delete images older than N hours."""
    import os
    from datetime import datetime, timedelta
    
    cutoff = datetime.now() - timedelta(hours=hours)
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        mtime = os.path.getmtime(filepath)
        if datetime.fromtimestamp(mtime) < cutoff:
            os.remove(filepath)
```

---

## Error Handling Best Practices

### Graceful Degradation

```python
def _on_feature_clicked(self):
    """Attempt feature with fallback."""
    try:
        result = self.do_something()
    except FileNotFoundError:
        logger.warning("File not found, using default")
        result = self.get_default()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        QMessageBox.warning(self, "Error", "Something went wrong")
        return
    
    self.process_result(result)
```

### Validation

```python
def validate_image(image_path: str) -> bool:
    """Check if image is valid."""
    try:
        img = cv2.imread(image_path)
        if img is None or img.size == 0:
            return False
        return True
    except Exception:
        return False

def _on_image_selected(self, path: str):
    if not validate_image(path):
        QMessageBox.warning(self, "Invalid Image", 
                          "Cannot read this image file")
        return
    # Process valid image
```

---

## Testing Template

```python
# test_app.py

import pytest
from PySide6.QtWidgets import QApplication
from main import VisionScannerApp

@pytest.fixture
def app():
    """Create application instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    window = VisionScannerApp()
    yield window
    app.quit()

def test_main_screen_visible(app):
    """Test main screen loads."""
    assert app.stacked_widget.currentIndex() == 0

def test_camera_service_initialized(app):
    """Test camera service exists."""
    assert app.camera_service is not None

def test_screen_navigation(app):
    """Test screen switching."""
    app.stacked_widget.setCurrentIndex(1)
    assert app.stacked_widget.currentIndex() == 1
```

---

## Code Review Checklist

Before committing new code:

- [ ] Code follows naming conventions (snake_case for functions)
- [ ] All classes have docstrings
- [ ] All methods have type hints where possible
- [ ] No hardcoded values (use config.py)
- [ ] Error handling present
- [ ] No UI blocking operations
- [ ] Signals properly connected
- [ ] Resources cleaned up properly
- [ ] Code tested manually
- [ ] Comments explain WHY not WHAT

---

## Resources

- **PySide6 Docs**: https://doc.qt.io/qtforpython/
- **PyQt/PySide Patterns**: https://doc.qt.io/qtforpython/overviews/index.html
- **OpenCV Docs**: https://docs.opencv.org/
- **Python Type Hints**: https://docs.python.org/3/library/typing.html

---

Happy coding! 🚀
