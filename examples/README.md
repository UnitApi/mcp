# MCP Hardware Examples

This directory contains example scripts demonstrating various features of the MCP Hardware library.

## Quick Start

1. Start the MCP server:
```bash
python start_server.py
```

2. Run any example:
```bash
python led_control.py
```

## Examples Overview

### Basic Hardware Control

#### `led_control.py`
- Simple LED blinking
- Different blink patterns
- Basic GPIO control

#### `keyboard_demo.py`
- Text typing automation
- Keyboard shortcuts (Ctrl+C, Ctrl+V)
- Form filling simulation

#### `mouse_demo.py`
- Mouse movement control
- Click operations (left, right, double-click)
- Drag and drop
- Screenshot capture

### Audio Features

#### `audio_record.py`
- Audio recording
- Playback functionality
- Volume control
- Text-to-speech conversion

### Camera Operations

#### `camera_demo.py`
- Camera capture
- Face detection
- Motion detection
- Video streaming (coming soon)

### Automation & Pipelines

#### `simple_pipeline.py`
- Basic pipeline creation
- Variable substitution
- Error handling examples

#### `automation_pipeline.py`
- Complex automation workflows
- Conditional execution
- Retry mechanisms

### Complete Systems

#### `traffic_light.py`
- Traffic light simulation
- Pedestrian crossing system
- LED sequencing

#### `security_system.py`
- Motion detection alerts
- Camera surveillance
- Multi-sensor integration

### Integration Examples

#### `ollama_integration.py`
- Natural language control
- AI-powered automation
- Voice commands

#### `voice_assistant.py`
- Voice control system
- Speech recognition
- Voice feedback

### Interactive Tools

#### `shell_cli_demo.py`
- Interactive command shell
- Pipeline management
- Script execution

#### `integrated_demo.py`
- Combined shell and pipeline usage
- Complex automation scenarios

## Running Examples

Most examples have multiple demos. When you run them, you'll see a menu:

```bash
$ python led_control.py
LED Control Demo
1. Simple blink
2. LED patterns
Select demo (1-2): 
```

## Hardware Requirements

Different examples require different hardware:

- **GPIO Examples**: Raspberry Pi with LEDs, buttons, sensors
- **Audio Examples**: Microphone and speakers
- **Camera Examples**: USB webcam or Pi Camera
- **Input Examples**: Any computer with keyboard/mouse

## Common Issues

1. **Permission Errors**: Run with appropriate permissions for hardware access
2. **Missing Hardware**: Some examples will simulate if hardware is not present
3. **Server Connection**: Ensure the MCP server is running before examples

## Creating Your Own Examples

Use these examples as templates for your own automation:

1. Copy a similar example
2. Modify the hardware setup
3. Adjust the control logic
4. Add error handling as needed

For more information, see the main project documentation.


# MCP Hardware Access Library

A comprehensive library for secure hardware control through the Model Context Protocol (MCP), enabling AI agents and automated systems to interact with physical devices.

## Core Features

### 1. Hardware Control
- **GPIO Control**: LEDs, buttons, sensors (Raspberry Pi)
- **Input Devices**: Keyboard and mouse automation
- **Audio System**: Recording, playback, text-to-speech
- **Camera Control**: Video capture, face detection
- **USB Devices**: Device enumeration and management

### 2. AI Integration
- **Ollama LLM Support**: Natural language hardware control
- **Voice Assistant**: Voice-controlled automation
- **Pipeline System**: Complex automation workflows

### 3. Interactive Shell
- **Command-line Interface**: Direct hardware control
- **Pipeline Management**: Create and run automation sequences
- **Variable System**: Dynamic configuration

## Examples Overview

The `examples/` folder contains focused demonstrations of each feature:

### Basic Hardware Control

