# On-Screen Keyboard Feature Documentation

## Overview

The Vision Scanner now includes an on-screen touchscreen keyboard for text input. This feature is essential for touchscreen devices that may not have physical keyboards attached.

## Keyboard Components

### OnScreenKeyboard Widget (`widgets/keyboard.py`)

A reusable PySide6 widget that provides touchscreen-optimized text input.

**Features**:
- Letters: A-Z (displayed, input as lowercase a-z)
- Numbers: 0-9
- Special characters: `-` (hyphen), `_` (underscore)
- Backspace button: Remove last character
- Clear button: Clear entire input
- Built-in QLineEdit for display
- Signal-based communication

**Usage**:
```python
from widgets.keyboard import OnScreenKeyboard

keyboard = OnScreenKeyboard()
keyboard.text_changed.connect(on_text_changed)
```

**Public Methods**:
- `get_text()` - Get current input text
- `set_text(text)` - Set text programmatically
- `clear()` - Clear input
- `set_external_field(line_edit)` - Connect to external QLineEdit

**Signals**:
- `text_changed(str)` - Emitted when text changes

---

## Integration Points

### 1. Part Selection Screen (`screens/part_selection_screen.py`)

**Feature**: Search parts using on-screen keyboard

The keyboard is now integrated into the part selection screen's search functionality.

**How it works**:
1. User types part name or code using the keyboard
2. Table filters in real-time as you type
3. Shows only matching parts
4. Clear or backspace to modify search

**Key Methods**:
- `_on_search_text_changed(search_text)` - Filter logic
- `_refresh_table()` - Update table display with filtered results

**Example search**:
- Type: `r` → Shows "Резистор 10кОм / 10K Resistor"
- Type: `r001` → Shows "R001" part
- Clear → Shows all parts

---

### 2. Custom Part Input Screen (`screens/custom_part_input_screen.py`)

**Feature**: Add custom parts with user-defined names

New dedicated screen for entering custom part names using the keyboard.

**Navigation**:
```
Main Screen
  ↓ (Add Part)
Part Selection Screen + Keyboard (search)
  ↓ (+ Custom button)
Custom Part Input Screen + Keyboard (enter name)
  ↓ (Done)
Image Collection Screen
```

**Workflow**:
1. User clicks "Add Part" from main screen
2. Part selection screen shows with search keyboard
3. User clicks "+ Custom" button
4. Custom part input screen appears with large keyboard
5. User enters part name (e.g., "R820")
6. User clicks "Done"
7. Proceeds to image collection with custom part

**Methods**:
- `get_entered_text()` - Get current input
- `reset()` - Clear for new entry

---

## Screen Navigation Flow

```
┌─────────────┐
│ Main Screen │
└──────┬──────┘
       │ "Add Part"
       ↓
┌──────────────────────────┐
│ Part Selection Screen     │
├──────────────────────────┤
│ Keyboard (Search enabled)│
│ - Filter by name/code    │
│ - Real-time results      │
│ - 5 sample parts         │
├──────────────────────────┤
│ [Select] [Custom] [Back] │
└──────┬────────┬──────────┘
       │        │ "+ Custom"
       │        ↓
       │   ┌──────────────────────────┐
       │   │ Custom Part Input Screen  │
       │   ├──────────────────────────┤
       │   │ Keyboard (Enter name)    │
       │   │ - Large, prominent       │
       │   │ - For custom part naming │
       │   ├──────────────────────────┤
       │   │ [Done] [Back]            │
       │   └────────┬─────────────────┘
       │            │ "Done"
       │            ↓
       └─────┬──────┘
             │ [Select] from list
             ↓
       ┌──────────────────────────┐
       │ Image Collection Screen   │
       interface-button│ Start/Stop auto-capture    │
       │ Take Photo               │
       │ [Back]                   │
       └──────────────────────────┘
```

---

## Keyboard Button Layout

### Character Layout

**Row 1 (Letters)**: Q W E R T Y U I O P  
**Row 2 (Letters)**: A S D F G H J K L  
**Row 3 (Letters)**: Z X C V B N M  
**Row 4 (Numbers)**: 0 1 2 3 4 5 6 7 8 9  
**Row 5 (Special)**: `-` `_`

### Control Buttons

**Backspace Row**: `← Стереть / Backspace` (wide, red button)  
**Clear Row**: `✕ Очистить / Clear` (wide, orange button)

---

## Keyboard Styling

### Button Styles

