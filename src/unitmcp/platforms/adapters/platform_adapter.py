#!/usr/bin/env python3
"""
Platform Adapter Module for UnitMCP

This module implements the Adapter Pattern for hardware platforms in UnitMCP.
It provides a unified interface for different hardware platforms, allowing
the rest of the system to interact with them in a consistent way.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Set

logger = logging.getLogger(__name__)


class PlatformAdapter(ABC):
    """
    Abstract base class for platform adapters.
    
    This class defines the interface that all platform adapter implementations must follow.
    It implements the Adapter Pattern for hardware platforms.
    """
    
    def __init__(self, platform_id: str):
        """
        Initialize a platform adapter.
        
        Parameters
        ----------
        platform_id : str
            Unique identifier for the platform
        """
        self.platform_id = platform_id
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the platform.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """
        Clean up platform resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of the platform.
        
        Returns
        -------
        Dict[str, Any]
            Platform capabilities
        """
        pass
    
    @abstractmethod
    async def get_pin_modes(self) -> Dict[int, List[str]]:
        """
        Get the available modes for each pin on the platform.
        
        Returns
        -------
        Dict[int, List[str]]
            Dictionary mapping pin numbers to lists of available modes
        """
        pass
    
    @abstractmethod
    async def set_pin_mode(self, pin: int, mode: str) -> bool:
        """
        Set the mode of a pin.
        
        Parameters
        ----------
        pin : int
            Pin number
        mode : str
            Pin mode (e.g., "input", "output", "pwm", "analog")
            
        Returns
        -------
        bool
            True if the mode was set successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def digital_read(self, pin: int) -> Optional[bool]:
        """
        Read the digital value of a pin.
        
        Parameters
        ----------
        pin : int
            Pin number
            
        Returns
        -------
        Optional[bool]
            Pin value (True for HIGH, False for LOW), or None if the read failed
        """
        pass
    
    @abstractmethod
    async def digital_write(self, pin: int, value: bool) -> bool:
        """
        Write a digital value to a pin.
        
        Parameters
        ----------
        pin : int
            Pin number
        value : bool
            Pin value (True for HIGH, False for LOW)
            
        Returns
        -------
        bool
            True if the write was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def analog_read(self, pin: int) -> Optional[int]:
        """
        Read the analog value of a pin.
        
        Parameters
        ----------
        pin : int
            Pin number
            
        Returns
        -------
        Optional[int]
            Pin value (0-1023), or None if the read failed
        """
        pass
    
    @abstractmethod
    async def analog_write(self, pin: int, value: int) -> bool:
        """
        Write an analog value to a pin.
        
        Parameters
        ----------
        pin : int
            Pin number
        value : int
            Pin value (0-255 for PWM, 0-1023 for DAC)
            
        Returns
        -------
        bool
            True if the write was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def pwm_write(self, pin: int, duty_cycle: float) -> bool:
        """
        Write a PWM value to a pin.
        
        Parameters
        ----------
        pin : int
            Pin number
        duty_cycle : float
            Duty cycle (0.0-1.0)
            
        Returns
        -------
        bool
            True if the write was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_platform_info(self) -> Dict[str, Any]:
        """
        Get information about the platform.
        
        Returns
        -------
        Dict[str, Any]
            Platform information
        """
        pass


class RaspberryPiAdapter(PlatformAdapter):
    """
    Adapter for Raspberry Pi platforms.
    
    This class provides an implementation of the platform adapter interface for Raspberry Pi.
    """
    
    def __init__(self, platform_id: str = "raspberry_pi"):
        """
        Initialize a Raspberry Pi adapter.
        
        Parameters
        ----------
        platform_id : str, optional
            Unique identifier for the platform, by default "raspberry_pi"
        """
        super().__init__(platform_id)
        self.gpio_module = None
        self.pin_modes = {}
    
    async def initialize(self) -> bool:
        """
        Initialize the Raspberry Pi platform.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            # Import the RPi.GPIO module
            import RPi.GPIO as GPIO
            self.gpio_module = GPIO
            
            # Set the pin numbering mode to BCM
            self.gpio_module.setmode(self.gpio_module.BCM)
            
            # Set warnings to False
            self.gpio_module.setwarnings(False)
            
            # Initialize pin modes dictionary
            self.pin_modes = {}
            
            self.is_initialized = True
            logger.info(f"Initialized Raspberry Pi platform {self.platform_id}")
            return True
        except ImportError:
            logger.error("Failed to import RPi.GPIO module")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Raspberry Pi platform {self.platform_id}: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """
        Clean up Raspberry Pi platform resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        try:
            if self.gpio_module:
                # Clean up all GPIO pins
                self.gpio_module.cleanup()
                
                # Reset pin modes dictionary
                self.pin_modes = {}
                
                self.is_initialized = False
                logger.info(f"Cleaned up Raspberry Pi platform {self.platform_id}")
                return True
            else:
                logger.warning("GPIO module not initialized")
                return False
        except Exception as e:
            logger.error(f"Failed to clean up Raspberry Pi platform {self.platform_id}: {e}")
            return False
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of the Raspberry Pi platform.
        
        Returns
        -------
        Dict[str, Any]
            Platform capabilities
        """
        return {
            "digital_input": True,
            "digital_output": True,
            "pwm_output": True,
            "analog_input": False,
            "analog_output": False,
            "i2c": True,
            "spi": True,
            "uart": True
        }
    
    async def get_pin_modes(self) -> Dict[int, List[str]]:
        """
        Get the available modes for each pin on the Raspberry Pi platform.
        
        Returns
        -------
        Dict[int, List[str]]
            Dictionary mapping pin numbers to lists of available modes
        """
        # Define available modes for each pin
        # This is a simplified example, in reality you would need to check the specific Raspberry Pi model
        pin_modes = {}
        
        # GPIO pins (BCM numbering)
        gpio_pins = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
        
        # PWM pins (BCM numbering)
        pwm_pins = [12, 13, 18, 19]
        
        for pin in gpio_pins:
            modes = ["input", "output"]
            if pin in pwm_pins:
                modes.append("pwm")
            pin_modes[pin] = modes
        
        return pin_modes
    
    async def set_pin_mode(self, pin: int, mode: str) -> bool:
        """
        Set the mode of a pin on the Raspberry Pi platform.
        
        Parameters
        ----------
        pin : int
            Pin number (BCM numbering)
        mode : str
            Pin mode ("input", "output", "pwm")
            
        Returns
        -------
        bool
            True if the mode was set successfully, False otherwise
        """
        if not self.is_initialized:
            logger.error("Platform not initialized")
            return False
        
        try:
            if mode == "input":
                self.gpio_module.setup(pin, self.gpio_module.IN)
                self.pin_modes[pin] = "input"
                return True
            elif mode == "output":
                self.gpio_module.setup(pin, self.gpio_module.OUT)
                self.pin_modes[pin] = "output"
                return True
            elif mode == "pwm":
                # Check if the pin supports PWM
                pin_modes = await self.get_pin_modes()
                if pin in pin_modes and "pwm" in pin_modes[pin]:
                    self.gpio_module.setup(pin, self.gpio_module.OUT)
                    self.pin_modes[pin] = "pwm"
                    return True
                else:
                    logger.error(f"Pin {pin} does not support PWM")
                    return False
            else:
                logger.error(f"Unsupported pin mode: {mode}")
                return False
        except Exception as e:
            logger.error(f"Failed to set pin {pin} mode to {mode}: {e}")
            return False
    
    async def digital_read(self, pin: int) -> Optional[bool]:
        """
        Read the digital value of a pin on the Raspberry Pi platform.
        
        Parameters
        ----------
        pin : int
            Pin number (BCM numbering)
            
        Returns
        -------
        Optional[bool]
            Pin value (True for HIGH, False for LOW), or None if the read failed
        """
        if not self.is_initialized:
            logger.error("Platform not initialized")
            return None
        
        try:
            # Check if the pin is set up as an input
            if pin not in self.pin_modes or self.pin_modes[pin] != "input":
                await self.set_pin_mode(pin, "input")
            
            # Read the pin value
            value = self.gpio_module.input(pin)
            return bool(value)
        except Exception as e:
            logger.error(f"Failed to read digital value from pin {pin}: {e}")
            return None
    
    async def digital_write(self, pin: int, value: bool) -> bool:
        """
        Write a digital value to a pin on the Raspberry Pi platform.
        
        Parameters
        ----------
        pin : int
            Pin number (BCM numbering)
        value : bool
            Pin value (True for HIGH, False for LOW)
            
        Returns
        -------
        bool
            True if the write was successful, False otherwise
        """
        if not self.is_initialized:
            logger.error("Platform not initialized")
            return False
        
        try:
            # Check if the pin is set up as an output
            if pin not in self.pin_modes or self.pin_modes[pin] != "output":
                await self.set_pin_mode(pin, "output")
            
            # Write the pin value
            self.gpio_module.output(pin, value)
            return True
        except Exception as e:
            logger.error(f"Failed to write digital value {value} to pin {pin}: {e}")
            return False
    
    async def analog_read(self, pin: int) -> Optional[int]:
        """
        Read the analog value of a pin on the Raspberry Pi platform.
        
        Note: Raspberry Pi does not have analog inputs, so this method always returns None.
        
        Parameters
        ----------
        pin : int
            Pin number (BCM numbering)
            
        Returns
        -------
        Optional[int]
            Always None for Raspberry Pi
        """
        logger.warning("Raspberry Pi does not support analog input")
        return None
    
    async def analog_write(self, pin: int, value: int) -> bool:
        """
        Write an analog value to a pin on the Raspberry Pi platform.
        
        Note: Raspberry Pi does not have analog outputs, so this method always returns False.
        
        Parameters
        ----------
        pin : int
            Pin number (BCM numbering)
        value : int
            Pin value (0-255)
            
        Returns
        -------
        bool
            Always False for Raspberry Pi
        """
        logger.warning("Raspberry Pi does not support analog output")
        return False
    
    async def pwm_write(self, pin: int, duty_cycle: float) -> bool:
        """
        Write a PWM value to a pin on the Raspberry Pi platform.
        
        Parameters
        ----------
        pin : int
            Pin number (BCM numbering)
        duty_cycle : float
            Duty cycle (0.0-1.0)
            
        Returns
        -------
        bool
            True if the write was successful, False otherwise
        """
        if not self.is_initialized:
            logger.error("Platform not initialized")
            return False
        
        try:
            # Check if the pin is set up as a PWM output
            if pin not in self.pin_modes or self.pin_modes[pin] != "pwm":
                await self.set_pin_mode(pin, "pwm")
            
            # Convert duty cycle from 0.0-1.0 to 0-100
            duty_cycle_percent = int(duty_cycle * 100)
            
            # Create a PWM instance
            pwm = self.gpio_module.PWM(pin, 1000)  # 1000 Hz frequency
            
            # Start PWM with the specified duty cycle
            pwm.start(duty_cycle_percent)
            
            # Note: In a real implementation, you would want to keep track of PWM instances
            # and stop them when they are no longer needed
            
            return True
        except Exception as e:
            logger.error(f"Failed to write PWM value {duty_cycle} to pin {pin}: {e}")
            return False
    
    async def get_platform_info(self) -> Dict[str, Any]:
        """
        Get information about the Raspberry Pi platform.
        
        Returns
        -------
        Dict[str, Any]
            Platform information
        """
        try:
            # Try to get Raspberry Pi model information
            with open("/proc/device-tree/model", "r") as f:
                model = f.read().strip('\0')
            
            # Try to get CPU temperature
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read().strip()) / 1000.0
            
            # Try to get memory information
            with open("/proc/meminfo", "r") as f:
                mem_info = {}
                for line in f:
                    if "MemTotal" in line or "MemFree" in line or "MemAvailable" in line:
                        key, value = line.split(":")
                        mem_info[key.strip()] = int(value.strip().split()[0]) // 1024  # Convert to MB
            
            return {
                "platform": "Raspberry Pi",
                "model": model,
                "temperature": temp,
                "memory": mem_info
            }
        except Exception as e:
            logger.error(f"Failed to get platform information: {e}")
            return {
                "platform": "Raspberry Pi",
                "error": str(e)
            }


