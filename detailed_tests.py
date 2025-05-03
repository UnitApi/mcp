#!/usr/bin/env python3
"""
UnitMCP Detailed Integration Tests

This script performs detailed tests of the UnitMCP DSL and Claude 3.7 integration,
examining the actual implementation of each component to identify issues.
"""

import os
import sys
import logging
import inspect
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

def inspect_module(module_name):
    """Inspect a module and return its attributes and methods."""
    try:
        module = __import__(module_name, fromlist=['*'])
        logger.info(f"Successfully imported module: {module_name}")
        
        # Get all classes in the module
        classes = {}
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and obj.__module__ == module.__name__:
                classes[name] = {
                    'methods': [],
                    'attributes': []
                }
                
                # Get methods and attributes
                for attr_name, attr in inspect.getmembers(obj):
                    if not attr_name.startswith('_'):  # Skip private/special methods
                        if inspect.isfunction(attr) or inspect.ismethod(attr):
                            classes[name]['methods'].append(attr_name)
                        else:
                            classes[name]['attributes'].append(attr_name)
        
        return {
            'name': module_name,
            'classes': classes
        }
    except ImportError as e:
        logger.error(f"Failed to import module {module_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inspecting module {module_name}: {e}")
        return None

def test_yaml_parser_implementation():
    """Test the actual implementation of the YAML parser."""
    logger.info("Testing YAML parser implementation...")
    
    try:
        from unitmcp.dsl.formats.yaml_parser import YamlConfigParser
        
        # Create an instance
        parser = YamlConfigParser()
        
        # Inspect the class
        methods = [name for name, method in inspect.getmembers(parser, predicate=inspect.ismethod)
                  if not name.startswith('_')]
        
        logger.info(f"YAML parser methods: {methods}")
        
        # Test the parse method with a simple YAML
        test_yaml = """
        devices:
          led1:
            type: led
            pin: 17
        """
        
        # Check if parse method exists and call it
        if 'parse' in methods:
            result = parser.parse(test_yaml)
            logger.info(f"Parse result: {json.dumps(result, indent=2)}")
            return True
        else:
            logger.error("YAML parser does not have a 'parse' method")
            return False
    except Exception as e:
        logger.error(f"Error testing YAML parser implementation: {e}")
        return False

def test_dsl_compiler_implementation():
    """Test the actual implementation of the DSL compiler."""
    logger.info("Testing DSL compiler implementation...")
    
    try:
        from unitmcp.dsl.compiler import DslCompiler
        
        # Create an instance
        compiler = DslCompiler()
        
        # Inspect the class
        methods = [name for name, method in inspect.getmembers(compiler, predicate=inspect.ismethod)
                  if not name.startswith('_')]
        
        logger.info(f"DSL compiler methods: {methods}")
        
        # Check for the missing detect_format method
        if 'detect_format' not in methods:
            logger.warning("DSL compiler is missing the 'detect_format' method")
        
        # Test the compile method if it exists
        if 'compile' in methods:
            test_yaml = """
            devices:
              led1:
                type: led
                pin: 17
            """
            
            result = compiler.compile(test_yaml)
            logger.info(f"Compile result: {json.dumps(result, indent=2)}")
            return True
        else:
            logger.error("DSL compiler does not have a 'compile' method")
            return False
    except Exception as e:
        logger.error(f"Error testing DSL compiler implementation: {e}")
        return False

async def test_device_converter_implementation():
    """Test the actual implementation of the device converter."""
    logger.info("Testing device converter implementation...")
    
    try:
        from unitmcp.dsl.converters.to_devices import DeviceConverter
        from unitmcp.dsl.converters.mock_factory import MockDeviceFactory
        
        # Inspect the class without instantiating
        methods = [name for name, method in inspect.getmembers(DeviceConverter, predicate=inspect.isfunction)
                  if not name.startswith('_')]
        
        logger.info(f"DeviceConverter methods: {methods}")
        
        # Check for abstract methods
        try:
            # Create a mock factory for testing
            mock_factory = MockDeviceFactory()
            
            # Create the converter with the mock factory
            converter = DeviceConverter(mock_factory)
            logger.info("Successfully instantiated DeviceConverter with mock factory")
            
            # Test with a simple configuration
            test_config = {
                "devices": {
                    "led1": {
                        "type": "led",
                        "pin": 17
                    }
                }
            }
            
            # Test the convert_to_devices method
            if 'convert_to_devices' in methods:
                await converter.convert_to_devices(test_config)
                logger.info("Successfully converted devices using mock factory")
                return True
            else:
                logger.error("DeviceConverter does not have a 'convert_to_devices' method")
                return False
                
        except TypeError as e:
            logger.warning(f"DeviceConverter is an abstract class: {e}")
            
            # Check if there's a concrete implementation
            concrete_classes = []
            for name, obj in inspect.getmembers(sys.modules['unitmcp.dsl.converters.to_devices']):
                if inspect.isclass(obj) and issubclass(obj, DeviceConverter) and obj != DeviceConverter:
                    concrete_classes.append(name)
            
            if concrete_classes:
                logger.info(f"Found concrete implementations: {concrete_classes}")
            else:
                logger.warning("No concrete implementations of DeviceConverter found")
        
        return 'convert_to_devices' in methods
    except Exception as e:
        logger.error(f"Error testing device converter implementation: {e}")
        return False