```python
# Regular key buttons
Background: #007acc (blue)
Pressed: #005a9e (darker blue)
Hover: #1084d7 (lighter blue)
Text: white, bold, 12pt font

# Backspace button
Background: #d9534f (red)
Pressed: #ac2925 (darker red)
Text: white, bold, 11pt font

# Clear button
Background: #f0ad4e (orange)
Pressed: #ec971f (darker orange)
Text: white, bold, 11pt font
```

### Input Field

- Minimum height: 40px
- Font size: 14pt
- Read-only (controlled only by keyboard)
- Clear display of current text

---

## Usage Examples

### Example 1: Search for Parts

```python
# User workflow:
# 1. See part selection screen
# 2. Keyboard is visible below title
# 3. Click key "R" → filters to show "Резистор 10кОм"
# 4. Click key "0", then "0", then "1" → further narrows to R001
# 5. Click [Select] → choose this part
# 6. Proceed to image collection
```

### Example 2: Add Custom Part

```python
# User workflow:
# 1. In part selection, click "+ Custom" button
# 2. Go to custom part input screen
# 3. Use keyboard to type: "R820"
# 4. Click [Done]
# 5. Custom part created: {"name": "R820", "code": "CUSTOM_R820", ...}
# 6. Proceed to image collection for "R820"
```

### Example 3: Modify Search

```python
# User workflow:
# 1. Typed "resistor" but needs to correct
# 2. Click backspace 3 times → removes "tor"
# 3. Now shows "resistor" filtered results, then "resiste", "resist"
# 4. Type new text instead
# 5. Or click clear button to start over
```

---

## Keyboard Features

### Text Input Validation

The keyboard naturally restricts input to:
- **Letters**: a-z (automatically converted to lowercase)
- **Numbers**: 0-9
- **Special**: `-`, `_`

**Benefits**:
- No invalid characters can be entered
- Natural filtering for part codes
- Suitable for filenames and identifiers

### Real-Time Feedback

**In Part Selection**:
- Type → Immediately see filtered results
- Each keystroke updates the table
- No need for separate "search" button

**In Custom Part Input**:
- Text displayed in input field
- User sees exactly what they typed
- Can backspace to fix before confirming

### Accessibility

- **Large buttons**: 45×45px minimum (touchscreen-friendly)
- **Clear labeling**: Bilingual (Russian/English)
- **High contrast**: Blue buttons with white text
- **Distinct controls**: Red backspace, orange clear
- **No typing required**: Hardware keyboard optional

---

## Integration with Application State

### Part Selection Flow

```python
# In main.py
class VisionScannerApp(QMainWindow):
    SCREEN_PART_SELECTION = 2
    SCREEN_CUSTOM_PART_INPUT = 4
    
    def _on_main_add_part_clicked(self):
        # Navigate to part selection
        self.stacked_widget.setCurrentIndex(self.SCREEN_PART_SELECTION)
    
    def _on_custom_part_requested(self):
        # Navigate to custom part input
        self.custom_part_input_screen.reset()
        self.stacked_widget.setCurrentIndex(self.SCREEN_CUSTOM_PART_INPUT)
    
    def _on_custom_part_name_entered(self, part_name: str):
        # Create custom part and proceed to image collection
        custom_part = {
            "name": part_name,
            "code": f"CUSTOM_{part_name.upper()[:4]}",
            "description": "Custom part added by user"
        }
        self._on_part_selected(custom_part)
```

---

## Configuration Options

### In `config.py`

```python
# Keyboard Character Set
KEYBOARD_LAYOUT = {
    'letters': 'QWERTYUIOPASDFGHJKLZXCVBNM',
    'numbers': '0123456789',
    'special': '-_'
}

# Keyboard Button Styling
KEYBOARD_BUTTON_MIN_HEIGHT = 45
KEYBOARD_BUTTON_MIN_WIDTH = 45
KEYBOARD_FONT_SIZE = 12
```

### Customizing Character Set

To add more characters, modify `OnScreenKeyboard._init_ui()`:

```python
# Example: Add @ symbol
keyboard = [
    ...existing rows...,
    ['@', '/', '\\'],  # New row
]
```

---

## Testing the Keyboard

### Manual Test Cases

1. **Basic Text Input**
   - Click letters → Text appears in field
   - Text is lowercase
   - Expected: "hello"

2. **Numbers**
   - Click number keys → Numbers appear
   - Expected: "12345"

3. **Special Characters**
   - Click `-` → Appears
   - Click `_` → Appears
   - Expected: "R-820_v2"

