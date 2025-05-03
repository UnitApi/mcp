# UnitMCP DSL and Claude 3.7 Integration

This document outlines the plan for extending UnitMCP with Domain-Specific Languages (DSL) and Claude 3.7 integration to enhance hardware control capabilities.

## Overview

The extension adds three key components to UnitMCP:

1. **DSL Support**: Multiple domain-specific languages for hardware configuration and automation
2. **CLI Integration**: Command-line interface with natural language processing
3. **Claude 3.7 Integration**: AI-powered command interpretation and execution

## DSL Implementation

### Supported DSL Formats

#### 1. YAML-based Configuration (Home Assistant style)

```yaml
# examples/automation/light_control.yaml
automation:
  trigger:
    platform: time
    at: "07:00"
  condition:
    condition: numeric_state
    entity_id: sensor.temperature
    below: 20
  action:
    service: light.turn_on
    entity_id: light.kitchen
    brightness: 255
```

#### 2. Flow-based Programming (Node-RED style)

```json
{
  "nodes": [
    {
      "id": "sensor1",
      "type": "gpio",
      "pin": 17,
      "mode": "input"
    },
    {
      "id": "led1",
      "type": "gpio",
      "pin": 18,
      "mode": "output"
    },
    {
      "id": "flow1",
      "wires": [
        {
          "source": "sensor1",
          "target": "led1",
          "condition": "value > 0.5"
        }
      ]
    }
  ]
}
```

#### 3. Hardware Configuration (ESPHome style)

```yaml
# examples/hardware/config.yaml
unitmcp:
  name: "livingroom-controller"
  platform: raspberry_pi
  mode: hardware

devices:
  - platform: gpio
    name: "living_room_light"
    pin: 17
    type: led
    
  - platform: gpio
    name: "motion_sensor"
    pin: 27
    type: button
    pull_up: true
    
  - platform: i2c
    name: "temperature_sensor"
    address: 0x76
    type: bme280
```

### DSL Compiler Architecture

```
src/unitmcp/dsl/
├── __init__.py
├── compiler.py         # Main DSL compiler interface
├── formats/
│   ├── __init__.py
│   ├── yaml_parser.py  # YAML-based automation parser
│   ├── flow_parser.py  # Flow-based programming parser
│   └── config_parser.py # Hardware configuration parser
├── converters/
│   ├── __init__.py
│   ├── to_commands.py  # Convert DSL to UnitMCP commands
│   └── to_objects.py   # Convert DSL to UnitMCP objects
└── validators/
    ├── __init__.py
    ├── schema.py       # Schema validation
    └── security.py     # Security validation
```

## CLI Integration

### Command-line Interface

```
src/unitmcp/cli/
├── __init__.py
├── main.py             # CLI entry point
├── commands/
│   ├── __init__.py
│   ├── device.py       # Device management commands
│   ├── automation.py   # Automation commands
│   └── system.py       # System commands
├── parser.py           # Command parser
└── utils.py            # CLI utilities
```

### Example CLI Usage

```bash
# Direct hardware control
unitmcp device led1 on

# Load automation from file
unitmcp automation load examples/automation/light_control.yaml

# Natural language command (uses Claude 3.7)
unitmcp nl "Turn on the kitchen light when motion is detected"

# Interactive shell
unitmcp shell
```

## Claude 3.7 Integration

### Architecture

```
src/unitmcp/llm/
├── __init__.py
├── claude.py           # Claude 3.7 API client
├── prompts/
│   ├── __init__.py
│   ├── hardware.py     # Hardware control prompts
│   ├── automation.py   # Automation prompts
│   └── system.py       # System prompts
├── parser.py           # Parse Claude responses
└── security.py         # Security validation for LLM commands
```

### Example Implementation