#### 1. LED Control (`examples/led_control.py`)
Simple LED blinking example:
```python
import asyncio
from unitmcp import MCPHardwareClient

async def blink_led():
    async with MCPHardwareClient() as client:
        # Setup LED
        await client.setup_led("led1", pin=17)
        
        # Blink 5 times
        for i in range(5):
            await client.control_led("led1", "on")
            await asyncio.sleep(0.5)
            await client.control_led("led1", "off")
            await asyncio.sleep(0.5)
```

#### 2. Keyboard Automation (`examples/keyboard_demo.py`)
Type text and use keyboard shortcuts:
```python
async def keyboard_demo():
    async with MCPHardwareClient() as client:
        # Type text
        await client.type_text("Hello, World!")
        
        # Use keyboard shortcut
        await client.hotkey("ctrl", "a")  # Select all
        await client.hotkey("ctrl", "c")  # Copy
```

#### 3. Mouse Control (`examples/mouse_demo.py`)
Control mouse movement and clicks:
```python
async def mouse_demo():
    async with MCPHardwareClient() as client:
        # Move mouse
        await client.move_mouse(500, 300)
        
        # Click operations
        await client.click("left")
        await client.double_click()
        
        # Take screenshot
        await client.screenshot()
```

### Audio and Voice

#### 4. Audio Recording (`examples/audio_record.py`)
Record and play audio:
```python
async def audio_demo():
    async with MCPHardwareClient() as client:
        # Record 5 seconds of audio
        await client.send_request("audio.startRecording", {})
        await asyncio.sleep(5)
        result = await client.send_request("audio.stopRecording", {})
        
        # Play back the recording
        await client.send_request("audio.playAudio", {
            "audio_data": result["audio_data"]
        })
```

#### 5. Voice Assistant (`examples/voice_control.py`)
Voice-controlled hardware:
```python
from unitmcp.examples.voice_assistant import VoiceHardwareAssistant

async def voice_control():
    assistant = VoiceHardwareAssistant()
    await assistant.connect()
    
    # Start listening for commands
    await assistant.run_assistant()
    # Say: "Assistant, turn on the red LED"
```

### Camera Operations

#### 6. Camera Capture (`examples/camera_demo.py`)
Capture images and detect faces:
```python
async def camera_demo():
    async with MCPHardwareClient() as client:
        # Open camera
        await client.send_request("camera.openCamera", {
            "camera_id": 0,
            "device_name": "webcam"
        })
        
        # Capture image
        result = await client.send_request("camera.captureImage", {
            "device_name": "webcam"
        })
        
        # Detect faces
        faces = await client.send_request("camera.detectFaces", {
            "device_name": "webcam"
        })
```

### Pipeline Automation

#### 7. Simple Pipeline (`examples/simple_pipeline.py`)
Create and run automation sequences:
```python
from unitmcp.pipeline import Pipeline, PipelineStep

async def pipeline_demo():
    steps = [
        PipelineStep(
            command="setup_led",
            method="gpio.setupLED",
            params={"device_id": "led1", "pin": 17}
        ),
        PipelineStep(
            command="blink",
            method="gpio.controlLED",
            params={"device_id": "led1", "action": "blink"}
        )
    ]
    
    pipeline = Pipeline("blink_pipeline", steps)
    
    async with MCPHardwareClient() as client:
        result = await pipeline.execute(client)
```

#### 8. Advanced Pipeline (`examples/automation_pipeline.py`)
Complex automation with error handling:
```python
async def advanced_pipeline():
    pipeline = Pipeline("advanced_automation", [
        PipelineStep(
            command="check_system",
            method="system.getStatus",
            expectations=[
                Expectation(ExpectationType.VALUE_EQUALS, "status", "ready")
            ],
            on_failure="error_handler"
        ),
        # ... more steps
    ])
```

### Interactive Shell

