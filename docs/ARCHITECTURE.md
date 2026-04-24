# Vision Scanner - Architecture Guide

## System Overview

The Vision Scanner is a modular PySide6 touchscreen application for capturing and managing part images. It uses a clean separation of concerns with dedicated services and UI components.

```
┌─────────────────────────────────────────────────────────────┐
│                  VisionScannerApp (Main Window)              │
│              Uses QStackedWidget for navigation              │
└────────┬────────────┬────────────┬────────────┬──────────────┘
         │            │            │            │
    ┌────▼────┐  ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
    │  Main   │  │ Image   │  │  Part  │  │ Image  │
    │ Screen  │  │ Viewer  │  │Selection│ │Collection│
    │         │  │ Screen  │  │ Screen │  │ Screen │
    └────┬────┘  └────┬────┘  └───┬────┘  └───┬────┘
         │            │            │            │
         └────────────┼────────────┼────────────┘
                      │
              ┌───────▼────────┐
              │  CameraService │
              │   (Shared)     │
              │                │
              │ • Frame capture│
              │ • Image saving │
              │ • Threading    │
              └────────────────┘
```

## Component Architecture

### 1. Main Application (VisionScannerApp)

**File**: `main.py`

**Responsibilities**:
- Window management and initialization
- Screen lifecycle management
- Navigation coordination between screens
- Camera service lifecycle
- Global state management (last_image_path)

**Key Methods**:
- `__init__()`: Initialize all screens and signals
- `_init_screens()`: Create and register screens in QStackedWidget
- `_connect_signals()`: Wire up navigation signals
- Navigation methods: `_go_to_main()`, etc.
- Signal handlers: `_on_main_scan_clicked()`, etc.

**Relationships**:
- Owns: CameraService instance (shared)
- Contains: All 4 screen widgets
- Parent of: All signal connections

### 2. Camera Service

**File**: `camera_service.py`

**Class**: `CameraService(QObject)`

**Responsibilities**:
- Camera device lifecycle (initialization, capture, cleanup)
- Frame streaming in background thread
- Image persistence to disk
- Error handling and reporting

**Signals**:
- `frame_ready(frame)`: Emitted when new frame is available
- `camera_error(message)`: Emitted on camera errors

**Key Methods**:
- `start_stream()`: Begin continuous frame capture
- `stop_stream()`: Stop frame capture  
- `capture_frame()`: Get single frame
- `save_image(frame, folder)`: Save frame to disk
- `cleanup()`: Release camera resources

**Threading**:
```
Main Thread: UI
└─ Camera Service
   └─ Capture Thread (_capture_loop)
      └─ Continuous camera.read() in loop
```

**Design Pattern**: Observer pattern (signals) + Threading

### 3. UI Components (Screens)

All screens inherit from `QWidget` and contain UI setup + logic.

#### 3.1 MainScreen

**File**: `screens/main_screen.py`

**Signals**:
- `scan_clicked`
- `add_part_clicked`
- `show_image_clicked`

**Elements**:
- QTableWidget: Parts table (4 columns)
- QPushButton: Scan, Add Part, Show Image
- QLabel: Status, title

**Methods**:
- `add_table_row()`: Insert row to table
- `set_undefined_objects_count()`: Update counter
- `show_api_call_dialog()`: Display API simulation

#### 3.2 ImageViewerScreen

**File**: `screens/image_viewer_screen.py`

**Signals**:
- `back_clicked`

**Elements**:
- QLabel: Image display area
- QPushButton: Back button

**Methods**:
- `display_image(path)`: Load and display image
- `clear_display()`: Clear displayed image

#### 3.3 PartSelectionScreen

**File**: `screens/part_selection_screen.py`

**Signals**:
- `part_selected(part_dict)`: Dictionary with name, code, description
- `back_clicked`

**Elements**:
- QTableWidget: Parts table (3 columns)
- QLineEdit: Search field (placeholder)
- QPushButton: Select, Back

**Data Source**:
- `_get_sample_parts()`: Returns hardcoded sample data
- Can be replaced with database query or API call

#### 3.4 ImageCollectionScreen

**File**: `screens/image_collection_screen.py`

**Signals**:
- `back_clicked`

**Elements**:
- QLabel: Camera display (receives frames from CameraService)
- QLabel: Image counter
- QPushButton: Start, Pause, Stop, Take Photo, Back
- QTimer: Auto-capture timer

**State**:
- `image_counter`: Count of captured images
- `is_capturing`: Auto-capture active
- `auto_capture_timer`: QTimer for auto-capture

**Methods**:
- `_on_frame_ready()`: Receive frame and display with visual frame
- `_on_photo_clicked()`: Capture single image
- `_on_start_clicked()`: Begin auto-capture (1s interval)
- `_on_pause_clicked()`: Pause auto-capture
- `_on_stop_clicked()`: End session
- `reset()`: Clear counter for new session

**Frame Processing**:
```
CameraService emits frame_ready signal
    ↓
ImageCollectionScreen._on_frame_ready()
    ↓
draw_frame_rect() adds visual guide
    ↓
cv2_to_qimage() converts to Qt format
    ↓
Display in QLabel
```

### 4. Utilities

**File**: `utils.py`

**Functions**:

- `cv2_to_qimage(cv_image)`: Convert OpenCV numpy array to QImage
  - Handles BGR→RGB conversion
  - Manages dimensions and byte alignment
  
- `load_image_from_file(filepath)`: Load QPixmap from file

