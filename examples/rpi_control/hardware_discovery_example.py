#!/usr/bin/env python3
"""
Hardware Discovery Example for UnitMCP

This example demonstrates how to:
1. Connect to the UnitMCP server
2. Discover available hardware devices
3. Query device capabilities
4. List available peripherals (GPIO, I2C, SPI, etc.)
5. Detect connected sensors and actuators

This script helps users identify what hardware is available on their system.
"""

import asyncio
import argparse
import platform
import json
import logging
import os
import subprocess
from typing import Dict, List, Optional, Any, Tuple

from unitmcp import MCPHardwareClient

# Check if we're on a Raspberry Pi
IS_RPI = platform.machine() in ["armv7l", "aarch64"]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("hardware_discovery.log")
    ]
)
logger = logging.getLogger("UnitMCP-HardwareDiscovery")


class I2CScanner:
    """Class to scan for I2C devices."""
    
    # Common I2C device addresses and their descriptions
    KNOWN_DEVICES = {
        0x27: "PCF8574 I2C LCD Controller",
        0x3C: "SSD1306 OLED Display",
        0x48: "ADS1115/ADS1015 ADC",
        0x68: "MPU6050 Accelerometer/Gyroscope or DS3231 RTC",
        0x76: "BME280 Environmental Sensor",
        0x77: "BMP180/BMP280 Pressure Sensor",
        0x40: "HTU21D/SHT21 Humidity Sensor or INA219 Current Sensor",
        0x39: "TSL2561 Light Sensor",
        0x23: "BH1750 Light Sensor",
        0x57: "ATMEL AT24C32 EEPROM",
        0x50: "AT24C32/AT24C64 EEPROM",
        0x70: "HT16K33 LED Matrix Driver",
        0x20: "MCP23017 I/O Expander",
        0x5C: "AM2320 Temperature/Humidity Sensor"
    }
    
    @staticmethod
    async def scan_i2c_bus(bus_num: int = 1) -> List[Dict[str, Any]]:
        """Scan the I2C bus for devices.
        
        Args:
            bus_num: I2C bus number to scan
            
        Returns:
            List of dictionaries with device information
        """
        if not IS_RPI:
            logger.info("I2C scanning only available on Raspberry Pi")
            return []
            
        devices = []
        
        # Check if i2c-tools is installed
        i2cdetect_path = subprocess.run(["which", "i2cdetect"], 
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if i2cdetect_path.returncode != 0:
            logger.warning("i2cdetect not found, cannot scan I2C bus")
            return devices
            
        # Check if I2C bus exists
        if not os.path.exists(f"/dev/i2c-{bus_num}"):
            logger.warning(f"I2C bus {bus_num} not found")
            return devices
            
        try:
            # Run i2cdetect to scan for devices
            cmd = ["i2cdetect", "-y", str(bus_num)]
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if process.returncode != 0:
                logger.error(f"Error scanning I2C bus: {process.stderr.decode()}")
                return devices
                
            # Parse the output
            output = process.stdout.decode()
            lines = output.strip().split('\n')[1:]  # Skip header line
            
            for line in lines:
                parts = line.strip().split(':')
                if len(parts) != 2:
                    continue
                    
                row_base = int(parts[0], 16) * 16
                cells = parts[1].strip().split()
                
                for i, cell in enumerate(cells):
                    if cell != "--":
                        try:
                            address = row_base + i
                            device = {
                                "address": address,
                                "address_hex": f"0x{address:02X}",
                                "description": I2CScanner.KNOWN_DEVICES.get(address, "Unknown device")
                            }
                            devices.append(device)
                        except ValueError:
                            pass
                            
            return devices
        except Exception as e:
            logger.error(f"Error scanning I2C bus: {e}")
            return []


class GPIOScanner:
    """Class to scan for GPIO devices and pins."""
    
    @staticmethod
    async def get_gpio_info() -> Dict[str, Any]:
        """Get information about GPIO pins.
        
        Returns:
            Dictionary with GPIO information
        """
        if not IS_RPI:
            logger.info("GPIO scanning only available on Raspberry Pi")
            return {"available": False}
            
        try:
            # Try to import RPi.GPIO
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Get Raspberry Pi model information
            model = "Unknown"
            revision = "Unknown"
            
            if os.path.exists("/proc/device-tree/model"):
                with open("/proc/device-tree/model", "r") as f:
                    model = f.read().strip('\0')
                    
            if os.path.exists("/proc/cpuinfo"):
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.startswith("Revision"):
                            revision = line.split(":")[1].strip()
                            break
                            
            # Determine available GPIO pins based on model
            available_pins = []
            
            # Standard GPIO pins available on most Raspberry Pi models
            standard_pins = [2, 3, 4, 17, 27, 22, 10, 9, 11, 5, 6, 13, 19, 26, 14, 15, 18, 23, 24, 25, 8, 7, 12, 16, 20, 21]
            
            # Add pins to available list
            for pin in standard_pins:
                available_pins.append({
                    "pin": pin,
                    "mode": "Unknown",  # Would require checking current pin mode
                    "function": "GPIO"
                })
                
            return {
                "available": True,
                "model": model,
                "revision": revision,
                "pin_count": len(available_pins),
                "pins": available_pins
            }
        except ImportError:
            logger.warning("RPi.GPIO module not available")
            return {"available": False, "error": "RPi.GPIO module not available"}
        except Exception as e:
            logger.error(f"Error getting GPIO information: {e}")
            return {"available": False, "error": str(e)}


class AudioScanner:
    """Class to scan for audio devices."""
    
    @staticmethod
    async def get_audio_devices() -> Dict[str, Any]:
        """Get information about audio devices.
        
        Returns:
            Dictionary with audio device information
        """
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            
            devices = []
            info = {"available": True}
            
            # Get device count
            device_count = p.get_device_count()
            info["device_count"] = device_count
            
            # Get information for each device
            for i in range(device_count):
                try:
                    device_info = p.get_device_info_by_index(i)
                    
                    # Create a simplified device info dictionary
                    device = {
                        "index": device_info["index"],
                        "name": device_info["name"],
                        "max_input_channels": device_info["maxInputChannels"],
                        "max_output_channels": device_info["maxOutputChannels"],
                        "default_sample_rate": device_info["defaultSampleRate"],
                        "is_input_device": device_info["maxInputChannels"] > 0,
                        "is_output_device": device_info["maxOutputChannels"] > 0
                    }
                    
                    # Check if this is a default device
                    device["is_default_input"] = (device_info["index"] == p.get_default_input_device_info()["index"]) if p.get_default_input_device_info() else False
                    device["is_default_output"] = (device_info["index"] == p.get_default_output_device_info()["index"]) if p.get_default_output_device_info() else False
                    
                    devices.append(device)
                except Exception as e:
                    logger.warning(f"Error getting info for audio device {i}: {e}")
                    
            # Add devices to info
            info["devices"] = devices
            
            # Clean up
            p.terminate()
            
            return info
        except ImportError:
            logger.warning("PyAudio module not available")
            return {"available": False, "error": "PyAudio module not available"}
        except Exception as e:
            logger.error(f"Error getting audio device information: {e}")
            return {"available": False, "error": str(e)}


class SPIScanner:
    """Class to scan for SPI devices."""
    
    @staticmethod
    async def get_spi_info() -> Dict[str, Any]:
        """Get information about SPI interfaces.
        
        Returns:
            Dictionary with SPI information
        """
        if not IS_RPI:
            logger.info("SPI scanning only available on Raspberry Pi")
            return {"available": False}
            
        try:
            # Check if SPI is enabled
            spi_enabled = False
            
            # Check if SPI device nodes exist
            spi_devices = []
            for i in range(2):  # Check SPI0 and SPI1
                device_path = f"/dev/spidev0.{i}"
                if os.path.exists(device_path):
                    spi_enabled = True
                    spi_devices.append({"device": device_path, "bus": 0, "chip_select": i})
                    
            if not spi_enabled:
                # Check if SPI is enabled in config but devices not loaded
                if os.path.exists("/boot/config.txt"):
                    with open("/boot/config.txt", "r") as f:
                        config = f.read()
                        if "dtparam=spi=on" in config:
                            spi_enabled = True
                            
            return {
                "available": spi_enabled,
                "devices": spi_devices
            }
        except Exception as e:
            logger.error(f"Error getting SPI information: {e}")
            return {"available": False, "error": str(e)}


class UARTScanner:
    """Class to scan for UART devices."""
    
    @staticmethod
    async def get_uart_info() -> Dict[str, Any]:
        """Get information about UART interfaces.
        
        Returns:
            Dictionary with UART information
        """
        if not IS_RPI:
            logger.info("UART scanning only available on Raspberry Pi")
            return {"available": False}
            
        try:
            # Check for UART devices
            uart_devices = []
            
            # Check for primary UART
            if os.path.exists("/dev/serial0") or os.path.exists("/dev/ttyAMA0"):
                uart_devices.append({
                    "device": "/dev/serial0" if os.path.exists("/dev/serial0") else "/dev/ttyAMA0",
                    "description": "Primary UART"
                })
                
            # Check for secondary UART on Raspberry Pi 4
            if os.path.exists("/dev/serial1") or os.path.exists("/dev/ttyS0"):
                uart_devices.append({
                    "device": "/dev/serial1" if os.path.exists("/dev/serial1") else "/dev/ttyS0",
                    "description": "Secondary UART"
                })
                
            # Check if UART is enabled in config
            uart_enabled = len(uart_devices) > 0
            if not uart_enabled and os.path.exists("/boot/config.txt"):
                with open("/boot/config.txt", "r") as f:
                    config = f.read()
                    if "enable_uart=1" in config:
                        uart_enabled = True
                        
            return {
                "available": uart_enabled,
                "devices": uart_devices
            }
        except Exception as e:
            logger.error(f"Error getting UART information: {e}")
            return {"available": False, "error": str(e)}


class SystemInfoScanner:
    """Class to gather system information."""
    
    @staticmethod
    async def get_system_info() -> Dict[str, Any]:
        """Get general system information.
        
        Returns:
            Dictionary with system information
        """
        info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "is_raspberry_pi": IS_RPI
        }
        
        # Get more detailed information on Raspberry Pi
        if IS_RPI:
            try:
                # Get CPU temperature
                if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
                    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                        temp = int(f.read().strip()) / 1000.0
                        info["cpu_temperature"] = temp
                        
                # Get memory information
                mem_info = {}
                if os.path.exists("/proc/meminfo"):
                    with open("/proc/meminfo", "r") as f:
                        for line in f:
                            if ":" in line:
                                key, value = line.split(":", 1)
                                mem_info[key.strip()] = value.strip()
                                
                    if "MemTotal" in mem_info:
                        total_mem = mem_info["MemTotal"].split()[0]
                        info["total_memory"] = f"{int(total_mem) // 1024} MB"
                        
                    if "MemAvailable" in mem_info:
                        available_mem = mem_info["MemAvailable"].split()[0]
                        info["available_memory"] = f"{int(available_mem) // 1024} MB"
                        
                # Get disk space information
                disk_info = subprocess.run(["df", "-h", "/"], 
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if disk_info.returncode == 0:
                    lines = disk_info.stdout.decode().strip().split('\n')
                    if len(lines) >= 2:
                        parts = lines[1].split()
                        if len(parts) >= 5:
                            info["disk_size"] = parts[1]
                            info["disk_used"] = parts[2]
                            info["disk_available"] = parts[3]
                            info["disk_use_percent"] = parts[4]
            except Exception as e:
                logger.warning(f"Error getting detailed system info: {e}")
                
        return info


class HardwareDiscoveryExample:
    """Main hardware discovery example class."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        """Initialize the hardware discovery example.
        
        Args:
            host: The hostname or IP address of the MCP server
            port: The port of the MCP server
        """
        self.host = host
        self.port = port
        self.client: Optional[MCPHardwareClient] = None
        self.discovery_results = {}
        
    async def connect(self):
        """Connect to the MCP server."""
        logger.info(f"Connecting to MCP server at {self.host}:{self.port}...")
        self.client = MCPHardwareClient(self.host, self.port)
        await self.client.connect()
        logger.info("Connected to MCP server")
        
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected from MCP server")
            
    async def discover_hardware(self):
        """Discover available hardware devices."""
        logger.info("Starting hardware discovery...")
        
        # Get system information
        logger.info("Getting system information...")
        self.discovery_results["system"] = await SystemInfoScanner.get_system_info()
        
        # Get GPIO information
        logger.info("Scanning for GPIO...")
        self.discovery_results["gpio"] = await GPIOScanner.get_gpio_info()
        
        # Get I2C information
        logger.info("Scanning for I2C devices...")
        self.discovery_results["i2c"] = {
            "available": IS_RPI and os.path.exists("/dev/i2c-1"),
            "devices": await I2CScanner.scan_i2c_bus(1)
        }
        
        # Get SPI information
        logger.info("Scanning for SPI interfaces...")
        self.discovery_results["spi"] = await SPIScanner.get_spi_info()
        
        # Get UART information
        logger.info("Scanning for UART interfaces...")
        self.discovery_results["uart"] = await UARTScanner.get_uart_info()
        
        # Get audio device information
        logger.info("Scanning for audio devices...")
        self.discovery_results["audio"] = await AudioScanner.get_audio_devices()
        
        # Get MCP server capabilities
        if self.client:
            try:
                logger.info("Getting MCP server capabilities...")
                capabilities = await self.client.send_request("system.getCapabilities", {})
                self.discovery_results["mcp_capabilities"] = capabilities
            except Exception as e:
                logger.error(f"Error getting MCP server capabilities: {e}")
                self.discovery_results["mcp_capabilities"] = {"error": str(e)}
        else:
            self.discovery_results["mcp_capabilities"] = {"error": "Not connected to MCP server"}
            
        logger.info("Hardware discovery completed")
        
    def print_discovery_results(self):
        """Print the hardware discovery results."""
        if not self.discovery_results:
            logger.warning("No discovery results available")
            return
            
        print("\n=== UnitMCP Hardware Discovery Results ===\n")
        
        # Print system information
        if "system" in self.discovery_results:
            system = self.discovery_results["system"]
            print("System Information:")
            print(f"  Platform: {system.get('platform')} {system.get('platform_release')} {system.get('platform_version')}")
            print(f"  Architecture: {system.get('architecture')}")
            print(f"  Processor: {system.get('processor')}")
            print(f"  Raspberry Pi: {'Yes' if system.get('is_raspberry_pi') else 'No'}")
            
            if system.get('is_raspberry_pi'):
                print(f"  CPU Temperature: {system.get('cpu_temperature', 'N/A')}°C")
                print(f"  Total Memory: {system.get('total_memory', 'N/A')}")
                print(f"  Available Memory: {system.get('available_memory', 'N/A')}")
                print(f"  Disk Size: {system.get('disk_size', 'N/A')}")
                print(f"  Disk Used: {system.get('disk_used', 'N/A')} ({system.get('disk_use_percent', 'N/A')})")
            print()
            
        # Print GPIO information
        if "gpio" in self.discovery_results:
            gpio = self.discovery_results["gpio"]
            print("GPIO Information:")
            if gpio.get("available", False):
                print(f"  Available: Yes")
                print(f"  Model: {gpio.get('model', 'Unknown')}")
                print(f"  Pin Count: {gpio.get('pin_count', 0)}")
                
                # Print first few pins
                pins = gpio.get("pins", [])
                if pins:
                    print("  Available Pins (first 10):")
                    for pin in pins[:10]:
                        print(f"    GPIO{pin['pin']}: {pin['function']}")
                    if len(pins) > 10:
                        print(f"    ... and {len(pins) - 10} more")
            else:
                print(f"  Available: No")
                if "error" in gpio:
                    print(f"  Error: {gpio['error']}")
            print()
            
        # Print I2C information
        if "i2c" in self.discovery_results:
            i2c = self.discovery_results["i2c"]
            print("I2C Information:")
            if i2c.get("available", False):
                print(f"  Available: Yes")
                devices = i2c.get("devices", [])
                if devices:
                    print(f"  Detected Devices: {len(devices)}")
                    for device in devices:
                        print(f"    {device['address_hex']}: {device['description']}")
                else:
                    print("  No I2C devices detected")
            else:
                print(f"  Available: No")
            print()
            
        # Print SPI information
        if "spi" in self.discovery_results:
            spi = self.discovery_results["spi"]
            print("SPI Information:")
            if spi.get("available", False):
                print(f"  Available: Yes")
                devices = spi.get("devices", [])
                if devices:
                    print(f"  Detected Interfaces: {len(devices)}")
                    for device in devices:
                        print(f"    {device['device']} (Bus: {device['bus']}, CS: {device['chip_select']})")
                else:
                    print("  SPI enabled but no device nodes found")
            else:
                print(f"  Available: No")
            print()
            
        # Print UART information
        if "uart" in self.discovery_results:
            uart = self.discovery_results["uart"]
            print("UART Information:")
            if uart.get("available", False):
                print(f"  Available: Yes")
                devices = uart.get("devices", [])
                if devices:
                    print(f"  Detected Interfaces: {len(devices)}")
                    for device in devices:
                        print(f"    {device['device']}: {device['description']}")
                else:
                    print("  UART enabled but no device nodes found")
            else:
                print(f"  Available: No")
            print()
            
        # Print audio information
        if "audio" in self.discovery_results:
            audio = self.discovery_results["audio"]
            print("Audio Information:")
            if audio.get("available", False):
                print(f"  Available: Yes")
                print(f"  Device Count: {audio.get('device_count', 0)}")
                devices = audio.get("devices", [])
                if devices:
                    print("  Detected Devices:")
                    for device in devices:
                        default_str = ""
                        if device.get("is_default_input"):
                            default_str += " (Default Input)"
                        if device.get("is_default_output"):
                            default_str += " (Default Output)"
                            
                        channels_str = []
                        if device.get("max_input_channels", 0) > 0:
                            channels_str.append(f"{device['max_input_channels']} in")
                        if device.get("max_output_channels", 0) > 0:
                            channels_str.append(f"{device['max_output_channels']} out")
                            
                        print(f"    {device['index']}: {device['name']}{default_str}")
                        print(f"       Channels: {', '.join(channels_str)}")
            else:
                print(f"  Available: No")
                if "error" in audio:
                    print(f"  Error: {audio['error']}")
            print()
            
        # Print MCP server capabilities
        if "mcp_capabilities" in self.discovery_results:
            capabilities = self.discovery_results["mcp_capabilities"]
            print("MCP Server Capabilities:")
            if "error" in capabilities:
                print(f"  Error: {capabilities['error']}")
            else:
                for key, value in capabilities.items():
                    if isinstance(value, dict):
                        print(f"  {key}:")
                        for subkey, subvalue in value.items():
                            print(f"    {subkey}: {subvalue}")
                    else:
                        print(f"  {key}: {value}")
            print()
            
    def save_discovery_results(self, output_file: str):
        """Save the hardware discovery results to a file.
        
        Args:
            output_file: Path to the output file
        """
        if not self.discovery_results:
            logger.warning("No discovery results available to save")
            return
            
        try:
            with open(output_file, "w") as f:
                json.dump(self.discovery_results, f, indent=2)
                
            logger.info(f"Discovery results saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving discovery results: {e}")
            
    async def run_discovery(self, output_file: Optional[str] = None):
        """Run the complete hardware discovery process.
        
        Args:
            output_file: Path to save the discovery results (optional)
        """
        try:
            # Connect to MCP server
            await self.connect()
            
            # Discover hardware
            await self.discover_hardware()
            
            # Print results
            self.print_discovery_results()
            
            # Save results if requested
            if output_file:
                self.save_discovery_results(output_file)
                
        finally:
            # Disconnect from MCP server
            await self.disconnect()


async def main():
    """Main function to run the hardware discovery example."""
    parser = argparse.ArgumentParser(description="UnitMCP Hardware Discovery Example")
    parser.add_argument("--host", default="127.0.0.1", help="MCP server hostname or IP")
    parser.add_argument("--port", type=int, default=8888, help="MCP server port")
    parser.add_argument("--output", help="Path to save discovery results (optional)")
    args = parser.parse_args()
    
    example = HardwareDiscoveryExample(host=args.host, port=args.port)
    await example.run_discovery(args.output)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Hardware discovery interrupted by user")
    except Exception as e:
        logger.error(f"Error in hardware discovery: {e}", exc_info=True)
