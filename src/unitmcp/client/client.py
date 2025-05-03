"""
client.py
"""

"""MCP Hardware client implementation."""

import asyncio
import json
import time
from typing import Dict, Any, Optional

from ..protocols.hardware_protocol import MCPRequest, MCPResponse
from ..utils.logger import get_logger


class MCPHardwareClient:
    """Client for MCP hardware server."""

    def __init__(
        self, host: str = "127.0.0.1", port: int = 8888, client_id: str = None
    ):
        self.host = host
        self.port = port
        self.client_id = client_id or f"client_{int(time.time())}"
        self.logger = get_logger("MCPHardwareClient")
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False

    async def connect(self):
        """Connect to MCP server."""
        try:
            self.logger.info(f"Attempting to connect to {self.host}:{self.port}...")
            
            # Try to resolve the hostname first
            import socket
            try:
                addr_info = socket.getaddrinfo(self.host, self.port, family=socket.AF_INET)
                resolved_ip = addr_info[0][4][0]
                self.logger.info(f"Resolved {self.host} to IP: {resolved_ip}")
            except socket.gaierror as e:
                self.logger.error(f"Failed to resolve hostname {self.host}: {e}")
                # Continue anyway as asyncio might handle it differently
            
            # Try to check if the port is open using a quick socket connection
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)  # 2 second timeout
                result = sock.connect_ex((self.host, self.port))
                sock.close()
                
                if result != 0:
                    self.logger.warning(f"Port check indicates {self.host}:{self.port} may not be open (error code: {result})")
                else:
                    self.logger.info(f"Port check successful: {self.host}:{self.port} appears to be open")
            except Exception as e:
                self.logger.warning(f"Port check failed: {e}")
            
            # Now try the actual asyncio connection
            self.logger.info(f"Establishing asyncio connection to {self.host}:{self.port}...")
            self._reader, self._writer = await asyncio.open_connection(
                self.host, self.port
            )
            self._connected = True
            self.logger.info(f"Successfully connected to MCP server at {self.host}:{self.port}")
        except ConnectionRefusedError as e:
            self.logger.error(f"Connection refused: {e} - The server at {self.host}:{self.port} actively refused the connection")
            self.logger.error("This typically means the server is not running or is not listening on this port")
            raise
        except asyncio.TimeoutError as e:
            self.logger.error(f"Connection timeout: {e} - Could not connect to {self.host}:{self.port} in time")
            self.logger.error("This typically means the server is unreachable or blocked by a firewall")
            raise
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            # Print more details about the exception
            import traceback
            self.logger.error(f"Exception details: {traceback.format_exc()}")
            raise

    def connect_sync(self):
        """
        Synchronous version of connect method.
        
        This method can be called from non-async code to connect to the server.
        """
        try:
            # Use asyncio.run to run the connect coroutine in a new event loop
            asyncio.run(self.connect())
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect (sync): {e}")
            raise
    
    async def connect_with_retry(self, max_retries=3, retry_delay=2.0):
        """
        Attempt to connect to the server with retry logic.
        
        Args:
            max_retries (int): Maximum number of connection attempts
            retry_delay (float): Delay between retries in seconds
            
        Returns:
            bool: True if connection was successful, False otherwise
            
        Raises:
            ConnectionError: If all connection attempts fail
        """
        self.logger.info(f"Attempting to connect to {self.host}:{self.port} with {max_retries} retries...")
        
        for attempt in range(1, max_retries + 1):
            self.logger.info(f"Connection attempt {attempt}/{max_retries}...")
            try:
                await self.connect()
                self.logger.info(f"Successfully connected to {self.host}:{self.port} on attempt {attempt}")
                return True
            except Exception as e:
                error_code = getattr(e, 'errno', None)
                self.logger.warning(f"Connection attempt {attempt} refused: {e}")
                
                if attempt < max_retries:
                    wait_time = retry_delay * (1.0 if attempt == 1 else 0.5 * attempt)
                    self.logger.info(f"Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
        
        self.logger.error(f"All {max_retries} connection attempts failed")
        raise ConnectionError(f"Could not establish a stable connection.")

    async def discover_server_port(self, port_ranges=None, timeout=0.2):
        """
        Discover the port that the server is listening on.
        
        Args:
            port_ranges (list): List of port ranges to check, each range is a tuple (start, end)
            timeout (float): Timeout for each port check in seconds
            
        Returns:
            int: The discovered port number, or None if no port is found
        """
        import socket
        import concurrent.futures
        import time
        
        if port_ranges is None:
            # Default port ranges to check, focusing on common MCP ports first
            port_ranges = [
                (8000, 8100),    # Common web server ports
                (9500, 9600),    # Common MCP ports
                (5000, 5100)     # Common Flask/API ports
            ]
        
        self.logger.info(f"Scanning {self.host} for open ports...")
        open_ports = []
        
        # Function to check a single port
        def check_port(port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((self.host, port))
            sock.close()
            if result == 0:
                return port
            return None
        
        # Check each port range
        for start_port, end_port in port_ranges:
            self.logger.info(f"Scanning port range {start_port}-{end_port}...")
            
            # Use ThreadPoolExecutor for parallel port scanning
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(check_port, port) for port in range(start_port, end_port + 1)]
                
                for future in concurrent.futures.as_completed(futures):
                    port = future.result()
                    if port is not None:
                        self.logger.info(f"Found open port: {port}")
                        open_ports.append(port)
        
        if not open_ports:
            self.logger.warning(f"No open ports found on {self.host}")
            return None
        
        # Try to connect to each open port to verify it's an MCP server
        for port in open_ports:
            self.logger.info(f"Attempting to connect to discovered port {port}...")
            
            # Save the original port
            original_port = self.port
            
            try:
                # Set the port to the discovered port
                self.port = port
                
                # Try to connect
                await self.connect()
                
                # If we get here, the connection was successful
                self.logger.info(f"Successfully connected to MCP server on port {port}")
                return port
                
            except Exception as e:
                self.logger.warning(f"Port {port} is open but not an MCP server: {e}")
                
                # Reset the connection state
                self._writer = None
                self._reader = None
                
            finally:
                # Restore the original port if the connection failed
                if self._writer is None and self._reader is None:
                    self.port = original_port
        
        # If we get here, none of the open ports were MCP servers
        self.logger.warning(f"No MCP servers found on any open ports on {self.host}")
        return None

    async def connect_with_discovery(self, max_retries=3, retry_delay=2.0):
        """
        Attempt to connect to the server, with automatic port discovery if the initial connection fails.
        
        Args:
            max_retries (int): Maximum number of connection attempts per port
            retry_delay (float): Delay between retries in seconds
            
        Returns:
            bool: True if connection was successful, False otherwise
            
        Raises:
            ConnectionError: If all connection attempts fail
        """
        # Try connecting to the specified port first
        try:
            self.logger.info(f"Attempting to connect to specified port {self.port} first...")
            await self.connect_with_retry(max_retries, retry_delay)
            return True
        except ConnectionError as e:
            self.logger.warning(f"Failed to connect to specified port {self.port}: {e}")
            
            # If that fails, try to discover the correct port
            self.logger.info("Attempting to discover the correct port...")
            discovered_port = await self.discover_server_port()
            
            if discovered_port is not None:
                self.logger.info(f"Discovered MCP server on port {discovered_port}")
                
                # Port was already set and connection established in discover_server_port
                return True
            else:
                self.logger.error("Could not discover any MCP server ports")
                raise ConnectionError("Could not discover any MCP server ports. Please verify the server is running.")

    async def disconnect(self):
        """Disconnect from MCP server."""
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
            self._connected = False
            self.logger.info("Disconnected from MCP server")

    def is_connected(self) -> bool:
        """
        Check if the client is connected to the server.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._connected and self._writer is not None and not self._writer.is_closing()

    async def send_request(
        self, method: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send request to MCP server."""
        if not self._connected:
            await self.connect()

        # Add client ID to params
        if params is None:
            params = {}
        params["client_id"] = self.client_id

        # Create request
        request = MCPRequest(
            id=str(int(time.time() * 1000)), method=method, params=params
        )

        try:
            # Send request
            self._writer.write(request.to_json().encode() + b"\n")
            await self._writer.drain()

            # Read response
            data = await self._reader.readuntil(b"\n")
            response = MCPResponse.from_json(data.decode())

            if response.error:
                raise Exception(response.error.get("message", "Unknown error"))

            if response.result is None:
                raise Exception("Invalid response: missing both result and error.")

            return response.result

        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            raise

    # GPIO control methods
    async def setup_pin(self, pin: int, mode: str = "OUT") -> Dict[str, Any]:
        """Setup GPIO pin."""
        return await self.send_request("gpio.setupPin", {"pin": pin, "mode": mode})

    async def write_pin(self, pin: int, value: bool) -> Dict[str, Any]:
        """Write to GPIO pin."""
        return await self.send_request("gpio.writePin", {"pin": pin, "value": value})

    async def read_pin(self, pin: int) -> Dict[str, Any]:
        """Read from GPIO pin."""
        return await self.send_request("gpio.readPin", {"pin": pin})

    async def setup_led(self, device_id: str, pin: int) -> Dict[str, Any]:
        """Setup LED device."""
        return await self.send_request(
            "gpio.setupLED", {"device_id": device_id, "pin": pin}
        )

    async def control_led(
        self, device_id: str, action: str, **kwargs
    ) -> Dict[str, Any]:
        """Control LED device."""
        params = {"device_id": device_id, "action": action}
        params.update(kwargs)
        return await self.send_request("gpio.controlLED", params)

    # Input control methods
    async def type_text(self, text: str) -> Dict[str, Any]:
        """Type text using keyboard."""
        return await self.send_request("input.typeText", {"text": text})

    async def press_key(self, key: str) -> Dict[str, Any]:
        """Press a specific key."""
        return await self.send_request("input.pressKey", {"key": key})

    async def release_key(self, key: str) -> Dict[str, Any]:
        """Release a specific key."""
        return await self.send_request("input.releaseKey", {"key": key})

    async def hotkey(self, *keys: str) -> Dict[str, Any]:
        """Execute keyboard hotkey."""
        return await self.send_request("input.hotkey", {"keys": list(keys)})

    async def move_mouse(
        self, x: int, y: int, relative: bool = False, duration: float = 0.1
    ) -> Dict[str, Any]:
        """Move mouse to coordinates."""
        return await self.send_request(
            "input.moveMouse",
            {"x": x, "y": y, "relative": relative, "duration": duration},
        )

    async def click(
        self,
        button: str = "left",
        clicks: int = 1,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Perform mouse click."""
        params = {"button": button, "clicks": clicks}
        if x is not None:
            params["x"] = x
        if y is not None:
            params["y"] = y

        return await self.send_request("input.click", params)

    async def double_click(
        self, x: Optional[int] = None, y: Optional[int] = None
    ) -> Dict[str, Any]:
        """Perform double click."""
        params = {}
        if x is not None:
            params["x"] = x
        if y is not None:
            params["y"] = y

        return await self.send_request("input.doubleClick", params)

    async def right_click(
        self, x: Optional[int] = None, y: Optional[int] = None
    ) -> Dict[str, Any]:
        """Perform right click."""
        params = {}
        if x is not None:
            params["x"] = x
        if y is not None:
            params["y"] = y

        return await self.send_request("input.rightClick", params)

    async def scroll(self, amount: int, horizontal: bool = False) -> Dict[str, Any]:
        """Perform mouse scroll."""
        return await self.send_request(
            "input.scroll", {"amount": amount, "horizontal": horizontal}
        )

    async def drag_to(
        self, x: int, y: int, duration: float = 0.5, button: str = "left"
    ) -> Dict[str, Any]:
        """Drag mouse to coordinates."""
        return await self.send_request(
            "input.dragTo", {"x": x, "y": y, "duration": duration, "button": button}
        )

    async def get_mouse_position(self) -> Dict[str, Any]:
        """Get current mouse position."""
        return await self.send_request("input.getMousePosition")

    async def screenshot(self, region: Optional[tuple] = None) -> Dict[str, Any]:
        """Take a screenshot."""
        params = {}
        if region:
            params["region"] = region

        return await self.send_request("input.screenshot", params)

    # Audio control methods
    async def list_audio_devices(self) -> Dict[str, Any]:
        """List available audio devices."""
        return await self.send_request("audio.listDevices")

    async def get_volume(self) -> Dict[str, Any]:
        """Get current system volume."""
        return await self.send_request("audio.getVolume")

    async def set_volume(self, volume: int) -> Dict[str, Any]:
        """Set system volume (0-100)."""
        return await self.send_request("audio.setVolume", {"volume": volume})

    async def play_audio(self, audio_data: str, format: str = "wav") -> Dict[str, Any]:
        """Play audio data (base64 encoded)."""
        return await self.send_request("audio.playAudio", {
            "audio_data": audio_data,
            "format": format
        })

    async def text_to_speech(self, text: str, rate: int = 150, volume: float = 1.0) -> Dict[str, Any]:
        """Convert text to speech and play it."""
        return await self.send_request("audio.textToSpeech", {
            "text": text,
            "rate": rate,
            "volume": volume
        })

    async def generate_tone(self, frequency: int, duration: float, output_file: str = None) -> Dict[str, Any]:
        """Generate a tone with specified frequency and duration."""
        params = {
            "frequency": frequency,
            "duration": duration
        }
        if output_file:
            params["output_file"] = output_file

        return await self.send_request("audio.generateTone", params)

    # I2C control methods
    async def setup_lcd(self, device_id: str, address: int, width: int = 16, height: int = 2) -> Dict[str, Any]:
        """Set up an I2C LCD display."""
        return await self.send_request("i2c.setupLCD", {
            "device_id": device_id,
            "address": address,
            "width": width,
            "height": height
        })

    async def control_lcd(self, device_id: str, action: str, **kwargs) -> Dict[str, Any]:
        """Control an I2C LCD display."""
        params = {"device_id": device_id, "action": action}
        params.update(kwargs)
        return await self.send_request("i2c.controlLCD", params)

    # Hardware discovery methods
    async def discover_hardware(self) -> Dict[str, Any]:
        """Discover available hardware devices."""
        return await self.send_request("system.discoverHardware")

    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return await self.send_request("system.getInfo")

    async def scan_i2c_bus(self, bus: int = 1) -> Dict[str, Any]:
        """Scan I2C bus for devices."""
        return await self.send_request("i2c.scanBus", {"bus": bus})

    async def list_gpio_pins(self) -> Dict[str, Any]:
        """List available GPIO pins."""
        return await self.send_request("gpio.listPins")

    # Installation and setup methods
    async def install_dependencies(self, packages: list) -> Dict[str, Any]:
        """Install system dependencies."""
        return await self.send_request("system.installDependencies", {"packages": packages})

    async def configure_system(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure system settings."""
        return await self.send_request("system.configure", config)

    async def run_self_test(self) -> Dict[str, Any]:
        """Run system self-test."""
        return await self.send_request("system.selfTest")

    # Context manager support
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