```python
# src/unitmcp/llm/claude.py
import asyncio
import json
import os
from typing import Dict, Any, Optional

class ClaudeIntegration:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("CLAUDE_API_KEY")
        if not self.api_key:
            raise ValueError("Claude API key not provided")
        
    async def process_command(self, natural_language: str) -> Dict[str, Any]:
        """Process natural language command using Claude 3.7"""
        prompt = self._build_prompt(natural_language)
        response = await self._call_claude_api(prompt)
        parsed_command = self._parse_response(response)
        return parsed_command
    
    def _build_prompt(self, command: str) -> str:
        return f"""
        Convert the following natural language command into a UnitMCP command:
        
        Command: {command}
        
        Output the result as a JSON object with the following structure:
        {{
            "command_type": "device_control|automation|system",
            "target": "device_id or system component",
            "action": "specific action to perform",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }}
        }}
        
        Only output valid JSON, nothing else.
        """
    
    async def _call_claude_api(self, prompt: str) -> str:
        # Implement Claude API call here
        # This is a placeholder
        await asyncio.sleep(0.5)
        return json.dumps({
            "command_type": "device_control",
            "target": "kitchen_light",
            "action": "turn_on",
            "parameters": {
                "brightness": 100
            }
        })
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse Claude response",
                "raw_response": response
            }
```

## Security Considerations

1. **Command Validation**: All commands generated by Claude 3.7 must be validated before execution
2. **Sandboxing**: LLM-generated commands should run in a restricted environment
3. **Permission System**: Role-based access control for different command types
4. **Audit Logging**: Log all commands and their sources for security review

## Integration with Existing Hardware Abstraction Layer

```python
# src/unitmcp/hardware/dsl_integration.py
from unitmcp.dsl.compiler import DslCompiler
from unitmcp.hardware.device_factory import DeviceFactory
from typing import Dict, Any, List

class DslHardwareIntegration:
    def __init__(self, device_factory: DeviceFactory):
        self.device_factory = device_factory
        self.dsl_compiler = DslCompiler()
    
    async def create_devices_from_dsl(self, dsl_content: str) -> Dict[str, Any]:
        """Create devices from DSL content"""
        compiled_config = self.dsl_compiler.compile(dsl_content)
        return await self.device_factory.create_devices_from_config(compiled_config)
    
    async def execute_automation(self, dsl_content: str) -> Dict[str, Any]:
        """Execute automation defined in DSL"""
        compiled_automation = self.dsl_compiler.compile(dsl_content)
        # Implementation depends on automation system
        return {"status": "success", "message": "Automation executed"}
```

## Implementation Roadmap

### Phase 1: DSL Core (2 weeks)
- Implement YAML parser for device configuration
- Create DSL compiler framework
- Integrate with existing device factory

### Phase 2: Automation DSL (3 weeks)
- Implement automation YAML parser
- Create automation execution engine
- Add event system for triggers and conditions

### Phase 3: Claude 3.7 Integration (2 weeks)
- Implement Claude API client
- Create prompt templates
- Add response parser and validator

### Phase 4: CLI and Security (2 weeks)
- Implement CLI commands
- Add security validation
- Create audit logging system

### Phase 5: Documentation and Examples (1 week)
- Create comprehensive documentation
- Develop example applications
- Write tutorials

## Example Applications

### 1. Smart Home Controller

```yaml
# examples/applications/smart_home.yaml
devices:
  living_room_light:
    type: led
    pin: 17
  
  motion_sensor:
    type: button
    pin: 27
    pull_up: true
  
  temperature_sensor:
    type: i2c
    address: 0x76
    device_type: bme280

automations:
  motion_light:
    trigger:
      platform: state
      entity_id: motion_sensor
      to: "on"
    condition:
      condition: numeric_state
      entity_id: temperature_sensor
      below: 20
    action:
      service: device.activate
      entity_id: living_room_light
```

### 2. Industrial Monitoring System

```yaml
# examples/applications/industrial_monitor.yaml
devices:
  production_line_sensor:
    type: analog_input
    pin: 4
  
  alarm_light:
    type: traffic_light
    red_pin: 17
    yellow_pin: 18
    green_pin: 27
  
  status_display:
    type: display
    display_type: lcd
    width: 16
    height: 2

automations:
  production_monitor:
    trigger:
      platform: numeric_state
      entity_id: production_line_sensor
      above: 80
    action:
      - service: device.set_state
        entity_id: alarm_light
        state: yellow
      - service: device.write_line
        entity_id: status_display
        line: 0
        text: "Warning: High load"
```

## Conclusion

This integration plan provides a comprehensive approach to extending UnitMCP with DSL support and Claude 3.7 integration. The implementation follows a modular architecture that integrates seamlessly with the existing hardware abstraction layer while providing powerful new capabilities for configuration, automation, and natural language control.
