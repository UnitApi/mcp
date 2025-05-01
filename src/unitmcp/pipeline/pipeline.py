"""
pipeline.py
"""

"""Pipeline management for MCP hardware control."""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Union
from pathlib import Path
from enum import Enum

from ..client.client import MCPHardwareClient
from ..utils.logger import get_logger


class ExpectationType(Enum):
    """Types of expectations for pipeline steps."""

    VALUE_EQUALS = "equals"
    VALUE_CONTAINS = "contains"
    VALUE_GREATER = "greater"
    VALUE_LESS = "less"
    VALUE_RANGE = "range"
    VALUE_REGEX = "regex"
    CUSTOM = "custom"


@dataclass
class Expectation:
    """Expectation for a pipeline step result."""

    type: ExpectationType
    field: str
    value: Any
    message: Optional[str] = None
    custom_check: Optional[Callable] = None

    def check(self, result: Dict[str, Any]) -> bool:
        """Check if the expectation is met."""
        if self.type == ExpectationType.CUSTOM and self.custom_check:
            return self.custom_check(result)

        # Get the field value from result
        field_value = result
        for part in self.field.split("."):
            if isinstance(field_value, dict) and part in field_value:
                field_value = field_value[part]
            else:
                return False

        # Check based on type
        if self.type == ExpectationType.VALUE_EQUALS:
            return field_value == self.value
        elif self.type == ExpectationType.VALUE_CONTAINS:
            return self.value in str(field_value)
        elif self.type == ExpectationType.VALUE_GREATER:
            return float(field_value) > float(self.value)
        elif self.type == ExpectationType.VALUE_LESS:
            return float(field_value) < float(self.value)
        elif self.type == ExpectationType.VALUE_RANGE:
            min_val, max_val = self.value
            return float(min_val) <= float(field_value) <= float(max_val)
        elif self.type == ExpectationType.VALUE_REGEX:
            import re

            return bool(re.match(self.value, str(field_value)))

        return False


