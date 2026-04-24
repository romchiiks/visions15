"""
Configuration file for the Vision Scanner application.
Centralized settings for easy customization.
"""

# Application Settings
APP_TITLE = "Visions15"
APP_WIDTH = 1024
APP_HEIGHT = 768

# Camera Settings
CAMERA_INDEX = 0  # Default camera device (0 = default)
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Image Capture Settings
CAPTURE_FOLDER = "captures"  # Folder for single snapshots
DATASET_FOLDER = "dataset_temp"  # Folder for bulk image collection
IMAGE_FORMAT = "jpg"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S_%f"  # Include milliseconds

# Auto-Capture Settings
AUTO_CAPTURE_INTERVAL_MS = 1000  # 1 second between auto-captures

# UI Settings
BUTTON_MIN_HEIGHT = 100
BUTTON_FONT_SIZE = 12
BUTTON_FONT_BOLD = True

TITLE_FONT_SIZE = 16
TITLE_FONT_BOLD = True

# Camera Frame Display
FRAME_MARGIN = 30  # Margin for visual frame rectangle
FRAME_COLOR = (0, 255, 0)  # RGB color (green)
FRAME_THICKNESS = 3

# Image Viewer
IMAGE_VIEWER_MAX_HEIGHT = 400

# Part Selection Sample Data
# Can be replaced with database query or API call
SAMPLE_PARTS = [
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

# API Settings (for future integration)
# Replace with actual API endpoints when ready
API_BASE_URL = "http://localhost:8000"  # Change to your API URL
API_INFER_ENDPOINT = "/infer"
API_UPLOAD_ENDPOINT = "/upload_images"
API_TIMEOUT_SECONDS = 30

# Debug Settings
DEBUG_MODE = True  # Set to True for debug logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
