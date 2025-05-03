# UnitMCP Input Devices Examples

This directory contains examples demonstrating how to interact with input devices (keyboard, mouse) using the UnitMCP framework.

## Available Examples

### Keyboard Automation

The `keyboard_demo.py` example demonstrates keyboard automation capabilities:

```bash
# Run the keyboard automation demo
python keyboard_demo.py

# Run with specific key sequence
python keyboard_demo.py --sequence "Hello, UnitMCP!"
```

This example shows how to:
- Simulate keyboard input programmatically
- Send individual keystrokes and key combinations
- Create keyboard macros and sequences
- Handle special keys and modifiers (Ctrl, Alt, Shift)
- Monitor keyboard events and respond to them

### Mouse Automation

The `mouse_demo.py` example demonstrates mouse automation capabilities:

```bash
# Run the mouse automation demo
python mouse_demo.py

# Run with specific movement pattern
python mouse_demo.py --pattern "circle"
```

This example showcases:
- Controlling mouse cursor position
- Simulating mouse clicks (left, right, middle)
- Creating complex mouse movement patterns
- Implementing drag and drop operations
- Monitoring mouse events and responding to them

## Input Device Features

The UnitMCP input device module provides several capabilities:

### 1. Keyboard Control

```python
# Example keyboard control
from unitmcp.input_devices import Keyboard

# Create keyboard controller
keyboard = Keyboard()

# Type text
keyboard.type_text("Hello, UnitMCP!")

# Press and release key combinations
keyboard.press_keys(["ctrl", "c"])

# Register callback for key events
keyboard.on_key_press(lambda key: print(f"Key pressed: {key}"))
```

### 2. Mouse Control

```python
# Example mouse control
from unitmcp.input_devices import Mouse

# Create mouse controller
mouse = Mouse()

# Move mouse to absolute position
mouse.move_to(100, 100)

# Move mouse relative to current position
mouse.move_relative(50, 20)

# Perform clicks
mouse.click(button="left")
mouse.double_click()

# Perform drag and drop
mouse.drag_from_to(100, 100, 200, 200)
```

### 3. Combined Input Control

```python
# Example combined input control
from unitmcp.input_devices import InputController

# Create input controller
input_controller = InputController()

# Perform complex input sequence
input_controller.execute_sequence([
    {"type": "mouse_move", "x": 100, "y": 100},
    {"type": "mouse_click", "button": "left"},
    {"type": "keyboard_type", "text": "Hello, UnitMCP!"},
    {"type": "keyboard_press", "keys": ["enter"]}
])
```

## Running the Examples

To run these examples, you'll need:

- Python 3.7+
- UnitMCP library installed (`pip install -e .` from the project root)
- Input device dependencies: pynput, pyautogui

Install the required dependencies:
```bash
pip install pynput pyautogui
```

## Security Considerations

When using input device automation:

1. **Be careful with automated input**: Automated keyboard and mouse actions can have unintended consequences
2. **Use safeguards**: Implement emergency stop mechanisms (e.g., move mouse to corner)
3. **Test in safe environments**: Always test automation scripts in controlled environments
4. **User consent**: Ensure users are aware of automated input operations
5. **Avoid sensitive data**: Be cautious about automating input for sensitive operations

## Additional Resources

- [UnitMCP Input Devices API Documentation](../../docs/api/input_devices.md)
- [PyAutoGUI Documentation](https://pyautogui.readthedocs.io/)
- [Pynput Documentation](https://pynput.readthedocs.io/)
