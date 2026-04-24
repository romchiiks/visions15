# Vision Scanner - Quick Start Guide

## 5-Minute Setup

### Step 1: Install Python Dependencies

Open terminal in the project directory and run:

```bash
# Windows
pip install -r requirements.txt

# Linux/macOS
pip3 install -r requirements.txt
```

Or use the provided scripts:
- **Windows**: Double-click `run.bat`
- **Linux/macOS**: Run `bash run.sh`

### Step 2: Connect a Webcam

Plug in a USB webcam or ensure your built-in camera is working.

### Step 3: Run the Application

```bash
python main.py
```

## Application Overview

### Screen 1: Main Scanner Interface
- **Scan**: Capture a single image and simulate API call
- **Add Part**: Select a part to collect training images
- **Show Image**: View the last captured image
- **Table**: Display of captured parts (initially empty)

### Screen 2: Image Viewer
- Shows the most recently captured image
- **Back**: Return to main screen

### Screen 3: Part Selection
- Browse available parts (5 sample parts included)
- **Select**: Choose a part and go to image collection
- **Back**: Return to main screen

### Screen 4: Image Collection
- Live camera feed with visual frame
- **Take Photo**: Manual single capture
- **Start**: Auto-capture every 1 second
- **Pause**: Pause auto-capture
- **Stop**: End session and show API confirmation
- **Back**: Return to main screen

## File Organization

```
Captured Files:
- Single snaps → captures/TIMESTAMP.jpg
- Dataset images → dataset_temp/TIMESTAMP.jpg
```

## Keyboard Shortcuts (Future)

Currently, use mouse/touch. Keyboard support can be added.

## Common Issues & Solutions

### "Камера не найдена / Camera not found"
- Check if webcam is connected
- Verify camera permissions (Linux/macOS)
- Try changing camera index in `config.py` (CAMERA_INDEX)

### "ModuleNotFoundError: No module named 'cv2'"
```bash
pip install opencv-python
```

### "ModuleNotFoundError: No module named 'PySide6'"
```bash
pip install PySide6
```

### Application won't start
1. Verify Python 3.8+: `python --version`
2. Reinstall packages: `pip install --force-reinstall -r requirements.txt`
3. Try with explicit Python path: `python3 main.py` (on macOS/Linux)

## Customization Tips

### Change Camera Index
Edit `config.py`:
```python
CAMERA_INDEX = 1  # Use second camera instead of default
```

### Modify Button Styles
Edit button styling in screen files:
```python
self.btn.setStyleSheet("""
    QPushButton { background-color: #007acc; }
""")
```

### Add More Sample Parts
Edit `config.py` -> `SAMPLE_PARTS` list

### Change Image Resolution
Edit `config.py`:
```python
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
```

## Next Steps

1. Test all screens and buttons
2. Verify images save correctly
3. Check captures/ and dataset_temp/ folders
4. Plan API integration
5. Develop actual image processing backend

## For Developers

### Adding a New Screen

1. Create `screens/new_screen.py`:
```python
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

class NewScreen(QWidget):
    back_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        # Your UI code here
        pass
```

2. Register in `main.py`:
```python
self.new_screen = NewScreen()
self.stacked_widget.addWidget(self.new_screen)
self.new_screen.back_clicked.connect(self._go_to_main)
```

### Connecting Real API

Replace mock dialogs with requests:
```python
import requests

response = requests.post(
    "http://your-api.com/infer",
    files={"image": open(image_path, "rb")},
    timeout=30
)
if response.status_code == 200:
    result = response.json()
```

## Support

For issues or questions:
1. Check the main `README.md`
2. Review code comments in relevant files
3. Test with simple modifications first

## Good Luck!

Enjoy building your vision scanning application! 🎉