def test_dsl_integration_implementation():
    """Test the actual implementation of the DSL hardware integration."""
    logger.info("Testing DSL hardware integration implementation...")
    
    try:
        from unitmcp.dsl.integration import DslHardwareIntegration
        
        # Inspect the module
        module_attrs = dir(sys.modules['unitmcp.dsl.integration'])
        logger.info(f"DSL integration module attributes: {[attr for attr in module_attrs if not attr.startswith('_')]}")
        
        # Check if MCPHardwareClient is imported
        if 'MCPHardwareClient' not in module_attrs:
            logger.warning("MCPHardwareClient is not imported in the integration module")
            
            # Check imports
            with open(sys.modules['unitmcp.dsl.integration'].__file__, 'r') as f:
                code = f.read()
                logger.info(f"Import statements in integration.py: {[line for line in code.split('\\n') if 'import' in line][:10]}")
        
        # Try to instantiate with a mock
        try:
            integration = DslHardwareIntegration(simulation=True)
            
            # Inspect the instance
            methods = [name for name, method in inspect.getmembers(integration, predicate=inspect.ismethod)
                      if not name.startswith('_')]
            
            logger.info(f"DslHardwareIntegration methods: {methods}")
            
            return True
        except Exception as e:
            logger.error(f"Error instantiating DslHardwareIntegration: {e}")
            return False
    except Exception as e:
        logger.error(f"Error testing DSL integration implementation: {e}")
        return False

def test_claude_integration_implementation():
    """Test the actual implementation of the Claude 3.7 integration."""
    logger.info("Testing Claude 3.7 integration implementation...")
    
    try:
        from unitmcp.llm.claude import ClaudeIntegration
        
        # Inspect the module
        module_attrs = dir(sys.modules['unitmcp.llm.claude'])
        logger.info(f"Claude integration module attributes: {[attr for attr in module_attrs if not attr.startswith('_')]}")
        
        # Check if requests is imported
        if 'requests' not in module_attrs:
            logger.warning("requests is not imported in the claude module")
            
            # Check imports
            with open(sys.modules['unitmcp.llm.claude'].__file__, 'r') as f:
                code = f.read()
                logger.info(f"Import statements in claude.py: {[line for line in code.split('\\n') if 'import' in line][:10]}")
        
        # Try to instantiate with a mock
        try:
            # Mock the requests module if needed
            if 'requests' not in module_attrs:
                sys.modules['unitmcp.llm.claude'].requests = mock.MagicMock()
            
            claude = ClaudeIntegration(api_key="mock_api_key")
            
            # Inspect the instance
            methods = [name for name, method in inspect.getmembers(claude, predicate=inspect.ismethod)
                      if not name.startswith('_')]
            
            logger.info(f"ClaudeIntegration methods: {methods}")
            
            return True
        except Exception as e:
            logger.error(f"Error instantiating ClaudeIntegration: {e}")
            return False
    except Exception as e:
        logger.error(f"Error testing Claude integration implementation: {e}")
        return False

def test_cli_parser_implementation():
    """Test the actual implementation of the CLI command parser."""
    logger.info("Testing CLI command parser implementation...")
    
    try:
        from unitmcp.cli.parser import CommandParser
        
        # Create an instance
        parser = CommandParser()
        
        # Inspect the class
        methods = [name for name, method in inspect.getmembers(parser, predicate=inspect.ismethod)
                  if not name.startswith('_')]
        
        logger.info(f"CLI parser methods: {methods}")
        
        # Check for the missing parse method
        if 'parse' not in methods:
            logger.warning("CLI parser is missing the 'parse' method")
            
            # Look for similar methods
            parse_like_methods = [method for method in methods if 'parse' in method.lower()]
            if parse_like_methods:
                logger.info(f"Found similar parsing methods: {parse_like_methods}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing CLI parser implementation: {e}")
        return False

async def run_detailed_tests():
    """Run all the detailed tests."""
    logger.info("Starting UnitMCP detailed integration tests...")
    
    # Set environment variables for simulation mode
    os.environ['SIMULATION'] = '1'
    os.environ['VERBOSE'] = '1'
    
    # Inspect key modules
    modules_to_inspect = [
        'unitmcp.dsl',
        'unitmcp.dsl.formats',
        'unitmcp.dsl.converters',
        'unitmcp.llm',
        'unitmcp.cli'
    ]
    
    for module_name in modules_to_inspect:
        result = inspect_module(module_name)
        if result:
            logger.info(f"\n=== Module: {result['name']} ===")
            for class_name, class_info in result['classes'].items():
                logger.info(f"Class: {class_name}")
                logger.info(f"  Methods: {class_info['methods']}")
                logger.info(f"  Attributes: {class_info['attributes']}")
    
    # Run the detailed tests
    results = {}
    
    # Test YAML parser implementation
    results['yaml_parser'] = test_yaml_parser_implementation()
    
    # Test DSL compiler implementation
    results['dsl_compiler'] = test_dsl_compiler_implementation()
    
    # Test device converter implementation
    results['device_converter'] = await test_device_converter_implementation()
    
    # Test DSL integration implementation
    results['dsl_integration'] = test_dsl_integration_implementation()
    
    # Test Claude integration implementation
    results['claude_integration'] = test_claude_integration_implementation()
    
    # Test CLI parser implementation
    results['cli_parser'] = test_cli_parser_implementation()
    
    # Print test results
    logger.info("\n=== UnitMCP Detailed Test Results ===")
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    # Calculate overall result
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_detailed_tests())
