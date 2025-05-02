#!/usr/bin/env python3
"""
Enhanced Hardware Control Server

This script runs a server that listens for hardware control commands
and executes them on the local machine. It's designed to run on a Raspberry Pi
or similar device with GPIO, I2C, SPI, and audio capabilities.

Supported components:
- GPIO pins
- I2C devices
- LCD displays (I2C)
- Speakers (audio playback)
- LED matrices
"""

import argparse
import asyncio
import json
import logging
import os
import platform
import socket
import subprocess
import sys
import time
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global variables
clients = {}  # Store connected clients
hardware_state = {
    "gpio": {},
    "i2c": {},
    "lcd": {},
    "speaker": {"last_played": None},
    "led_matrix": {},
    "status": "ready",
    "last_command": None,
    "last_command_time": None,
    "simulation_mode": False  # Flag to indicate if we're in simulation mode
}

# Check if running on a Raspberry Pi
def is_raspberry_pi() -> bool:
    """Check if the script is running on a Raspberry Pi."""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            return 'raspberry pi' in model.lower()
    except:
        return False
    
# Try to import GPIO library if on Raspberry Pi
GPIO = None
if is_raspberry_pi():
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        logger.info("[HARDWARE] GPIO library initialized successfully")
    except ImportError:
        logger.warning("[HARDWARE] RPi.GPIO library not available")

# Try to import I2C library if available
I2C = None
try:
    import smbus
    I2C = smbus.SMBus(1)  # Use bus 1
    logger.info("[HARDWARE] I2C library initialized successfully")
except ImportError:
    logger.warning("[HARDWARE] smbus library not available")
except Exception as e:
    logger.warning(f"[HARDWARE] I2C error: {e}")

# Try to import audio libraries
AUDIO_AVAILABLE = False
try:
    import pygame
    pygame.mixer.init()
    AUDIO_AVAILABLE = True
    logger.info("[HARDWARE] Audio library (pygame) initialized successfully")
except ImportError:
    try:
        from pydub import AudioSegment
        from pydub.playback import play
        AUDIO_AVAILABLE = True
        logger.info("[HARDWARE] Audio library (pydub) initialized successfully")
    except ImportError:
        logger.warning("[HARDWARE] Audio libraries not available")
except Exception as e:
    logger.warning(f"[HARDWARE] Audio initialization error: {e}")

# Try to import LCD libraries
LCD_AVAILABLE = False
LCD_DEVICE = None
try:
    # For I2C LCD displays (most common)
    from RPLCD.i2c import CharLCD
    LCD_AVAILABLE = True
    # Default to common I2C address for 16x2 LCD
    try:
        LCD_DEVICE = CharLCD('PCF8574', 0x27, cols=16, rows=2)
        logger.info("[HARDWARE] LCD library initialized successfully")
    except Exception as e:
        logger.warning(f"[HARDWARE] LCD device not available: {e}")
        LCD_AVAILABLE = False
except ImportError:
    logger.warning("[HARDWARE] LCD library not available")

# Try to import LED matrix libraries
LED_MATRIX_AVAILABLE = False
try:
    # For Adafruit LED matrix displays
    from luma.led_matrix.device import max7219
    from luma.core.interface.serial import spi, noop
    from luma.core.render import canvas
    LED_MATRIX_AVAILABLE = True
    logger.info("[HARDWARE] LED matrix library initialized successfully")
except ImportError:
    logger.warning("[HARDWARE] LED matrix library not available")