4. **Backspace**
   - Type "test"
   - Click backspace 2 times
   - Expected: "te"

5. **Clear**
   - Type "test"
   - Click clear
   - Expected: "" (empty)

6. **Part Selection Filter**
   - Type "R" in keyboard
   - Expected: Table filters to show resistor parts
   - Clear and type "C"
   - Expected: Table filters to show capacitor parts

7. **Custom Part Add**
   - Part selection → Click "+ Custom"
   - Type "MyPart" in keyboard
   - Click "Done"
   - Expected: Proceeds to image collection for "MyPart"

---

## Troubleshooting

### Keyboard Not Appearing

**Issue**: Keyboard widget not visible on screen

**Solutions**:
- Check if parent layout has `addWidget(keyboard)` call
- Verify screen is set to `setCurrentIndex()` correctly
- Check window size is sufficient (minimum 800×600)

### Text Not Updating

**Issue**: Keyboard buttons clicked but text doesn't appear

**Solutions**:
- Verify signal connection: `text_changed.connect()`
- Check if QLineEdit is read-only (it should be)
- Verify `_on_key_pressed()` is called

### Search Not Filtering

**Issue**: Text appears but table doesn't filter

**Solutions**:
- Verify `_on_search_text_changed()` is called
- Check filter logic in `_refresh_table()`
- Ensure part data is properly loaded

### Custom Part Not Created

**Issue**: Text entered but custom part not created

**Solutions**:
- Check if "Done" button calls `part_name_entered.emit()`
- Verify part name is not empty
- Check if `_on_custom_part_name_entered()` is connected

---

## Future Enhancements

### Potential Additions

1. **Uppercase toggle**: Switch between a-z and A-Z
2. **Space character**: Add spacing in part names
3. **Additional symbols**: @, /, \, etc.
4. **Word suggestions**: Auto-complete common part names
5. **Numeric pad layout**: Alternative number arrangement
6. **Shift/caps**: For uppercase letters
7. **Multi-language**: Switch keyboard layouts (Russian/English)
8. **Clipboard**: Paste functionality for external input
9. **Delete key**: Selectively delete characters
10. **Keyboard themes**: Dark mode, accessibility modes

---

## Performance Considerations

### Memory

- Keyboard widget: ~100-200 KB
- Input buffer: Minimal (short part names)
- No image caching in text input

### CPU

- Signal-slot calls: Very fast
- Table filtering: O(n) where n = number of parts
- No expensive string operations

### Optimization Tips

```python
# Use .lower() once, not per comparison
search_lower = search_text.lower()  # Do this once
for part in self.parts_data:
    if search_lower in part["name"].lower():  # Already lowercase
        ...

# Use list comprehension for filtering
filtered = [
    idx for idx, part in enumerate(self.parts_data)
    if condition(part)
]
```

---

## API Reference

### OnScreenKeyboard Class

```python
class OnScreenKeyboard(QWidget):
    # Signals
    text_changed = Signal(str)
    
    # Constructor
    __init__(self, parent=None)
    
    # Public Methods
    get_text(self) -> str
    set_text(self, text: str) -> None
    clear(self) -> None
    set_external_field(self, line_edit: QLineEdit) -> None
```

### PartSelectionScreen Integration

```python
class PartSelectionScreen(QWidget):
    # Signals
    part_selected = Signal(dict)
    custom_part_requested = Signal()
    back_clicked = Signal()
    
    # Attributes
    keyboard: OnScreenKeyboard
    table: QTableWidget
    
    # Methods
    _on_search_text_changed(self, search_text: str) -> None
    _refresh_table(self) -> None
```

### CustomPartInputScreen

```python
class CustomPartInputScreen(QWidget):
    # Signals
    part_name_entered = Signal(str)
    back_clicked = Signal()
    
    # Attributes
    keyboard: OnScreenKeyboard
    
    # Methods
    reset(self) -> None
    get_entered_text(self) -> str
```

---

## Files Modified/Created

**New Files**:
- `widgets/keyboard.py` - OnScreenKeyboard widget
- `widgets/__init__.py` - Package initialization
- `screens/custom_part_input_screen.py` - Custom part input screen

**Modified Files**:
- `screens/part_selection_screen.py` - Added keyboard integration
- `screens/__init__.py` - Added new screen export
- `main.py` - Screen registration and navigation handling

**Total Changes**: 6 files (3 new, 3 modified)

---

**Last Updated**: March 19, 2026

For questions on keyboard implementation, refer to the source code documentation in the respective files.