@dataclass
class PipelineStep:
    """Single step in a pipeline."""

    command: str
    method: str
    params: Dict[str, Any] = field(default_factory=dict)
    expectations: List[Expectation] = field(default_factory=list)
    on_success: Optional[str] = None  # Next step or pipeline to execute
    on_failure: Optional[str] = None  # Step or pipeline to execute on failure
    retry_count: int = 0
    retry_delay: float = 1.0
    timeout: float = 30.0
    description: Optional[str] = None


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""

    success: bool
    steps_executed: int
    results: List[Dict[str, Any]]
    errors: List[str]
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class Pipeline:
    """Pipeline for executing sequences of hardware commands."""

    def __init__(
        self, name: str, steps: List[PipelineStep], description: Optional[str] = None
    ):
        self.name = name
        self.steps = steps
        self.description = description
        self.variables: Dict[str, Any] = {}
        self.logger = get_logger(f"Pipeline.{name}")

    def set_variable(self, name: str, value: Any):
        """Set a pipeline variable."""
        self.variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a pipeline variable."""
        return self.variables.get(name, default)

    def substitute_variables(self, value: Any) -> Any:
        """Substitute variables in a value."""
        if isinstance(value, str):
            # Replace ${var} with variable values
            import re

            pattern = r"\$\{([^}]+)\}"

            def replace(match):
                var_name = match.group(1)
                return str(self.get_variable(var_name, match.group(0)))

            return re.sub(pattern, replace, value)
        elif isinstance(value, dict):
            return {k: self.substitute_variables(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.substitute_variables(v) for v in value]
        return value

    async def execute_step(
        self, client: MCPHardwareClient, step: PipelineStep, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single pipeline step."""
        # Substitute variables in parameters
        params = self.substitute_variables(step.params)

        # Execute with retry logic
        last_error = None
        for attempt in range(step.retry_count + 1):
            try:
                # Execute the command
                result = await asyncio.wait_for(
                    client.send_request(step.method, params), timeout=step.timeout
                )

                # Check expectations
                expectations_met = True
                for expectation in step.expectations:
                    if not expectation.check(result):
                        expectations_met = False
                        error_msg = (
                            expectation.message
                            or f"Expectation failed: {expectation.field}"
                        )
                        self.logger.warning(error_msg)
                        last_error = error_msg

                if expectations_met:
                    return {"success": True, "result": result}

            except asyncio.TimeoutError:
                last_error = f"Step timed out after {step.timeout} seconds"
                self.logger.warning(f"Attempt {attempt + 1} timed out")
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")

            if attempt < step.retry_count:
                await asyncio.sleep(step.retry_delay)

        return {"success": False, "error": last_error}

    async def execute(
        self, client: MCPHardwareClient, context: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        """Execute the pipeline."""
        start_time = time.time()
        context = context or {}
        results = []
        errors = []
        steps_executed = 0

        self.logger.info(f"Starting pipeline execution: {self.name}")

        current_step_idx = 0
        while current_step_idx < len(self.steps):
            step = self.steps[current_step_idx]
            self.logger.info(f"Executing step {current_step_idx + 1}: {step.command}")

            # Execute the step
            step_result = await self.execute_step(client, step, context)
            results.append(step_result)
            steps_executed += 1

            if step_result["success"]:
                # Update context with result
                context[f"step_{current_step_idx}_result"] = step_result["result"]

                # Check for next step override
                if step.on_success:
                    # Find step by name or index
                    next_step = self._find_step(step.on_success)
                    if next_step is not None:
                        current_step_idx = next_step
                    else:
                        self.logger.warning(
                            f"On_success step not found: {step.on_success}"
                        )
                        current_step_idx += 1
                else:
                    current_step_idx += 1
            else:
                # Handle failure
                error_msg = step_result.get("error", "Unknown error")
                errors.append(f"Step {current_step_idx + 1} failed: {error_msg}")
                self.logger.error(f"Step failed: {error_msg}")

                if step.on_failure:
                    next_step = self._find_step(step.on_failure)
                    if next_step is not None:
                        current_step_idx = next_step
                    else:
                        self.logger.warning(
                            f"On_failure step not found: {step.on_failure}"
                        )
                        break
                else:
                    break

        duration = time.time() - start_time
        success = len(errors) == 0 and steps_executed == len(self.steps)

        self.logger.info(f"Pipeline completed in {duration:.2f}s - Success: {success}")

        return PipelineResult(
            success=success,
            steps_executed=steps_executed,
            results=results,
            errors=errors,
            duration=duration,
            metadata={"variables": self.variables, "context": context},
        )

    def _find_step(self, identifier: str) -> Optional[int]:
        """Find step index by command name or index."""
        # Try as index
        try:
            idx = int(identifier)
            if 0 <= idx < len(self.steps):
                return idx
        except ValueError:
            pass

        # Try as command name
        for i, step in enumerate(self.steps):
            if step.command == identifier:
                return i

        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "steps": [
                {
                    "command": step.command,
                    "method": step.method,
                    "params": step.params,
                    "expectations": [
                        {
                            "type": exp.type.value,
                            "field": exp.field,
                            "value": exp.value,
                            "message": exp.message,
                        }
                        for exp in step.expectations
                    ],
                    "on_success": step.on_success,
                    "on_failure": step.on_failure,
                    "retry_count": step.retry_count,
                    "retry_delay": step.retry_delay,
                    "timeout": step.timeout,
                    "description": step.description,
                }
                for step in self.steps
            ],
            "variables": self.variables,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pipeline":
        """Create pipeline from dictionary."""
        steps = []
        for step_data in data.get("steps", []):
            expectations = []
            for exp_data in step_data.get("expectations", []):
                expectations.append(
                    Expectation(
                        type=ExpectationType(exp_data["type"]),
                        field=exp_data["field"],
                        value=exp_data["value"],
                        message=exp_data.get("message"),
                    )
                )

            steps.append(
                PipelineStep(
                    command=step_data["command"],
                    method=step_data["method"],
                    params=step_data.get("params", {}),
                    expectations=expectations,
                    on_success=step_data.get("on_success"),
                    on_failure=step_data.get("on_failure"),
                    retry_count=step_data.get("retry_count", 0),
                    retry_delay=step_data.get("retry_delay", 1.0),
                    timeout=step_data.get("timeout", 30.0),
                    description=step_data.get("description"),
                )
            )

        pipeline = cls(
            name=data["name"], steps=steps, description=data.get("description")
        )
        pipeline.variables = data.get("variables", {})
        return pipeline

    def save(self, filepath: Union[str, Path]):
        """Save pipeline to file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "Pipeline":
        """Load pipeline from file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)