class ArduinoAdapter(PlatformAdapter):
    """
    Adapter for Arduino platforms.
    
    This class provides an implementation of the platform adapter interface for Arduino.
    """
    
    def __init__(self, platform_id: str = "arduino", port: str = "/dev/ttyUSB0", baud_rate: int = 9600):
        """
        Initialize an Arduino adapter.
        
        Parameters
        ----------
        platform_id : str, optional
            Unique identifier for the platform, by default "arduino"
        port : str, optional
            Serial port for the Arduino, by default "/dev/ttyUSB0"
        baud_rate : int, optional
            Baud rate for serial communication, by default 9600
        """
        super().__init__(platform_id)
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None
        self.pin_modes = {}
    
    async def initialize(self) -> bool:
        """
        Initialize the Arduino platform.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            # Import the serial module
            import serial
            import serial.tools.list_ports
            
            # Check if the specified port exists
            ports = list(serial.tools.list_ports.comports())
            port_exists = any(p.device == self.port for p in ports)
            
            if not port_exists:
                logger.error(f"Serial port {self.port} not found")
                return False
            
            # Open the serial connection
            self.serial = serial.Serial(self.port, self.baud_rate, timeout=1)
            
            # Wait for the Arduino to reset
            import asyncio
            await asyncio.sleep(2)
            
            # Initialize pin modes dictionary
            self.pin_modes = {}
            
            self.is_initialized = True
            logger.info(f"Initialized Arduino platform {self.platform_id} on port {self.port}")
            return True
        except ImportError:
            logger.error("Failed to import serial module")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Arduino platform {self.platform_id}: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """
        Clean up Arduino platform resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        try:
            if self.serial:
                # Close the serial connection
                self.serial.close()
                self.serial = None
                
                # Reset pin modes dictionary
                self.pin_modes = {}
                
                self.is_initialized = False
                logger.info(f"Cleaned up Arduino platform {self.platform_id}")
                return True
            else:
                logger.warning("Serial connection not initialized")
                return False
        except Exception as e:
            logger.error(f"Failed to clean up Arduino platform {self.platform_id}: {e}")
            return False
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of the Arduino platform.
        
        Returns
        -------
        Dict[str, Any]
            Platform capabilities
        """
        return {
            "digital_input": True,
            "digital_output": True,
            "pwm_output": True,
            "analog_input": True,
            "analog_output": True,
            "i2c": True,
            "spi": True,
            "uart": True
        }
    
    async def get_pin_modes(self) -> Dict[int, List[str]]:
        """
        Get the available modes for each pin on the Arduino platform.
        
        Returns
        -------
        Dict[int, List[str]]
            Dictionary mapping pin numbers to lists of available modes
        """
        # Define available modes for each pin
        # This is a simplified example for Arduino Uno, in reality you would need to check the specific Arduino model
        pin_modes = {}
        
        # Digital pins
        for pin in range(0, 14):
            modes = ["input", "output"]
            if pin in [3, 5, 6, 9, 10, 11]:
                modes.append("pwm")
            pin_modes[pin] = modes
        
        # Analog pins
        for pin in range(14, 20):
            pin_modes[pin] = ["input", "analog"]
        
        return pin_modes
    
    async def set_pin_mode(self, pin: int, mode: str) -> bool:
        """
        Set the mode of a pin on the Arduino platform.
        
        Parameters
        ----------
        pin : int
            Pin number
        mode : str
            Pin mode ("input", "output", "pwm", "analog")
            
        Returns
        -------
        bool
            True if the mode was set successfully, False otherwise
        """
        if not self.is_initialized:
            logger.error("Platform not initialized")
            return False
        
        try:
            # Send a command to the Arduino to set the pin mode
            command = f"M,{pin},{mode}\n"
            self.serial.write(command.encode())
            
            # Wait for a response
            import asyncio
            await asyncio.sleep(0.1)
            
            # Read the response
            response = self.serial.readline().decode().strip()
            
            if response == "OK":
                self.pin_modes[pin] = mode
                return True
            else:
                logger.error(f"Failed to set pin {pin} mode to {mode}: {response}")
                return False
        except Exception as e:
            logger.error(f"Failed to set pin {pin} mode to {mode}: {e}")
            return False
    
    async def digital_read(self, pin: int) -> Optional[bool]:
        """
        Read the digital value of a pin on the Arduino platform.
        
        Parameters
        ----------
        pin : int
            Pin number
            
        Returns
        -------
        Optional[bool]
            Pin value (True for HIGH, False for LOW), or None if the read failed
        """
        if not self.is_initialized:
            logger.error("Platform not initialized")
            return None
        
        try:
            # Check if the pin is set up as an input
            if pin not in self.pin_modes or self.pin_modes[pin] != "input":
                await self.set_pin_mode(pin, "input")
            
            # Send a command to the Arduino to read the pin
            command = f"DR,{pin}\n"
            self.serial.write(command.encode())
            
            # Wait for a response
            import asyncio
            await asyncio.sleep(0.1)
            
            # Read the response
            response = self.serial.readline().decode().strip()
            
            if response.startswith("DR,"):
                value = int(response.split(",")[1])
                return bool(value)
            else:
                logger.error(f"Failed to read digital value from pin {pin}: {response}")
                return None
        except Exception as e:
            logger.error(f"Failed to read digital value from pin {pin}: {e}")
            return None
    
    async def digital_write(self, pin: int, value: bool) -> bool:
        """
        Write a digital value to a pin on the Arduino platform.
        
        Parameters
        ----------
        pin : int
            Pin number
        value : bool
            Pin value (True for HIGH, False for LOW)
            
        Returns
        -------
        bool
            True if the write was successful, False otherwise
        """
        if not self.is_initialized:
            logger.error("Platform not initialized")
            return False
        
        try:
            # Check if the pin is set up as an output
            if pin not in self.pin_modes or self.pin_modes[pin] != "output":
                await self.set_pin_mode(pin, "output")
            
            # Send a command to the Arduino to write to the pin
            command = f"DW,{pin},{1 if value else 0}\n"
            self.serial.write(command.encode())
            
            # Wait for a response
            import asyncio
            await asyncio.sleep(0.1)
            
            # Read the response
            response = self.serial.readline().decode().strip()
            
            if response == "OK":
                return True
            else:
                logger.error(f"Failed to write digital value {value} to pin {pin}: {response}")
                return False
        except Exception as e:
            logger.error(f"Failed to write digital value {value} to pin {pin}: {e}")
            return False
    
    async def analog_read(self, pin: int) -> Optional[int]:
        """
        Read the analog value of a pin on the Arduino platform.
        
        Parameters
        ----------
        pin : int
            Pin number
            
        Returns
        -------
        Optional[int]
            Pin value (0-1023), or None if the read failed
        """
        if not self.is_initialized:
            logger.error("Platform not initialized")
            return None
        
        try:
            # Check if the pin is set up as an analog input
            if pin not in self.pin_modes or self.pin_modes[pin] != "analog":
                await self.set_pin_mode(pin, "analog")
            
            # Send a command to the Arduino to read the pin
            command = f"AR,{pin}\n"
            self.serial.write(command.encode())
            
            # Wait for a response
            import asyncio
            await asyncio.sleep(0.1)
            
            # Read the response
            response = self.serial.readline().decode().strip()
            
            if response.startswith("AR,"):
                value = int(response.split(",")[1])
                return value
            else:
                logger.error(f"Failed to read analog value from pin {pin}: {response}")
                return None
        except Exception as e:
            logger.error(f"Failed to read analog value from pin {pin}: {e}")
            return None
    
    async def analog_write(self, pin: int, value: int) -> bool:
        """
        Write an analog value to a pin on the Arduino platform.
        
        Parameters
        ----------
        pin : int
            Pin number
        value : int
            Pin value (0-255)
            
        Returns
        -------
        bool
            True if the write was successful, False otherwise
        """
        if not self.is_initialized:
            logger.error("Platform not initialized")
            return False
        
        try:
            # Check if the pin is set up as a PWM output
            if pin not in self.pin_modes or self.pin_modes[pin] != "pwm":
                await self.set_pin_mode(pin, "pwm")
            
            # Send a command to the Arduino to write to the pin
            command = f"AW,{pin},{value}\n"
            self.serial.write(command.encode())
            
            # Wait for a response
            import asyncio
            await asyncio.sleep(0.1)
            
            # Read the response
            response = self.serial.readline().decode().strip()
            
            if response == "OK":
                return True
            else:
                logger.error(f"Failed to write analog value {value} to pin {pin}: {response}")
                return False
        except Exception as e:
            logger.error(f"Failed to write analog value {value} to pin {pin}: {e}")
            return False
    
    async def pwm_write(self, pin: int, duty_cycle: float) -> bool:
        """
        Write a PWM value to a pin on the Arduino platform.
        
        Parameters
        ----------
        pin : int
            Pin number
        duty_cycle : float
            Duty cycle (0.0-1.0)
            
        Returns
        -------
        bool
            True if the write was successful, False otherwise
        """
        if not self.is_initialized:
            logger.error("Platform not initialized")
            return False
        
        try:
            # Convert duty cycle from 0.0-1.0 to 0-255
            value = int(duty_cycle * 255)
            
            # Use analog_write to set the PWM value
            return await self.analog_write(pin, value)
        except Exception as e:
            logger.error(f"Failed to write PWM value {duty_cycle} to pin {pin}: {e}")
            return False
    
    async def get_platform_info(self) -> Dict[str, Any]:
        """
        Get information about the Arduino platform.
        
        Returns
        -------
        Dict[str, Any]
            Platform information
        """
        if not self.is_initialized:
            logger.error("Platform not initialized")
            return {"platform": "Arduino", "error": "Not initialized"}
        
        try:
            # Send a command to the Arduino to get platform information
            command = "INFO\n"
            self.serial.write(command.encode())
            
            # Wait for a response
            import asyncio
            await asyncio.sleep(0.1)
            
            # Read the response
            response = self.serial.readline().decode().strip()
            
            if response.startswith("INFO,"):
                parts = response.split(",")
                return {
                    "platform": "Arduino",
                    "model": parts[1] if len(parts) > 1 else "Unknown",
                    "version": parts[2] if len(parts) > 2 else "Unknown"
                }
            else:
                logger.error(f"Failed to get platform information: {response}")
                return {"platform": "Arduino", "error": response}
        except Exception as e:
            logger.error(f"Failed to get platform information: {e}")
            return {"platform": "Arduino", "error": str(e)}


# Factory function to create the appropriate platform adapter
def create_platform_adapter(platform_type: str, **kwargs) -> Optional[PlatformAdapter]:
    """
    Create a platform adapter of the specified type.
    
    Parameters
    ----------
    platform_type : str
        Type of platform adapter to create (raspberry_pi, arduino)
    **kwargs
        Platform adapter parameters
    
    Returns
    -------
    Optional[PlatformAdapter]
        An instance of the appropriate platform adapter class, or None if creation failed
    
    Raises
    ------
    ValueError
        If the platform type is not supported
    """
    if platform_type.lower() == "raspberry_pi":
        return RaspberryPiAdapter(**kwargs)
    elif platform_type.lower() == "arduino":
        return ArduinoAdapter(**kwargs)
    else:
        raise ValueError(f"Unsupported platform type: {platform_type}")


# Helper function to get a platform adapter
def get_platform_adapter(platform_type: str = None, **kwargs) -> Optional[PlatformAdapter]:
    """
    Get a platform adapter of the specified type.
    
    If no platform type is specified, the function will try to detect the platform.
    
    Parameters
    ----------
    platform_type : str, optional
        Type of platform adapter to get (raspberry_pi, arduino)
    **kwargs
        Platform adapter parameters
    
    Returns
    -------
    Optional[PlatformAdapter]
        An instance of the appropriate platform adapter class, or None if creation failed
    """
    # If no platform type is specified, try to detect the platform
    if platform_type is None:
        # Try to detect if we're running on a Raspberry Pi
        try:
            import platform
            if "armv" in platform.machine():
                logger.info("Detected Raspberry Pi platform")
                return create_platform_adapter("raspberry_pi", **kwargs)
        except Exception as e:
            logger.warning(f"Error detecting platform: {e}")
    
    # If platform type is specified or detection failed, use the specified type
    try:
        return create_platform_adapter(platform_type, **kwargs)
    except Exception as e:
        logger.error(f"Error creating platform adapter: {e}")
        return None
