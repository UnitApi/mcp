"""
gpio.py
"""

"""GPIO server for Raspberry Pi control."""

from typing import Dict, Any
import platform

from .base import MCPServer
from ..protocols.hardware_protocol import MCPRequest, MCPResponse, MCPErrorCode

# Check if we're on a Raspberry Pi
IS_RPI = platform.machine() in ["armv7l", "aarch64"]

if IS_RPI:
    import RPi.GPIO as GPIO
    from gpiozero import LED, Button, Buzzer, MotionSensor
else:
    # Mock classes for development on non-RPi systems
    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT"
        IN = "IN"
        HIGH = True
        LOW = False

        @staticmethod
        def setmode(mode):
            pass

        @staticmethod
        def setup(pin, mode):
            pass

        @staticmethod
        def output(pin, value):
            pass

        @staticmethod
        def input(pin):
            return False

        @staticmethod
        def cleanup():
            pass

    GPIO = MockGPIO()

    class MockDevice:
        def on(self):
            pass

        def off(self):
            pass

        def toggle(self):
            pass

        def blink(self, on_time=1, off_time=1):
            pass

        @property
        def is_lit(self):
            return False

        @property
        def is_pressed(self):
            return False

    LED = Button = Buzzer = MotionSensor = MockDevice


class GPIOServer(MCPServer):
    """MCP server for Raspberry Pi GPIO control."""

    def __init__(self):
        super().__init__()
        self.devices: Dict[str, Any] = {}
        self.pins_in_use: set = set()

        if IS_RPI:
            GPIO.setmode(GPIO.BCM)

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle GPIO requests."""
        try:
            method_parts = request.method.split(".")
            if len(method_parts) < 2:
                return self.create_error_response(
                    request.id, MCPErrorCode.METHOD_NOT_FOUND, "Invalid method format"
                )

            action = method_parts[1]

            # Map methods to handlers
            handlers = {
                "setupPin": self.setup_pin,
                "writePin": self.write_pin,
                "readPin": self.read_pin,
                "setupLED": self.setup_led,
                "controlLED": self.control_led,
                "setupButton": self.setup_button,
                "readButton": self.read_button,
                "setupBuzzer": self.setup_buzzer,
                "controlBuzzer": self.control_buzzer,
                "setupMotionSensor": self.setup_motion_sensor,
                "readMotionSensor": self.read_motion_sensor,
                "cleanup": self.cleanup,
            }

            if action not in handlers:
                return self.create_error_response(
                    request.id,
                    MCPErrorCode.METHOD_NOT_FOUND,
                    f"Unknown GPIO method: {action}",
                )

            return await handlers[action](request)

        except Exception as e:
            self.logger.error(f"GPIO error: {e}")
            return self.create_error_response(
                request.id, MCPErrorCode.INTERNAL_ERROR, str(e)
            )

    async def setup_pin(self, request: MCPRequest) -> MCPResponse:
        """Setup a GPIO pin."""
        pin = request.params.get("pin")
        mode = request.params.get("mode", "OUT").upper()

        if pin is None:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Missing pin parameter"
            )

        try:
            if mode == "OUT":
                GPIO.setup(pin, GPIO.OUT)
            else:
                GPIO.setup(pin, GPIO.IN)

            self.pins_in_use.add(pin)

            return MCPResponse(
                id=request.id, result={"status": "success", "pin": pin, "mode": mode}
            )
        except Exception as e:
            return self.create_error_response(
                request.id,
                MCPErrorCode.HARDWARE_ERROR,
                f"Failed to setup motion sensor: {e}",
            )

    async def read_motion_sensor(self, request: MCPRequest) -> MCPResponse:
        """Read motion sensor state."""
        device_id = request.params.get("device_id")

        if not device_id:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Missing device_id parameter"
            )

        sensor = self.devices.get(device_id)
        if not sensor or not isinstance(sensor, MotionSensor):
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Invalid motion sensor device: {device_id}",
            )

        try:
            return MCPResponse(
                id=request.id,
                result={
                    "status": "success",
                    "device_id": device_id,
                    "motion_detected": sensor.motion_detected,
                },
            )
        except Exception as e:
            return self.create_error_response(
                request.id,
                MCPErrorCode.HARDWARE_ERROR,
                f"Failed to read motion sensor: {e}",
            )

    async def cleanup(self, request: MCPRequest) -> MCPResponse:
        """Cleanup GPIO resources."""
        try:
            GPIO.cleanup()
            self.devices.clear()
            self.pins_in_use.clear()

            return MCPResponse(
                id=request.id,
                result={"status": "success", "message": "GPIO cleanup completed"},
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to cleanup GPIO: {e}"
            )

    async def write_pin(self, request: MCPRequest) -> MCPResponse:
        """Write to a GPIO pin."""
        pin = request.params.get("pin")
        value = request.params.get("value")

        if pin is None or value is None:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                "Missing pin or value parameter",
            )

        try:
            GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)

            return MCPResponse(
                id=request.id, result={"status": "success", "pin": pin, "value": value}
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to write pin: {e}"
            )

    async def read_pin(self, request: MCPRequest) -> MCPResponse:
        """Read from a GPIO pin."""
        pin = request.params.get("pin")

        if pin is None:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Missing pin parameter"
            )

        try:
            value = GPIO.input(pin)

            return MCPResponse(
                id=request.id,
                result={"status": "success", "pin": pin, "value": bool(value)},
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to read pin: {e}"
            )

    async def setup_led(self, request: MCPRequest) -> MCPResponse:
        """Setup an LED device."""
        device_id = request.params.get("device_id")
        pin = request.params.get("pin")

        if not device_id or pin is None:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                "Missing device_id or pin parameter",
            )

        try:
            led = LED(pin)
            self.devices[device_id] = led
            self.pins_in_use.add(pin)

            return MCPResponse(
                id=request.id,
                result={"status": "success", "device_id": device_id, "pin": pin},
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to setup LED: {e}"
            )

    async def control_led(self, request: MCPRequest) -> MCPResponse:
        """Control an LED device."""
        device_id = request.params.get("device_id")
        action = request.params.get("action")

        if not device_id or not action:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                "Missing device_id or action parameter",
            )

        led = self.devices.get(device_id)
        if not led or not isinstance(led, LED):
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Invalid LED device: {device_id}",
            )

        try:
            if action == "on":
                led.on()
            elif action == "off":
                led.off()
            elif action == "toggle":
                led.toggle()
            elif action == "blink":
                on_time = request.params.get("on_time", 1)
                off_time = request.params.get("off_time", 1)
                led.blink(on_time=on_time, off_time=off_time)
            else:
                return self.create_error_response(
                    request.id, MCPErrorCode.INVALID_PARAMS, f"Invalid action: {action}"
                )

            return MCPResponse(
                id=request.id,
                result={
                    "status": "success",
                    "device_id": device_id,
                    "action": action,
                    "state": "on" if led.is_lit else "off",
                },
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to control LED: {e}"
            )

    async def setup_button(self, request: MCPRequest) -> MCPResponse:
        """Setup a button device."""
        device_id = request.params.get("device_id")
        pin = request.params.get("pin")

        if not device_id or pin is None:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                "Missing device_id or pin parameter",
            )

        try:
            button = Button(pin)
            self.devices[device_id] = button
            self.pins_in_use.add(pin)

            return MCPResponse(
                id=request.id,
                result={"status": "success", "device_id": device_id, "pin": pin},
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to setup button: {e}"
            )

    async def read_button(self, request: MCPRequest) -> MCPResponse:
        """Read button state."""
        device_id = request.params.get("device_id")

        if not device_id:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Missing device_id parameter"
            )

        button = self.devices.get(device_id)
        if not button or not isinstance(button, Button):
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Invalid button device: {device_id}",
            )

        try:
            return MCPResponse(
                id=request.id,
                result={
                    "status": "success",
                    "device_id": device_id,
                    "is_pressed": button.is_pressed,
                },
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to read button: {e}"
            )

    async def setup_buzzer(self, request: MCPRequest) -> MCPResponse:
        """Setup a buzzer device."""
        device_id = request.params.get("device_id")
        pin = request.params.get("pin")

        if not device_id or pin is None:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                "Missing device_id or pin parameter",
            )

        try:
            buzzer = Buzzer(pin)
            self.devices[device_id] = buzzer
            self.pins_in_use.add(pin)

            return MCPResponse(
                id=request.id,
                result={"status": "success", "device_id": device_id, "pin": pin},
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to setup buzzer: {e}"
            )

    async def control_buzzer(self, request: MCPRequest) -> MCPResponse:
        """Control a buzzer device."""
        device_id = request.params.get("device_id")
        action = request.params.get("action")

        if not device_id or not action:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                "Missing device_id or action parameter",
            )

        buzzer = self.devices.get(device_id)
        if not buzzer or not isinstance(buzzer, Buzzer):
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Invalid buzzer device: {device_id}",
            )

        try:
            if action == "on":
                buzzer.on()
            elif action == "off":
                buzzer.off()
            elif action == "beep":
                on_time = request.params.get("on_time", 0.1)
                off_time = request.params.get("off_time", 0.1)
                count = request.params.get("count", 1)
                buzzer.beep(on_time=on_time, off_time=off_time, n=count)
            else:
                return self.create_error_response(
                    request.id, MCPErrorCode.INVALID_PARAMS, f"Invalid action: {action}"
                )

            return MCPResponse(
                id=request.id,
                result={"status": "success", "device_id": device_id, "action": action},
            )
        except Exception as e:
            return self.create_error_response(
                request.id,
                MCPErrorCode.HARDWARE_ERROR,
                f"Failed to control buzzer: {e}",
            )

    async def setup_motion_sensor(self, request: MCPRequest) -> MCPResponse:
        """Setup a motion sensor device."""
        device_id = request.params.get("device_id")
        pin = request.params.get("pin")

        if not device_id or pin is None:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                "Missing device_id or pin parameter",
            )

        try:
            sensor = MotionSensor(pin)
            self.devices[device_id] = sensor
            self.pins_in_use.add(pin)

            return MCPResponse(
                id=request.id,
                result={"status": "success", "device_id": device_id, "pin": pin},
            )
        except Exception as e:
            return self.create_error_response(
                request.id,
                MCPErrorCode.HARDWARE_ERROR,
                f"Failed to setup motion sensor: {e}",
            )
