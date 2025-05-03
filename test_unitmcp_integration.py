#!/usr/bin/env python3
"""
UnitMCP Integration Test

This script tests the DSL and Claude 3.7 integration components of UnitMCP.
It runs in simulation mode to avoid requiring actual hardware.
"""

import os
import sys
import logging
import asyncio
import json
import yaml
from unittest import mock

# Add the source directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_dsl_compiler():
    """Test the DSL compiler functionality."""
    logger.info("Testing DSL compiler...")
    
    try:
        from unitmcp.dsl.compiler import DslCompiler
        
        # Create a compiler instance
        compiler = DslCompiler()
        logger.info("DSL compiler created successfully")
        
        # Test format detection
        test_yaml = """
        devices:
          led1:
            type: led
            pin: 17
        """
        format_type = compiler.detect_format(test_yaml)
        logger.info(f"Format detection result: {format_type}")
        
        # Test compilation
        result = compiler.compile(test_yaml)
        logger.info(f"Compilation result: {json.dumps(result, indent=2)}")
        
        return True
    except ImportError as e:
        logger.error(f"Failed to import DSL compiler: {e}")
        return False
    except Exception as e:
        logger.error(f"Error testing DSL compiler: {e}")
        return False

def test_yaml_parser():
    """Test the YAML parser functionality."""
    logger.info("Testing YAML parser...")
    
    try:
        from unitmcp.dsl.formats.yaml_parser import YamlConfigParser
        
        # Create a parser instance
        parser = YamlConfigParser()
        logger.info("YAML parser created successfully")
        
        # Test parsing
        test_yaml = """
        devices:
          led1:
            type: led
            pin: 17
        """
        result = parser.parse(test_yaml)
        logger.info(f"Parsing result: {json.dumps(result, indent=2)}")
        
        return True
    except ImportError as e:
        logger.error(f"Failed to import YAML parser: {e}")
        return False
    except Exception as e:
        logger.error(f"Error testing YAML parser: {e}")
        return False

async def test_device_converter():
    """Test the device converter functionality."""
    logger.info("Testing device converter...")
    
    try:
        from unitmcp.dsl.converters.to_devices import DeviceConverter
        from unitmcp.dsl.converters.mock_factory import MockDeviceFactory
        
        # Create a mock factory for testing
        mock_factory = MockDeviceFactory()
        
        # Create the converter with the mock factory
        converter = DeviceConverter(mock_factory)
        logger.info("Device converter created successfully")
        
        # Test converting a simple configuration
        test_config = {
            "devices": {
                "led1": {
                    "type": "led",
                    "pin": 17
                }
            }
        }
        
        # Convert the configuration to devices
        devices = await converter.convert_to_devices(test_config)
        logger.info(f"Convert result: {devices}")
        
        return True
    except ImportError as e:
        logger.error(f"Failed to import device converter: {e}")
        return False
    except Exception as e:
        logger.error(f"Error testing device converter: {e}")
        return False

async def test_dsl_hardware_integration():
    """Test DSL hardware integration."""
    try:
        from unitmcp.dsl.integration import DslHardwareIntegration
        from unitmcp.dsl.converters.mock_factory import MockDeviceFactory
        
        # Create a mock factory for testing
        mock_factory = MockDeviceFactory()
        
        # Create the integration with simulation mode
        integration = DslHardwareIntegration(device_factory=mock_factory, simulation=True)
        
        # Load a test configuration
        config = """
        devices:
          led1:
            type: led
            pin: 17
          button1:
            type: button
            pin: 18
        """
        
        result = await integration.load_config(config)
        
        # Verify the devices were created
        assert 'devices' in result
        assert 'led1' in result['devices']
        assert 'button1' in result['devices']
        
        # Initialize the devices
        init_result = await integration.initialize_devices()
        assert init_result.get('led1')
        assert init_result.get('button1')
        
        # Execute a command
        command = {
            'device': 'led1',
            'action': 'on',
            'parameters': {}
        }
        
        cmd_result = await integration.execute_command(command)
        assert cmd_result['status'] == 'success'
        
        # Clean up the devices
        cleanup_result = await integration.cleanup_devices()
        assert cleanup_result.get('led1')
        assert cleanup_result.get('button1')
        
        logger.info("DSL hardware integration test passed")
        return True
    except Exception as e:
        logger.error(f"DSL hardware integration test failed: {e}")
        return False

async def test_claude_integration():
    """Test the Claude 3.7 integration functionality."""
    logger.info("Testing Claude 3.7 integration...")
    
    try:
        from unitmcp.llm.claude import ClaudeIntegration
        
        # Create an instance with simulation mode
        integration = ClaudeIntegration(api_key="test_key")
        logger.info("Claude integration created successfully")
        
        # Test processing a command
        test_command = "Turn on the kitchen light"
        
        # Process the command
        result = await integration.process_command(test_command)
        logger.info(f"Process command result: {result}")
        
        return True
    except ImportError as e:
        logger.error(f"Failed to import Claude integration: {e}")
        return False
    except Exception as e:
        logger.error(f"Error testing Claude integration: {e}")
        return False

def test_cli_parser():
    """Test the CLI command parser functionality."""
    logger.info("Testing CLI command parser...")
    
    try:
        from unitmcp.cli.parser import CommandParser
        
        # Create a parser instance
        parser = CommandParser()
        logger.info("CLI parser created successfully")
        
        # Test parsing a device command
        device_cmd = "device led1 on"
        result = parser.parse(device_cmd)
        logger.info(f"Parse device command result: {result}")
        
        # Test parsing a natural language command
        nl_cmd = "natural turn on the kitchen light"
        result = parser.parse(nl_cmd)
        logger.info(f"Parse natural language command result: {result}")
        
        return True
    except ImportError as e:
        logger.error(f"Failed to import CLI parser: {e}")
        return False
    except Exception as e:
        logger.error(f"Error testing CLI parser: {e}")
        return False

async def run_integration_tests():
    """Run all the integration tests."""
    logger.info("Starting UnitMCP integration tests...")
    
    # Test results
    results = {}
    
    # Test DSL compiler
    results['dsl_compiler'] = test_dsl_compiler()
    
    # Test YAML parser
    results['yaml_parser'] = test_yaml_parser()
    
    # Test device converter
    results['device_converter'] = await test_device_converter()
    
    # Test DSL integration
    results['dsl_integration'] = await test_dsl_hardware_integration()
    
    # Test Claude integration
    results['claude_integration'] = await test_claude_integration()
    
    # Test CLI parser
    results['cli_parser'] = test_cli_parser()
    
    # Print results
    logger.info("\n=== UnitMCP Integration Test Results ===")
    for test, result in results.items():
        logger.info(f"{test}: {'PASSED' if result else 'FAILED'}")
    
    # Overall result
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    logger.info(f"\nOverall: {passed}/{total} tests passed")

if __name__ == "__main__":
    asyncio.run(run_integration_tests())