def log_system_info():
    """Log system information for debugging purposes."""
    logger.info("=== SERVER SYSTEM INFORMATION ===")
    logger.info(f"Hostname: {socket.gethostname()}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Get IP addresses
    logger.info("IP addresses:")
    try:
        hostname = socket.gethostname()
        ip_addresses = socket.getaddrinfo(hostname, None)
        for addrinfo in ip_addresses:
            if addrinfo[0] == socket.AF_INET:  # Only IPv4
                logger.info(f"  - {addrinfo[4][0]}")
    except Exception as e:
        logger.error(f"Error getting IP addresses: {e}")
    
    # Check for hardware components
    logger.info("Hardware components:")
    logger.info(f"  - GPIO available: {'Yes' if GPIO else 'No'}")
    logger.info(f"  - I2C available: {'Yes' if I2C else 'No'}")
    logger.info(f"  - Audio available: {'Yes' if AUDIO_AVAILABLE else 'No'}")
    logger.info(f"  - LCD available: {'Yes' if LCD_AVAILABLE else 'No'}")
    logger.info(f"  - LED matrix available: {'Yes' if LED_MATRIX_AVAILABLE else 'No'}")
    logger.info(f"  - Simulation mode: {'Yes' if hardware_state['simulation_mode'] else 'No'}")
    
    # Check for audio devices
    if AUDIO_AVAILABLE:
        try:
            audio_devices = subprocess.check_output(['aplay', '-l']).decode('utf-8')
            logger.info("Audio devices:")
            for line in audio_devices.split('\n'):
                if line.strip():
                    logger.info(f"  {line.strip()}")
        except:
            logger.info("  Could not enumerate audio devices")
    
    logger.info("=== END SYSTEM INFORMATION ===")

async def handle_gpio_command(pin: int, state: str) -> Dict[str, Any]:
    """Handle GPIO commands."""
    if not GPIO and not hardware_state["simulation_mode"]:
        return {"status": "error", "message": "GPIO not available"}
    
    try:
        # Convert pin to int and state to boolean
        pin = int(pin)
        if state.lower() in ['on', 'high', '1', 'true']:
            value = GPIO.HIGH if GPIO else 1
            state_str = "HIGH"
        else:
            value = GPIO.LOW if GPIO else 0
            state_str = "LOW"
        
        if GPIO:
            # Set up the pin as output if not already
            if pin not in hardware_state["gpio"]:
                GPIO.setup(pin, GPIO.OUT)
                hardware_state["gpio"][pin] = "output"
            
            # Set the pin state
            GPIO.output(pin, value)
        
        # Update state even in simulation mode
        hardware_state["gpio"][pin] = state_str
        
        logger.info(f"[HARDWARE] {'Simulated ' if not GPIO else ''}Set GPIO pin {pin} to {state_str}")
        
        return {"status": "success", "message": f"GPIO pin {pin} set to {state_str}"}
    except Exception as e:
        logger.error(f"[HARDWARE] GPIO error: {e}")
        return {"status": "error", "message": f"GPIO error: {e}"}

async def handle_i2c_command(address: int, register: int, value: Optional[int] = None) -> Dict[str, Any]:
    """Handle I2C commands."""
    if not I2C and not hardware_state["simulation_mode"]:
        return {"status": "error", "message": "I2C not available"}
    
    try:
        # Convert to integers
        address = int(address, 16) if isinstance(address, str) else int(address)
        register = int(register, 16) if isinstance(register, str) else int(register)
        
        if value is not None:
            # Write to I2C
            value = int(value, 16) if isinstance(value, str) else int(value)
            
            if I2C:
                I2C.write_byte_data(address, register, value)
            
            # Update state even in simulation mode
            if "writes" not in hardware_state["i2c"]:
                hardware_state["i2c"]["writes"] = []
            hardware_state["i2c"]["writes"].append({
                "address": f"0x{address:02X}",
                "register": f"0x{register:02X}",
                "value": f"0x{value:02X}",
                "time": datetime.now().isoformat()
            })
            
            logger.info(f"[HARDWARE] {'Simulated ' if not I2C else ''}Write to I2C device 0x{address:02X}, register 0x{register:02X}, value 0x{value:02X}")
            return {"status": "success", "message": f"Wrote 0x{value:02X} to I2C device 0x{address:02X}, register 0x{register:02X}"}
        else:
            # Read from I2C
            if I2C:
                value = I2C.read_byte_data(address, register)
            else:
                # In simulation mode, return a random value
                value = (address + register) % 256
            
            # Update state
            if "reads" not in hardware_state["i2c"]:
                hardware_state["i2c"]["reads"] = []
            hardware_state["i2c"]["reads"].append({
                "address": f"0x{address:02X}",
                "register": f"0x{register:02X}",
                "value": f"0x{value:02X}",
                "time": datetime.now().isoformat()
            })
            
            logger.info(f"[HARDWARE] {'Simulated ' if not I2C else ''}Read from I2C device 0x{address:02X}, register 0x{register:02X}, value 0x{value:02X}")
            return {"status": "success", "message": f"Read 0x{value:02X} from I2C device 0x{address:02X}, register 0x{register:02X}", "value": value}
    except Exception as e:
        logger.error(f"[HARDWARE] I2C error: {e}")
        return {"status": "error", "message": f"I2C error: {e}"}

async def handle_lcd_command(text: str, line: int = 0, clear: bool = False) -> Dict[str, Any]:
    """Handle LCD display commands."""
    if not LCD_AVAILABLE and not hardware_state["simulation_mode"]:
        return {"status": "error", "message": "LCD not available"}
    
    try:
        if clear:
            if LCD_DEVICE:
                LCD_DEVICE.clear()
            
            logger.info("[HARDWARE] {'Simulated ' if not LCD_DEVICE else ''}LCD display cleared")
            hardware_state["lcd"] = {"cleared": datetime.now().isoformat()}
            return {"status": "success", "message": "LCD display cleared"}
        
        # Ensure line is valid (0 or 1 for a 2-line display)
        line = max(0, min(int(line), 1))  # Default to 2 rows even in simulation
        
        # Truncate text to fit display width
        text = str(text)[:16]  # Default to 16 columns even in simulation
        
        if LCD_DEVICE:
            # Position cursor at beginning of the specified line
            LCD_DEVICE.cursor_pos = (line, 0)
            
            # Write the text
            LCD_DEVICE.write_string(text)
            
            # Pad with spaces to clear any previous text
            padding = ' ' * (16 - len(text))
            LCD_DEVICE.write_string(padding)
        
        logger.info(f"[HARDWARE] {'Simulated ' if not LCD_DEVICE else ''}Displayed text on LCD line {line}: '{text}'")
        
        # Update state
        hardware_state["lcd"][f"line_{line}"] = text
        hardware_state["lcd"]["last_updated"] = datetime.now().isoformat()
        
        return {"status": "success", "message": f"Text displayed on LCD line {line}"}
    except Exception as e:
        logger.error(f"[HARDWARE] LCD error: {e}")
        return {"status": "error", "message": f"LCD error: {e}"}

async def handle_speaker_command(action: str, file_data: Optional[str] = None, text: Optional[str] = None) -> Dict[str, Any]:
    """Handle speaker commands."""
    if not AUDIO_AVAILABLE and not hardware_state["simulation_mode"]:
        return {"status": "error", "message": "Audio not available"}
    
    try:
        if action == "play_file":
            if not file_data:
                return {"status": "error", "message": "No audio file data provided"}
            
            if AUDIO_AVAILABLE:
                # Save base64 data to temporary file
                import base64
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                temp_file.write(base64.b64decode(file_data))
                temp_file.close()
                
                # Play the audio file
                if 'pygame' in sys.modules:
                    pygame.mixer.music.load(temp_file.name)
                    pygame.mixer.music.play()
                    # Wait for playback to finish
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
                else:
                    # Using pydub
                    sound = AudioSegment.from_file(temp_file.name)
                    play(sound)
                
                # Clean up
                os.unlink(temp_file.name)
            
            logger.info(f"[HARDWARE] {'Simulated ' if not AUDIO_AVAILABLE else ''}Played audio file")
            hardware_state["speaker"]["last_played"] = datetime.now().isoformat()
            hardware_state["speaker"]["last_action"] = "play_file"
            return {"status": "success", "message": "Audio file played successfully"}
            
        elif action == "play_tone":
            frequency = 1000  # Default frequency in Hz
            duration = 1      # Default duration in seconds
            
            if AUDIO_AVAILABLE:
                # Generate a simple tone
                if 'pygame' in sys.modules:
                    pygame.mixer.Sound(pygame.sndarray.make_sound(
                        pygame.sndarray.array([4096 * pygame.math.sin(2.0 * 3.14159 * frequency * t / 44100)
                                             for t in range(0, 44100 * duration)]).astype(int)
                    )).play()
                    await asyncio.sleep(duration)
                else:
                    # Using pydub to generate a tone
                    from pydub.generators import Sine
                    tone = Sine(frequency).to_audio_segment(duration=duration*1000)
                    play(tone)
            
            logger.info(f"[HARDWARE] {'Simulated ' if not AUDIO_AVAILABLE else ''}Played tone at {frequency}Hz for {duration}s")
            hardware_state["speaker"]["last_played"] = datetime.now().isoformat()
            hardware_state["speaker"]["last_action"] = "play_tone"
            hardware_state["speaker"]["frequency"] = frequency
            hardware_state["speaker"]["duration"] = duration
            return {"status": "success", "message": f"Tone played at {frequency}Hz for {duration}s"}
            
        elif action == "speak":
            if not text:
                return {"status": "error", "message": "No text provided for speech"}
            
            if AUDIO_AVAILABLE:
                # Try to use system text-to-speech
                try:
                    # Try espeak first (common on Raspberry Pi)
                    subprocess.run(['espeak', text], check=True)
                except:
                    try:
                        # Try festival as fallback
                        process = subprocess.Popen(['festival', '--tts'], stdin=subprocess.PIPE)
                        process.communicate(text.encode())
                    except:
                        pass
            
            logger.info(f"[HARDWARE] {'Simulated ' if not AUDIO_AVAILABLE else ''}Spoke text: '{text}'")
            hardware_state["speaker"]["last_played"] = datetime.now().isoformat()
            hardware_state["speaker"]["last_action"] = "speak"
            hardware_state["speaker"]["last_text"] = text
            return {"status": "success", "message": "Text spoken successfully"}
        else:
            return {"status": "error", "message": f"Unknown speaker action: {action}"}
    except Exception as e:
        logger.error(f"[HARDWARE] Speaker error: {e}")
        return {"status": "error", "message": f"Speaker error: {e}"}

async def handle_led_matrix_command(action: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle LED matrix commands."""
    if not LED_MATRIX_AVAILABLE and not hardware_state["simulation_mode"]:
        return {"status": "error", "message": "LED matrix not available"}
    
    try:
        # Initialize the LED matrix device if not already done and not in simulation mode
        if LED_MATRIX_AVAILABLE and "device" not in hardware_state["led_matrix"]:
            serial = spi(port=0, device=0, gpio=noop())
            device = max7219(serial, cascaded=1, block_orientation=-90)
            device.contrast(16)  # Medium brightness
            hardware_state["led_matrix"]["device"] = device
        
        device = hardware_state["led_matrix"].get("device", None)
        
        if action == "clear":
            if device:
                with canvas(device) as draw:
                    pass  # Empty canvas clears the display
            
            # Clear the state
            hardware_state["led_matrix"] = {"cleared": datetime.now().isoformat()}
            if device:
                hardware_state["led_matrix"]["device"] = device
                
            logger.info(f"[HARDWARE] {'Simulated ' if not device else ''}LED matrix cleared")
            return {"status": "success", "message": "LED matrix cleared"}
            
        elif action == "text":
            if not data or "text" not in data:
                return {"status": "error", "message": "No text provided for LED matrix"}
            
            text = data["text"]
            x = data.get("x", 0)
            y = data.get("y", 0)
            
            if device:
                with canvas(device) as draw:
                    draw.text((x, y), text, fill="white")
            
            # Update state
            hardware_state["led_matrix"]["text"] = text
            hardware_state["led_matrix"]["x"] = x
            hardware_state["led_matrix"]["y"] = y
            hardware_state["led_matrix"]["last_updated"] = datetime.now().isoformat()
            
            logger.info(f"[HARDWARE] {'Simulated ' if not device else ''}Displayed text on LED matrix: '{text}'")
            return {"status": "success", "message": "Text displayed on LED matrix"}
            
        elif action == "pixel":
            if not data or "x" not in data or "y" not in data:
                return {"status": "error", "message": "Coordinates not provided for LED matrix pixel"}
            
            x = int(data["x"])
            y = int(data["y"])
            state = data.get("state", True)
            
            if device:
                with canvas(device) as draw:
                    if state:
                        draw.point((x, y), fill="white")
            
            # Update state
            if "pixels" not in hardware_state["led_matrix"]:
                hardware_state["led_matrix"]["pixels"] = []
            hardware_state["led_matrix"]["pixels"].append({"x": x, "y": y, "state": state})
            hardware_state["led_matrix"]["last_updated"] = datetime.now().isoformat()
            
            logger.info(f"[HARDWARE] {'Simulated ' if not device else ''}Set LED matrix pixel at ({x}, {y}) to {state}")
            return {"status": "success", "message": f"LED matrix pixel at ({x}, {y}) set to {state}"}
            
        else:
            return {"status": "error", "message": f"Unknown LED matrix action: {action}"}
    except Exception as e:
        logger.error(f"[HARDWARE] LED matrix error: {e}")
        return {"status": "error", "message": f"LED matrix error: {e}"}

async def handle_status_command() -> Dict[str, Any]:
    """Handle status command."""
    status_info = {
        "status": "success",
        "message": "System status",
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "time": datetime.now().isoformat(),
        },
        "hardware": {
            "gpio_available": GPIO is not None,
            "i2c_available": I2C is not None,
            "audio_available": AUDIO_AVAILABLE,
            "lcd_available": LCD_AVAILABLE,
            "led_matrix_available": LED_MATRIX_AVAILABLE,
            "simulation_mode": hardware_state["simulation_mode"],
            "gpio_pins": hardware_state["gpio"],
            "lcd_state": hardware_state["lcd"],
            "speaker_state": hardware_state["speaker"],
            "led_matrix_state": {k: v for k, v in hardware_state["led_matrix"].items() if k != "device"},
            "last_command": hardware_state["last_command"],
            "last_command_time": hardware_state["last_command_time"],
        }
    }
    
    # Add Raspberry Pi specific information if available
    if is_raspberry_pi():
        try:
            # Get CPU temperature
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read()) / 1000.0
                status_info["system"]["cpu_temperature"] = f"{temp:.1f}°C"
        except:
            pass
        
        try:
            # Get memory information
            mem_info = subprocess.check_output(['free', '-h']).decode('utf-8')
            status_info["system"]["memory_info"] = mem_info.split('\n')[1].split()[1:4]
        except:
            pass
    
    logger.info(f"[HARDWARE] Status command executed")
    return status_info

async def process_command(command_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a command from a client."""
    action = command_data.get("action", "")
    
    # Update last command information
    hardware_state["last_command"] = action
    hardware_state["last_command_time"] = datetime.now().isoformat()
    
    # Process based on action
    if action == "status":
        return await handle_status_command()
    
    elif action == "gpio":
        pin = command_data.get("pin")
        state = command_data.get("state")
        if pin is None or state is None:
            return {"status": "error", "message": "Missing pin or state for GPIO command"}
        return await handle_gpio_command(pin, state)
    
    elif action == "i2c":
        address = command_data.get("address")
        register = command_data.get("register")
        value = command_data.get("value")
        if address is None or register is None:
            return {"status": "error", "message": "Missing address or register for I2C command"}
        return await handle_i2c_command(address, register, value)
    
    elif action == "lcd":
        text = command_data.get("text", "")
        line = command_data.get("line", 0)
        clear = command_data.get("clear", False)
        return await handle_lcd_command(text, line, clear)
    
    elif action == "speaker":
        sub_action = command_data.get("sub_action")
        if not sub_action:
            return {"status": "error", "message": "Missing sub_action for speaker command"}
        
        if sub_action == "play_file":
            file_data = command_data.get("file_data")
            return await handle_speaker_command("play_file", file_data=file_data)
        
        elif sub_action == "play_tone":
            return await handle_speaker_command("play_tone")
        
        elif sub_action == "speak":
            text = command_data.get("text")
            return await handle_speaker_command("speak", text=text)
        
        else:
            return {"status": "error", "message": f"Unknown speaker sub_action: {sub_action}"}
    
    elif action == "led_matrix":
        sub_action = command_data.get("sub_action")
        data = command_data.get("data", {})
        if not sub_action:
            return {"status": "error", "message": "Missing sub_action for LED matrix command"}
        return await handle_led_matrix_command(sub_action, data)
    
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}

async def handle_client(reader, writer):
    """Handle client connection."""
    addr = writer.get_extra_info('peername')
    client_id = f"{addr[0]}:{addr[1]}"
    clients[client_id] = {"connected_at": datetime.now().isoformat()}
    
    logger.info(f"[CONNECTION] New client connected from {client_id}")
    
    while True:
        try:
            # Read data from client
            data = await reader.read(4096)
            if not data:
                logger.info(f"[CONNECTION] Client {client_id} disconnected (no data)")
                break
            
            # Parse the command
            try:
                command_data = json.loads(data.decode())
                logger.info(f"[COMMAND] Received from {client_id}: {command_data}")
                
                # Add client information to command data
                command_data["client_id"] = client_id
                command_data["timestamp"] = datetime.now().isoformat()
                
                # Process the command
                response = await process_command(command_data)
                
                # Send response back to client
                writer.write(json.dumps(response).encode())
                await writer.drain()
                logger.info(f"[RESPONSE] Sent to {client_id}: {response}")
                
            except json.JSONDecodeError:
                logger.error(f"[ERROR] Invalid JSON from {client_id}: {data.decode()}")
                writer.write(json.dumps({"status": "error", "message": "Invalid JSON"}).encode())
                await writer.drain()
                
        except Exception as e:
            logger.error(f"[ERROR] Error handling client {client_id}: {e}")
            break
    
    # Clean up when client disconnects
    if client_id in clients:
        del clients[client_id]
    writer.close()
    logger.info(f"[CONNECTION] Client {client_id} disconnected")

async def verify_server_is_listening(host, port):
    """Verify that the server is listening on the specified port."""
    try:
        # Create a connection to the server
        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        
        # Send a simple status command
        command = json.dumps({"action": "status"}).encode()
        writer.write(command)
        await writer.drain()
        
        # Read the response
        data = await reader.read(4096)
        response = json.loads(data.decode())
        
        # Close the connection
        writer.close()
        await writer.wait_closed()
        
        logger.info(f"[SERVER] Successfully verified server is listening on port {port}")
        return True
    except Exception as e:
        logger.error(f"[SERVER] Failed to verify server is listening on port {port}: {e}")
        return False

async def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Hardware Control Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8082, help='Port to listen on')
    parser.add_argument('--verify', action='store_true', help='Verify server is listening and exit')
    parser.add_argument('--simulate', action='store_true', help='Run in simulation mode (for testing without hardware)')
    args = parser.parse_args()
    
    # Set simulation mode if requested
    if args.simulate:
        hardware_state["simulation_mode"] = True
        logger.info("[CONFIG] Running in simulation mode (hardware operations will be simulated)")
    
    # Log startup information
    logger.info(f"[STARTUP] Hardware Control Server starting at {datetime.now().isoformat()}")
    logger.info(f"[CONFIG] Host: {args.host}, Port: {args.port}")
    
    # Log system information
    log_system_info()
    
    if args.verify:
        # Just verify the server is listening and exit
        result = await verify_server_is_listening(args.host, args.port)
        sys.exit(0 if result else 1)
    
    # Start the server
    server = await asyncio.start_server(handle_client, args.host, args.port)
    
    addr = server.sockets[0].getsockname()
    logger.info(f'[SERVER] Listening on {addr[0]}:{addr[1]}')
    
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[SERVER] Server stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"[SERVER] Server error: {e}")
    finally:
        # Clean up GPIO if used
        if GPIO:
            GPIO.cleanup()
        logger.info("[SERVER] Server shutdown complete")
