#!/usr/bin/env python3
"""
Display Device Module for UnitMCP

This module provides classes for controlling display devices in UnitMCP.
It includes implementations for various display types including LCD, OLED, and simulation.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple, Union

from .base import OutputDevice, DeviceType, DeviceState, DeviceMode, DeviceCommandError
from ..utils.env_loader import EnvLoader

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
env = EnvLoader()


class DisplayType(Enum):
    """Enumeration of display types."""
    LCD = "lcd"
    OLED = "oled"
    LED_MATRIX = "led_matrix"
    SEGMENT = "segment"
    VIRTUAL = "virtual"
    UNKNOWN = "unknown"


class DisplayDevice(OutputDevice):
    """
    Display device implementation.
    
    This class provides functionality for controlling display devices.
    It supports various display types and both hardware and simulation modes.
    """
    
    def __init__(
        self,
        device_id: str,
        display_type: Union[DisplayType, str] = None,
        width: int = None,
        height: int = None,
        address: int = None,
        mode: Union[DeviceMode, str] = None,
        **kwargs
    ):
        """
        Initialize a display device.
        
        Args:
            device_id: Unique identifier for the device
            display_type: Type of display (LCD, OLED, LED_MATRIX, SEGMENT, VIRTUAL)
            width: Display width in characters or pixels
            height: Display height in characters or pixels
            address: I2C address for the display (if applicable)
            mode: Operation mode (hardware, simulation, remote, mock)
            **kwargs: Additional device parameters
        """
        super().__init__(device_id, DeviceType.DISPLAY, mode, **kwargs)
        
        # Convert display type to enum if needed
        if isinstance(display_type, str):
            try:
                self.display_type = DisplayType(display_type.lower())
            except ValueError:
                logger.warning(f"Unknown display type: {display_type}, defaulting to LCD")
                self.display_type = DisplayType.LCD
        else:
            self.display_type = display_type or DisplayType.LCD
        
        # Display dimensions
        self.width = width or env.get_int('DISPLAY_WIDTH', kwargs.get('default_width', 16))
        self.height = height or env.get_int('DISPLAY_HEIGHT', kwargs.get('default_height', 2))
        
        # I2C address (if applicable)
        self.address = address or env.get_int('DISPLAY_ADDRESS', kwargs.get('default_address', 0x27))
        
        # Display content
        self.content = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        self.cursor_x = 0
        self.cursor_y = 0
        self.backlight_on = True
        
        # Display-specific attributes
        self._display = None  # Will be set during initialization if in hardware mode
        
        # Additional parameters
        self.i2c_port = kwargs.get('i2c_port', 1)
        self.spi_port = kwargs.get('spi_port', 0)
        self.rotation = kwargs.get('rotation', 0)
        self.font_size = kwargs.get('font_size', 1)
        
        logger.debug(f"Created display device '{device_id}' of type {self.display_type.value} "
                    f"with dimensions {self.width}x{self.height} (mode: {self.mode.value})")
    
    async def initialize(self) -> bool:
        """
        Initialize the display device.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        self.state = DeviceState.INITIALIZING
        
        try:
            if self.mode == DeviceMode.HARDWARE:
                # Initialize hardware display
                await self._initialize_hardware()
            elif self.mode == DeviceMode.SIMULATION:
                # No hardware initialization needed for simulation
                logger.info(f"Initialized display device '{self.device_id}' in simulation mode")
            elif self.mode == DeviceMode.REMOTE:
                # Initialize remote connection
                await self._initialize_remote()
            elif self.mode == DeviceMode.MOCK:
                # No initialization needed for mock mode
                logger.info(f"Initialized display device '{self.device_id}' in mock mode")
            
            # Clear the display
            await self.clear()
            
            self.state = DeviceState.READY
            return True
            
        except Exception as e:
            self.state = DeviceState.ERROR
            self.last_error = str(e)
            logger.error(f"Error initializing display device '{self.device_id}': {e}")
            return False
    
    async def _initialize_hardware(self) -> None:
        """
        Initialize the hardware display.
        
        Raises:
            DeviceInitError: If hardware initialization fails
        """
        try:
            if self.display_type == DisplayType.LCD:
                await self._initialize_lcd()
            elif self.display_type == DisplayType.OLED:
                await self._initialize_oled()
            elif self.display_type == DisplayType.LED_MATRIX:
                await self._initialize_led_matrix()
            elif self.display_type == DisplayType.SEGMENT:
                await self._initialize_segment()
            else:
                logger.warning(f"Unsupported display type: {self.display_type.value}, falling back to simulation mode")
                self.mode = DeviceMode.SIMULATION
                
        except Exception as e:
            logger.error(f"Error initializing display hardware: {e}")
            raise
    
    async def _initialize_lcd(self) -> None:
        """Initialize an LCD display."""
        try:
            # Import RPLCD library
            try:
                from RPLCD.i2c import CharLCD
                
                # Initialize LCD
                self._display = CharLCD(
                    i2c_expander='PCF8574',
                    address=self.address,
                    port=self.i2c_port,
                    cols=self.width,
                    rows=self.height,
                    dotsize=8
                )
                
                logger.info(f"Initialized LCD display '{self.device_id}' at address 0x{self.address:02x}")
                
            except ImportError:
                logger.warning("RPLCD library not found, falling back to simulation mode")
                self.mode = DeviceMode.SIMULATION
                
        except Exception as e:
            logger.error(f"Error initializing LCD display: {e}")
            raise
    
    async def _initialize_oled(self) -> None:
        """Initialize an OLED display."""
        try:
            # Import Adafruit libraries
            try:
                import board
                import busio
                import adafruit_ssd1306
                
                # Initialize I2C
                i2c = busio.I2C(board.SCL, board.SDA)
                
                # Initialize OLED
                self._display = adafruit_ssd1306.SSD1306_I2C(
                    self.width,
                    self.height,
                    i2c,
                    addr=self.address
                )
                
                logger.info(f"Initialized OLED display '{self.device_id}' at address 0x{self.address:02x}")
                
            except ImportError:
                logger.warning("Adafruit libraries not found, falling back to simulation mode")
                self.mode = DeviceMode.SIMULATION
                
        except Exception as e:
            logger.error(f"Error initializing OLED display: {e}")
            raise
    
    async def _initialize_led_matrix(self) -> None:
        """Initialize an LED matrix display."""
        try:
            # Import max7219 library
            try:
                from luma.led_matrix.device import max7219
                from luma.core.interface.serial import spi, noop
                
                # Initialize SPI
                serial = spi(port=self.spi_port, device=0, gpio=noop())
                
                # Initialize LED matrix
                self._display = max7219(
                    serial,
                    cascaded=1,
                    block_orientation=0,
                    rotate=self.rotation,
                    blocks_arranged_in_reverse_order=False
                )
                
                logger.info(f"Initialized LED matrix display '{self.device_id}'")
                
            except ImportError:
                logger.warning("luma.led_matrix library not found, falling back to simulation mode")
                self.mode = DeviceMode.SIMULATION
                
        except Exception as e:
            logger.error(f"Error initializing LED matrix display: {e}")
            raise
    
    async def _initialize_segment(self) -> None:
        """Initialize a 7-segment display."""
        try:
            # Import max7219 library
            try:
                from luma.led_matrix.device import max7219
                from luma.core.interface.serial import spi, noop
                
                # Initialize SPI
                serial = spi(port=self.spi_port, device=0, gpio=noop())
                
                # Initialize 7-segment display
                self._display = max7219(
                    serial,
                    cascaded=1,
                    block_orientation=0,
                    rotate=0
                )
                
                logger.info(f"Initialized 7-segment display '{self.device_id}'")
                
            except ImportError:
                logger.warning("luma.led_matrix library not found, falling back to simulation mode")
                self.mode = DeviceMode.SIMULATION
                
        except Exception as e:
            logger.error(f"Error initializing 7-segment display: {e}")
            raise
    
    async def _initialize_remote(self) -> None:
        """
        Initialize the remote connection for the display.
        
        Raises:
            DeviceInitError: If remote initialization fails
        """
        # Implementation for remote mode would go here
        # This could involve setting up a connection to a remote server
        # that controls the actual hardware
        raise NotImplementedError("Remote mode not implemented yet")
    
    async def cleanup(self) -> bool:
        """
        Clean up display device resources.
        
        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            # Clear the display
            await self.clear()
            
            if self.mode == DeviceMode.HARDWARE and self._display:
                # Close the display
                if hasattr(self._display, 'close'):
                    self._display.close()
                elif hasattr(self._display, 'cleanup'):
                    self._display.cleanup()
            
            self.state = DeviceState.UNINITIALIZED
            logger.info(f"Cleaned up display device '{self.device_id}'")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error cleaning up display device '{self.device_id}': {e}")
            return False
    
    async def clear(self) -> bool:
        """
        Clear the display.
        
        Returns:
            True if clearing was successful, False otherwise
        """
        try:
            if self.mode == DeviceMode.HARDWARE and self._display:
                if self.display_type == DisplayType.LCD:
                    self._display.clear()
                elif self.display_type == DisplayType.OLED:
                    self._display.fill(0)
                    self._display.show()
                elif self.display_type in [DisplayType.LED_MATRIX, DisplayType.SEGMENT]:
                    self._display.clear()
            
            # Clear content in memory
            self.content = [[' ' for _ in range(self.width)] for _ in range(self.height)]
            self.cursor_x = 0
            self.cursor_y = 0
            
            # Trigger event
            await self.trigger_event("cleared")
            
            logger.debug(f"Cleared display '{self.device_id}'")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error clearing display device '{self.device_id}': {e}")
            return False
    
    async def set_cursor(self, x: int, y: int) -> bool:
        """
        Set the cursor position.
        
        Args:
            x: Column position
            y: Row position
            
        Returns:
            True if setting cursor was successful, False otherwise
        """
        try:
            # Validate position
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                logger.warning(f"Invalid cursor position: ({x}, {y})")
                return False
            
            if self.mode == DeviceMode.HARDWARE and self._display:
                if self.display_type == DisplayType.LCD:
                    self._display.cursor_pos = (y, x)
            
            # Update cursor position in memory
            self.cursor_x = x
            self.cursor_y = y
            
            logger.debug(f"Set cursor position to ({x}, {y}) on display '{self.device_id}'")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error setting cursor position on display device '{self.device_id}': {e}")
            return False
    
    async def write_text(self, text: str, x: int = None, y: int = None) -> bool:
        """
        Write text to the display.
        
        Args:
            text: Text to write
            x: Column position (or current cursor position if None)
            y: Row position (or current cursor position if None)
            
        Returns:
            True if writing was successful, False otherwise
        """
        try:
            # Set cursor position if provided
            if x is not None and y is not None:
                await self.set_cursor(x, y)
            
            if self.mode == DeviceMode.HARDWARE and self._display:
                if self.display_type == DisplayType.LCD:
                    self._display.write_string(text)
                elif self.display_type == DisplayType.OLED:
                    # For OLED, we would need to use a drawing library
                    # This is a simplified implementation
                    from PIL import Image, ImageDraw, ImageFont
                    
                    # Create blank image for drawing
                    image = Image.new("1", (self.width, self.height))
                    draw = ImageDraw.Draw(image)
                    
                    # Load default font
                    font = ImageFont.load_default()
                    
                    # Draw text
                    draw.text((self.cursor_x, self.cursor_y), text, font=font, fill=255)
                    
                    # Display image
                    self._display.image(image)
                    self._display.show()
                    
                elif self.display_type in [DisplayType.LED_MATRIX, DisplayType.SEGMENT]:
                    # For LED matrix, we would need to use a drawing library
                    # This is a simplified implementation
                    from luma.core.render import canvas
                    
                    with canvas(self._display) as draw:
                        draw.text((self.cursor_x, self.cursor_y), text, fill="white")
            
            # Update content in memory
            for i, char in enumerate(text):
                if self.cursor_x + i < self.width:
                    self.content[self.cursor_y][self.cursor_x + i] = char
            
            # Update cursor position
            self.cursor_x += len(text)
            if self.cursor_x >= self.width:
                self.cursor_x = 0
                self.cursor_y += 1
                if self.cursor_y >= self.height:
                    self.cursor_y = 0
            
            # Trigger event
            await self.trigger_event("text_written", text=text, x=x, y=y)
            
            logger.debug(f"Wrote text '{text}' to display '{self.device_id}'")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error writing text to display device '{self.device_id}': {e}")
            return False
    
    async def write_line(self, text: str, line: int) -> bool:
        """
        Write text to a specific line on the display.
        
        Args:
            text: Text to write
            line: Line number (0-based)
            
        Returns:
            True if writing was successful, False otherwise
        """
        try:
            # Validate line number
            if line < 0 or line >= self.height:
                logger.warning(f"Invalid line number: {line}")
                return False
            
            # Clear the line first
            await self.clear_line(line)
            
            # Write text to the line
            return await self.write_text(text, 0, line)
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error writing line to display device '{self.device_id}': {e}")
            return False
    
    async def clear_line(self, line: int) -> bool:
        """
        Clear a specific line on the display.
        
        Args:
            line: Line number (0-based)
            
        Returns:
            True if clearing was successful, False otherwise
        """
        try:
            # Validate line number
            if line < 0 or line >= self.height:
                logger.warning(f"Invalid line number: {line}")
                return False
            
            if self.mode == DeviceMode.HARDWARE and self._display:
                if self.display_type == DisplayType.LCD:
                    self._display.cursor_pos = (line, 0)
                    self._display.write_string(' ' * self.width)
            
            # Clear line in memory
            self.content[line] = [' ' for _ in range(self.width)]
            
            logger.debug(f"Cleared line {line} on display '{self.device_id}'")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error clearing line on display device '{self.device_id}': {e}")
            return False
    
    async def set_backlight(self, on: bool) -> bool:
        """
        Set the backlight state.
        
        Args:
            on: True to turn on the backlight, False to turn it off
            
        Returns:
            True if setting backlight was successful, False otherwise
        """
        try:
            if self.mode == DeviceMode.HARDWARE and self._display:
                if self.display_type == DisplayType.LCD and hasattr(self._display, 'backlight_enabled'):
                    self._display.backlight_enabled = on
            
            # Update backlight state in memory
            self.backlight_on = on
            
            # Trigger event
            await self.trigger_event("backlight_changed", on=on)
            
            logger.debug(f"Set backlight {'on' if on else 'off'} on display '{self.device_id}'")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error setting backlight on display device '{self.device_id}': {e}")
            return False
    
    async def create_char(self, location: int, pattern: List[int]) -> bool:
        """
        Create a custom character (for LCD displays).
        
        Args:
            location: Character location (0-7)
            pattern: Character pattern (list of 8 integers)
            
        Returns:
            True if creating character was successful, False otherwise
        """
        try:
            # Validate location
            if location < 0 or location > 7:
                logger.warning(f"Invalid character location: {location}")
                return False
            
            # Validate pattern
            if len(pattern) != 8:
                logger.warning(f"Invalid pattern length: {len(pattern)}")
                return False
            
            if self.mode == DeviceMode.HARDWARE and self._display:
                if self.display_type == DisplayType.LCD and hasattr(self._display, 'create_char'):
                    self._display.create_char(location, pattern)
            
            logger.debug(f"Created custom character at location {location} on display '{self.device_id}'")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error creating custom character on display device '{self.device_id}': {e}")
            return False
    
    async def simulate_display(self) -> str:
        """
        Get a string representation of the display content.
        
        Returns:
            String representation of the display content
        """
        # Create a border around the display content
        border_top = '+' + '-' * self.width + '+'
        border_bottom = '+' + '-' * self.width + '+'
        
        # Create the display content
        content = [border_top]
        for row in self.content:
            content.append('|' + ''.join(row) + '|')
        content.append(border_bottom)
        
        return '\n'.join(content)
    
    async def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a command on the display device.
        
        Args:
            command: Command to execute (clear, set_cursor, write_text, write_line, clear_line, set_backlight)
            params: Command parameters
            
        Returns:
            Command result
            
        Raises:
            DeviceCommandError: If the command fails
        """
        params = params or {}
        
        if not self.state == DeviceState.READY and command != "status":
            return {"success": False, "error": f"Device not ready (state: {self.state.value})"}
        
        try:
            if command == "clear":
                success = await self.clear()
                return {"success": success}
            
            elif command == "set_cursor":
                x = params.get("x")
                y = params.get("y")
                
                if x is None or y is None:
                    return {"success": False, "error": "Missing required parameters: x, y"}
                
                success = await self.set_cursor(x, y)
                return {"success": success, "cursor": {"x": self.cursor_x, "y": self.cursor_y}}
            
            elif command == "write_text":
                text = params.get("text")
                x = params.get("x")
                y = params.get("y")
                
                if text is None:
                    return {"success": False, "error": "Missing required parameter: text"}
                
                success = await self.write_text(text, x, y)
                return {"success": success, "cursor": {"x": self.cursor_x, "y": self.cursor_y}}
            
            elif command == "write_line":
                text = params.get("text")
                line = params.get("line")
                
                if text is None or line is None:
                    return {"success": False, "error": "Missing required parameters: text, line"}
                
                success = await self.write_line(text, line)
                return {"success": success, "cursor": {"x": self.cursor_x, "y": self.cursor_y}}
            
            elif command == "clear_line":
                line = params.get("line")
                
                if line is None:
                    return {"success": False, "error": "Missing required parameter: line"}
                
                success = await self.clear_line(line)
                return {"success": success}
            
            elif command == "set_backlight":
                on = params.get("on")
                
                if on is None:
                    return {"success": False, "error": "Missing required parameter: on"}
                
                success = await self.set_backlight(on)
                return {"success": success, "backlight_on": self.backlight_on}
            
            elif command == "create_char":
                location = params.get("location")
                pattern = params.get("pattern")
                
                if location is None or pattern is None:
                    return {"success": False, "error": "Missing required parameters: location, pattern"}
                
                success = await self.create_char(location, pattern)
                return {"success": success}
            
            elif command == "simulate":
                display_content = await self.simulate_display()
                return {"success": True, "display": display_content}
            
            elif command == "status":
                return {
                    "success": True,
                    "display_type": self.display_type.value,
                    "dimensions": {"width": self.width, "height": self.height},
                    "cursor": {"x": self.cursor_x, "y": self.cursor_y},
                    "backlight_on": self.backlight_on,
                    "content": [''.join(row) for row in self.content]
                }
            
            else:
                return {"success": False, "error": f"Unknown command: {command}"}
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error executing command '{command}' on display device '{self.device_id}': {e}")
            return {"success": False, "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the display device.
        
        Returns:
            Dictionary containing device status information
        """
        status = await super().get_status()
        status.update({
            "display_type": self.display_type.value,
            "dimensions": {"width": self.width, "height": self.height},
            "address": f"0x{self.address:02x}" if self.address else None,
            "cursor": {"x": self.cursor_x, "y": self.cursor_y},
            "backlight_on": self.backlight_on,
            "content": [''.join(row) for row in self.content]
        })
        return status