class PipelineManager:
    """Manager for multiple pipelines."""

    def __init__(self):
        self.pipelines: Dict[str, Pipeline] = {}
        self.logger = get_logger("PipelineManager")

    def add_pipeline(self, pipeline: Pipeline):
        """Add a pipeline to the manager."""
        self.pipelines[pipeline.name] = pipeline
        self.logger.info(f"Added pipeline: {pipeline.name}")

    def get_pipeline(self, name: str) -> Optional[Pipeline]:
        """Get a pipeline by name."""
        return self.pipelines.get(name)

    def remove_pipeline(self, name: str) -> bool:
        """Remove a pipeline by name."""
        if name in self.pipelines:
            del self.pipelines[name]
            self.logger.info(f"Removed pipeline: {name}")
            return True
        return False

    def list_pipelines(self) -> List[str]:
        """List all pipeline names."""
        return list(self.pipelines.keys())

    async def execute_pipeline(
        self,
        name: str,
        client: MCPHardwareClient,
        context: Optional[Dict[str, Any]] = None,
    ) -> PipelineResult:
        """Execute a pipeline by name."""
        pipeline = self.get_pipeline(name)
        if not pipeline:
            raise ValueError(f"Pipeline not found: {name}")

        return await pipeline.execute(client, context)

    def save_all(self, directory: Union[str, Path]):
        """Save all pipelines to a directory."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        for name, pipeline in self.pipelines.items():
            filepath = directory / f"{name}.json"
            pipeline.save(filepath)

        self.logger.info(f"Saved {len(self.pipelines)} pipelines to {directory}")

    def load_all(self, directory: Union[str, Path]):
        """Load all pipelines from a directory."""
        directory = Path(directory)
        if not directory.exists():
            raise ValueError(f"Directory not found: {directory}")

        for filepath in directory.glob("*.json"):
            try:
                pipeline = Pipeline.load(filepath)
                self.add_pipeline(pipeline)
            except Exception as e:
                self.logger.error(f"Failed to load pipeline from {filepath}: {e}")

    def create_from_template(self, template_name: str, **kwargs) -> Pipeline:
        """Create a pipeline from a template."""
        templates = {
            "led_blink": self._create_led_blink_template,
            "keyboard_test": self._create_keyboard_test_template,
            "camera_monitor": self._create_camera_monitor_template,
            "system_check": self._create_system_check_template,
        }

        if template_name not in templates:
            raise ValueError(f"Unknown template: {template_name}")

        return templates[template_name](**kwargs)

    def _create_led_blink_template(
        self,
        led_pin: int = 17,
        blink_count: int = 5,
        on_time: float = 0.5,
        off_time: float = 0.5,
    ) -> Pipeline:
        """Create a LED blink pipeline template."""
        steps = [
            PipelineStep(
                command="setup_led",
                method="gpio.setupLED",
                params={"device_id": "led1", "pin": led_pin},
                expectations=[
                    Expectation(
                        type=ExpectationType.VALUE_EQUALS,
                        field="status",
                        value="success",
                        message="LED setup failed",
                    )
                ],
                description="Setup LED on specified pin",
            ),
            PipelineStep(
                command="blink_led",
                method="gpio.controlLED",
                params={
                    "device_id": "led1",
                    "action": "blink",
                    "on_time": on_time,
                    "off_time": off_time,
                },
                expectations=[
                    Expectation(
                        type=ExpectationType.VALUE_EQUALS,
                        field="status",
                        value="success",
                    )
                ],
                description=f"Blink LED {blink_count} times",
            ),
            PipelineStep(
                command="wait",
                method="system.sleep",
                params={"duration": (on_time + off_time) * blink_count},
                description="Wait for blinking to complete",
            ),
            PipelineStep(
                command="turn_off",
                method="gpio.controlLED",
                params={"device_id": "led1", "action": "off"},
                expectations=[
                    Expectation(
                        type=ExpectationType.VALUE_EQUALS,
                        field="status",
                        value="success",
                    )
                ],
                description="Turn off LED",
            ),
        ]

        return Pipeline(
            name="led_blink",
            steps=steps,
            description=f"Blink LED on pin {led_pin} for {blink_count} times",
        )

    def _create_keyboard_test_template(
        self, test_text: str = "Hello, World!"
    ) -> Pipeline:
        """Create a keyboard test pipeline template."""
        steps = [
            PipelineStep(
                command="type_text",
                method="input.typeText",
                params={"text": test_text},
                expectations=[
                    Expectation(
                        type=ExpectationType.VALUE_EQUALS,
                        field="status",
                        value="success",
                    )
                ],
                description="Type test text",
            ),
            PipelineStep(
                command="select_all",
                method="input.hotkey",
                params={"keys": ["ctrl", "a"]},
                description="Select all text",
            ),
            PipelineStep(
                command="copy_text",
                method="input.hotkey",
                params={"keys": ["ctrl", "c"]},
                description="Copy selected text",
            ),
            PipelineStep(
                command="new_line",
                method="input.pressKey",
                params={"key": "enter"},
                description="Press Enter key",
            ),
            PipelineStep(
                command="paste_text",
                method="input.hotkey",
                params={"keys": ["ctrl", "v"]},
                description="Paste copied text",
            ),
        ]

        return Pipeline(
            name="keyboard_test",
            steps=steps,
            description="Test keyboard input functionality",
        )

    def _create_camera_monitor_template(
        self, duration: int = 60, threshold: int = 25
    ) -> Pipeline:
        """Create a camera monitoring pipeline template."""
        steps = [
            PipelineStep(
                command="open_camera",
                method="camera.openCamera",
                params={"camera_id": 0, "device_name": "monitor_cam"},
                expectations=[
                    Expectation(
                        type=ExpectationType.VALUE_EQUALS,
                        field="status",
                        value="success",
                    )
                ],
                description="Open camera for monitoring",
            ),
            PipelineStep(
                command="check_motion",
                method="camera.detectMotion",
                params={
                    "device_name": "monitor_cam",
                    "threshold": threshold,
                    "mark_motion": True,
                },
                expectations=[
                    Expectation(
                        type=ExpectationType.VALUE_EQUALS,
                        field="status",
                        value="success",
                    )
                ],
                retry_count=duration,  # Check every second for duration
                retry_delay=1.0,
                on_success="check_motion",  # Loop back to itself
                description="Monitor for motion",
            ),
            PipelineStep(
                command="close_camera",
                method="camera.closeCamera",
                params={"device_name": "monitor_cam"},
                description="Close camera",
            ),
        ]

        return Pipeline(
            name="camera_monitor",
            steps=steps,
            description=f"Monitor camera for motion for {duration} seconds",
        )

    def _create_system_check_template(self) -> Pipeline:
        """Create a system check pipeline template."""
        steps = [
            PipelineStep(
                command="list_gpio_devices",
                method="gpio.listDevices",
                params={},
                expectations=[
                    Expectation(
                        type=ExpectationType.VALUE_EQUALS,
                        field="status",
                        value="success",
                    )
                ],
                description="List GPIO devices",
            ),
            PipelineStep(
                command="list_audio_devices",
                method="audio.listDevices",
                params={},
                expectations=[
                    Expectation(
                        type=ExpectationType.VALUE_EQUALS,
                        field="status",
                        value="success",
                    )
                ],
                description="List audio devices",
            ),
            PipelineStep(
                command="list_cameras",
                method="camera.listCameras",
                params={},
                expectations=[
                    Expectation(
                        type=ExpectationType.VALUE_EQUALS,
                        field="status",
                        value="success",
                    )
                ],
                description="List camera devices",
            ),
            PipelineStep(
                command="get_mouse_position",
                method="input.getMousePosition",
                params={},
                expectations=[
                    Expectation(
                        type=ExpectationType.VALUE_EQUALS,
                        field="status",
                        value="success",
                    )
                ],
                description="Get current mouse position",
            ),
        ]

        return Pipeline(
            name="system_check",
            steps=steps,
            description="Check system hardware availability",
        )

    def validate_pipeline(self, pipeline: Pipeline) -> List[str]:
        """Validate a pipeline configuration."""
        errors = []

        # Check for empty steps
        if not pipeline.steps:
            errors.append("Pipeline has no steps")

        # Check each step
        for i, step in enumerate(pipeline.steps):
            # Check required fields
            if not step.command:
                errors.append(f"Step {i + 1}: Missing command")
            if not step.method:
                errors.append(f"Step {i + 1}: Missing method")

            # Check on_success/on_failure references
            if step.on_success and not pipeline._find_step(step.on_success):
                errors.append(
                    f"Step {i + 1}: Invalid on_success reference: {step.on_success}"
                )
            if step.on_failure and not pipeline._find_step(step.on_failure):
                errors.append(
                    f"Step {i + 1}: Invalid on_failure reference: {step.on_failure}"
                )

        return errors