#### 9. Shell Commands (`examples/shell_commands.py`)
Interactive control examples:
```python
# Start shell
python -m unitmcp.client.shell

# Example commands:
# GPIO control
mcp> gpio_setup 17 OUT
mcp> led_setup led1 17
mcp> led led1 on

# Input control  
mcp> type "Hello from shell!"
mcp> move 500 300
mcp> click left

# Pipeline management
mcp> pipeline_create my_automation
mcp> pipeline_add my_automation type "Automated message"
mcp> pipeline_run my_automation
```

### AI Integration

#### 10. Ollama Control (`examples/ollama_demo.py`)
Natural language hardware control:
```python
from unitmcp.examples.ollama_integration import OllamaHardwareAgent

async def ollama_demo():
    agent = OllamaHardwareAgent()
    await agent.connect()
    
    # Natural language commands
    await agent.process_command("Turn on the LED on pin 17")
    await agent.process_command("Type 'Hello' using the keyboard")
```

### Complete Examples

#### 11. Traffic Light System (`examples/traffic_light.py`)
Simulated traffic light with LEDs:
```python
async def traffic_light():
    async with MCPHardwareClient() as client:
        # Setup LEDs
        await client.setup_led("red", pin=17)
        await client.setup_led("yellow", pin=27)
        await client.setup_led("green", pin=22)
        
        # Traffic light sequence
        while True:
            # Red
            await client.control_led("red", "on")
            await asyncio.sleep(5)
            
            # Yellow
            await client.control_led("red", "off")
            await client.control_led("yellow", "on")
            await asyncio.sleep(2)
            
            # Green
            await client.control_led("yellow", "off")
            await client.control_led("green", "on")
            await asyncio.sleep(5)
```

#### 12. Security System (`examples/security_system.py`)
Motion detection with alerts:
```python
async def security_system():
    pipeline = Pipeline("security_monitor", [
        PipelineStep(
            command="setup_motion",
            method="gpio.setupMotionSensor",
            params={"device_id": "motion1", "pin": 23}
        ),
        PipelineStep(
            command="monitor",
            method="gpio.readMotionSensor",
            params={"device_id": "motion1"},
            expectations=[
                Expectation(ExpectationType.VALUE_EQUALS, 
                          "motion_detected", True)
            ],
            on_success="alert",
            on_failure="monitor",  # Loop if no motion
            retry_count=1000,
            retry_delay=0.1
        ),
        PipelineStep(
            command="alert",
            method="gpio.controlBuzzer",
            params={"device_id": "buzzer1", "action": "beep"}
        )
    ])
```

## Running Examples

### Installation
```bash
# Clone repository
git clone https://github.com/example/mcp-hardware.git
cd mcp-hardware

# Install package
pip install -e .
```

### Start MCP Server
```bash
# Start server with all hardware support
python examples/start_server.py
```

### Run Individual Examples
```bash
# LED control
python examples/led_control.py

# Keyboard automation
python examples/keyboard_demo.py

# Voice assistant
python examples/voice_control.py

# Pipeline automation
python examples/simple_pipeline.py
```

### Interactive Shell
```bash
# Start shell interface
python -m unitmcp.client.shell

# Or use the demo
python examples/shell_commands.py --interactive
```

## Example Directory Structure

```
examples/
├── __init__.py
├── start_server.py          # Server startup script
├── led_control.py           # Basic LED control
├── keyboard_demo.py         # Keyboard automation
├── mouse_demo.py            # Mouse control
├── audio_record.py          # Audio recording/playback
├── voice_control.py         # Voice assistant demo
├── camera_demo.py           # Camera operations
├── simple_pipeline.py       # Basic pipeline example
├── automation_pipeline.py   # Advanced pipeline
├── shell_commands.py        # Shell interface demo
├── ollama_demo.py           # LLM integration
├── traffic_light.py         # Complete traffic light system
├── security_system.py       # Motion detection system
└── README.md                # Examples documentation
```

Each example is self-contained and demonstrates specific features of the MCP Hardware library, making it easy to learn and integrate into your own projects.