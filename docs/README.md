# Vision Scanner - PySide6 Touchscreen Application

A minimalist, touchscreen-friendly Python application built with PySide6 (Qt6) for capturing and managing part images using a webcam.

## Features

- **Multi-screen interface** with QStackedWidget
- **Camera capture** using OpenCV (cv2)
- **Image collection** with automatic capture intervals
- **Touchscreen-optimized UI** with large buttons and clear layouts
- **Modular architecture** for easy extension and maintenance
- **API simulation** dialogs for future backend integration

## Project Structure

```
visions15/
├── main.py                          # Application entry point
├── camera_service.py                # Camera handling (CameraService class)
├── utils.py                         # Image utilities and helper functions
├── requirements.txt                 # Python dependencies
├── captures/                        # Directory for single captured images
├── dataset_temp/                    # Directory for bulk image collection
└── screens/
    ├── __init__.py
    ├── main_screen.py               # Main scanner interface
    ├── image_viewer_screen.py       # Image view screen
    ├── part_selection_screen.py     # Part selection interface
    └── image_collection_screen.py   # Dataset collection interface
```

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- PySide6 (Qt6 bindings for Python)
- opencv-python (cv2 - camera and image processing)

### 2. Prepare Directories

The application will automatically create these directories if they don't exist:
- `captures/` - for single image snapshots
- `dataset_temp/` - for bulk image collection sessions

## Usage

### Run the Application

```bash
python main.py
```

### Screen Navigation

1. **Main Screen** (default)
   - View captured parts in a table
   - **Scan** button: Capture single image → simulates `/infer` API call
   - **Add Part** button: Opens part selection screen
   - **Show Image** button: View last captured image

2. **Image Viewer Screen**
   - Displays the last captured image in full view
   - **Back** button: Return to main screen

3. **Part Selection Screen**
   - Browse available parts (sample data included)
   - Search field (placeholder for future implementation)
   - **Select** button: Choose part and go to image collection
   - **Back** button: Return to main screen

4. **Image Collection Screen**
   - Live camera feed with visual frame guide
   - Image counter showing captured photos
   - **Take Photo** button: Single manual capture
   - **Start** button: Begin automatic capture (1 second interval)
   - **Pause** button: Pause automatic capture
   - **Stop** button: End session → simulates `/upload_images` API call
   - **Back** button: Return to main screen

## Camera Configuration

The application uses OpenCV to access the default camera (index 0):

```python
self.cap = cv2.VideoCapture(0)
```

**Camera settings:**
- Resolution: 640×480
- FPS: 30
- Single thread for entire application

To use a different camera:
1. Edit `camera_service.py`
2. Change `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)` (or other index)

## Image File Organization

### Single Capture
- Saved to: `captures/`
- Filename: `YYYYMMDD_HHMMSS_mmm.jpg` (timestamp)

### Bulk Collection
- Saved to: `dataset_temp/`
- Filename: `YYYYMMDD_HHMMSS_mmm.jpg` (timestamp)

## Code Architecture

### CameraService (`camera_service.py`)
- Manages camera lifecycle
- Runs capture loop in separate thread
- Signals: `frame_ready`, `camera_error`
- Methods: `start_stream()`, `stop_stream()`, `capture_frame()`, `save_image()`

### Screens
Each screen is a separate QWidget class:

- **MainScreen**: Table management, scan/add/view buttons
- **ImageViewerScreen**: Image display widget
- **PartSelectionScreen**: Part selection table
- **ImageCollectionScreen**: Live camera feed, capture controls

### VisionScannerApp (`main.py`)
Main window using QStackedWidget for screen navigation:
- Manages camera service (shared across all screens)
- Handles navigation between screens
- Coordinates signals from all screens
- Manages state (last image path, etc.)

## Extending the Application

### Adding New Screens

1. Create a new screen class in `screens/`:
   ```python
   from PySide6.QtWidgets import QWidget
   from PySide6.QtCore import Signal
   
   class NewScreen(QWidget):
       back_clicked = Signal()
       
       def __init__(self):
           super().__init__()
           self._init_ui()
   ```

2. Add to `screens/__init__.py`

3. Register in `VisionScannerApp._init_screens()`:
   ```python
   self.new_screen = NewScreen()
   self.stacked_widget.addWidget(self.new_screen)
   ```

4. Connect signals in `_connect_signals()`

### Connecting Real API

Replace the `QMessageBox.information()` calls with actual API requests:

```python
# Instead of:
self.main_screen.show_api_call_dialog("/infer")

# Use actual API:
import requests
response = requests.post("http://api.example.com/infer", 
                         files={"image": open(image_path, "rb")})
```

### Custom Button Styling

Modify `_create_button()` methods or add stylesheets:

```python
btn.setStyleSheet("""
    QPushButton {
        background-color: #007acc;
        color: white;
        border-radius: 5px;
    }
    QPushButton:pressed {
        background-color: #005a9e;
    }
""")
```

## Troubleshooting

### Camera Not Working
- Ensure a camera is connected and accessible
- Check camera permissions (on Linux/macOS)
- Try changing camera index in `camera_service.py`

### Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.8+ required)

### Qt Platform Plugin Error
- On Linux: `sudo apt-get install libxkbcommon-x11-0`
- On macOS: Reinstall Qt bindings: `pip install --force-reinstall PySide6`

## Future Enhancements

- [ ] Real API integration
- [ ] Object detection with bounding boxes
- [ ] Part recognition and classification
- [ ] Database integration for parts inventory
- [ ] Multi-camera support
- [ ] Image annotation tools
- [ ] Batch processing capabilities
- [ ] Settings/configuration screen
- [ ] Data export functionality

## License

This project is provided as-is for educational and development purposes.

## Author

Created with PySide6 and OpenCV for touchscreen applications.