- `draw_frame_rect(frame, thickness, color)`: Draw rectangle on frame
  - Used for visual guide in image collection

**Dependencies**: cv2, PySide6.QtGui

### 5. Configuration

**File**: `config.py`

**Purpose**: Centralized configuration for easy customization

**Sections**:
- App Settings: Window size, title
- Camera Settings: Index, resolution, FPS
- Image Capture: Folder paths, filename format
- UI Settings: Button sizes, fonts
- Part Data: Sample parts
- API Settings: Endpoints (for future integration)
- Debug Settings: Logging configuration

## Data Flow Diagrams

### Scan Button Flow

```
User clicks Scan
    ↓
VisionScannerApp._on_main_scan_clicked()
    ↓
CameraService.capture_frame() → frame
    ↓
CameraService.save_image(frame, "captures") → filepath
    ↓
Store in app.last_image_path
    ↓
MainScreen.show_api_call_dialog("/infer")
```

### Image Capture Flow

```
ImageCollectionScreen starts
    ↓
showEvent() → camera_service.start_stream()
    ↓
CameraService thread continuously calls camera.read()
    ↓
frame_ready signal emitted every ~33ms
    ↓
ImageCollectionScreen._on_frame_ready(frame)
    ↓
draw_frame_rect() + cv2_to_qimage()
    ↓
Display in camera_label
    ↓
(User clicks Take Photo)
    ↓
capture_frame() → save_image() → counter++
```

### Auto-Capture Flow

```
User clicks Start
    ↓
QTimer created with 1000ms interval
    ↓
Timer timeout → _on_auto_capture_timer()
    ↓
Call _on_photo_clicked()
    ↓
Capture and save image
    ↓
Increment counter
    ↓
(Repeat or user clicks Stop)
    ↓
Stop timer
    ↓
Show API dialog "/upload_images"
```

## Navigation State Machine

```
Main Screen
├─ [Scan] → API dialog → Main Screen
├─ [Add Part] → Part Selection Screen
│                 ├─ [Select] → Image Collection Screen
│                 │              ├─ [Back] → Main Screen
│                 │              └─ [Stop] → API dialog → Main Screen
│                 └─ [Back] → Main Screen
└─ [Show Image] → Image Viewer Screen
                  └─ [Back] → Main Screen
```

Implementation: `QStackedWidget` with `setCurrentIndex()`

## Threading Model

### Main Thread (UI)
- Qt event loop
- UI updates
- Button clicks
- Signal emissions

### Camera Thread (Background)
- OpenCV continuous capture
- Frame read loop (blocking on `camera.read()`)
- Emits `frame_ready` signal

```
Main Thread          Camera Thread
    │                    │
    ├─ start_stream() ──►│
    │                    ├─ while is_running:
    │                    │    frame = cap.read()
    │                    │    emit frame_ready(frame)
    │                    │
    ├ display frame◄─────┤
    │                    │
    ├─ stop_stream() ───►│
    │                    └─ exit loop
    │
```

**Thread Safety**:
- `frame_ready` signal is thread-safe
- `is_running` flag controls loop
- Main thread calls `join(timeout=2)` when stopping

## Error Handling

### Camera Errors
```
Camera fails → CameraService.camera_error signal
    ↓
VisionScannerApp._on_camera_error()
    ↓
QMessageBox.critical() displays error
```

### Image Save Errors
```
save_image() fails → emit camera_error signal
    ↓
(Same as above)
```

### Frame Capture Errors
```
capture_frame() returns None
    ↓
Check at button handler
    ↓
QMessageBox.warning()
```

## Extension Points

### 1. Adding New Screens

1. Create `screens/new_screen.py`
2. Inherit from `QWidget`, define signals
3. Add to `VisionScannerApp._init_screens()`
4. Connect signals in `_connect_signals()`
5. Add navigation methods

### 2. Real API Integration

Replace `QMessageBox` calls with:
```python
import requests

response = requests.post(
    "http://api.example.com/infer",
    files={"image": file},
    json=metadata
)
```

### 3. Database Integration

Replace part sample data with:
```python
# In PartSelectionScreen._get_sample_parts()
from database import get_parts
return get_parts()
```

### 4. Image Processing

Add to `ImageCollectionScreen._on_photo_clicked()`:
```python
# Process image before saving
processed = apply_filters(frame)
self.camera_service.save_image(processed, folder)
```

### 5. Styling

Global stylesheet in `VisionScannerApp.__init__()`:
```python
stylesheet = """
    QWidget { font-size: 14px; }
    QPushButton { background-color: #007acc; }
"""
self.setStyleSheet(stylesheet)
```

## Dependencies

- **PySide6**: Qt6 bindings for Python
- **opencv-python (cv2)**: Camera and image processing
- **Python 3.8+**: Standard library

No other heavy dependencies to keep it lightweight.

## Performance Considerations

### Memory
- Camera frames (~1MB each) held in memory briefly
- QPixmap caching in image viewer
- Minimize stored frames in collection screen

### CPU
- Camera thread offloads capture loop
- UI thread responsive for buttons
- Frame display rate: ~30fps

### Threading
- One camera thread for entire app
- Efficient signal-based communication
- No busy-waiting

## Testing Points

1. Camera initialization and frame capture
2. Image saving to correct folders
3. Screen transitions and signal routing
4. Auto-capture timer functionality  
5. Window close and cleanup
6. Error handling (camera not found, save fails)

---

**Last Updated**: 2024

For questions, refer to README.md and QUICKSTART.md
