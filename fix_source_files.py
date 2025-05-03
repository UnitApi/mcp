#!/usr/bin/env python3
"""
UnitMCP Source File Fixes

This script modifies the actual source files to fix the issues identified in the UnitMCP DSL and Claude 3.7 integration.
"""

import os
import sys
import logging
import re
import inspect
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_dsl_compiler_file():
    """Fix the DSL compiler source file by adding the missing detect_format method."""
    logger.info("Fixing DSL compiler source file...")
    
    # Path to the compiler.py file
    compiler_path = os.path.join('src', 'unitmcp', 'dsl', 'compiler.py')
    
    if not os.path.exists(compiler_path):
        logger.error(f"File not found: {compiler_path}")
        return False
    
    try:
        # Read the current content
        with open(compiler_path, 'r') as f:
            content = f.read()
        
        # Check if detect_format method already exists
        if 'def detect_format' in content:
            logger.info("detect_format method already exists in the source file")
            return True
        
        # Find the class definition
        class_match = re.search(r'class DslCompiler[^\n]*:', content)
        if not class_match:
            logger.error("DslCompiler class definition not found")
            return False
        
        # Find the end of the class
        class_start = class_match.start()
        
        # Add the detect_format method after the compile method
        detect_format_method = '''
    def detect_format(self, content: str) -> str:
        """
        Detect the format of the DSL content.
        
        Args:
            content: The DSL content to analyze
                
        Returns:
            str: The detected format ('yaml', 'json', or 'unknown')
        """
        content = content.strip()
        
        # Try to parse as YAML
        try:
            import yaml
            yaml.safe_load(content)
            return 'yaml'
        except yaml.YAMLError:
            pass
        
        # Try to parse as JSON
        try:
            import json
            json.loads(content)
            return 'json'
        except json.JSONDecodeError:
            pass
        
        # Unknown format
        return 'unknown'
'''
        
        # Find the position to insert the new method
        compile_method_match = re.search(r'def compile\([^)]*\):', content)
        if compile_method_match:
            # Find the end of the compile method
            compile_end = content.find('\n\n', compile_method_match.end())
            if compile_end == -1:
                compile_end = len(content)
            
            # Insert the detect_format method after the compile method
            new_content = content[:compile_end] + detect_format_method + content[compile_end:]
        else:
            # If compile method not found, add at the end of the class
            new_content = content[:class_start] + content[class_start:] + detect_format_method
        
        # Write the updated content
        with open(compiler_path, 'w') as f:
            f.write(new_content)
        
        logger.info("Added detect_format method to DslCompiler in source file")
        return True
    except Exception as e:
        logger.error(f"Error fixing DSL compiler source file: {e}")
        return False

def fix_device_converter_file():
    """Fix the device converter source file by creating a concrete implementation."""
    logger.info("Fixing device converter source file...")
    
    # Path to the to_devices.py file
    converter_path = os.path.join('src', 'unitmcp', 'dsl', 'converters', 'to_devices.py')
    
    if not os.path.exists(converter_path):
        logger.error(f"File not found: {converter_path}")
        return False
    
    try:
        # Read the current content
        with open(converter_path, 'r') as f:
            content = f.read()
        
        # Check if ConcreteDeviceConverter already exists
        if 'class ConcreteDeviceConverter' in content:
            logger.info("ConcreteDeviceConverter already exists in the source file")
            return True
        
        # Create the concrete implementation
        concrete_implementation = '''

class ConcreteDeviceConverter(DeviceConverter):
    """
    Concrete implementation of the DeviceConverter.
    """
    
    def create_device(self, device_type: str, config: Dict[str, Any]) -> Any:
        """
        Create a device instance based on the device type and configuration.
        
        Args:
            device_type: The type of device to create
            config: The device configuration
            
        Returns:
            Any: The created device instance
        """
        logger.info(f"Creating device of type {device_type} with config {config}")
        
        # Simulate device creation
        return {
            'type': device_type,
            'config': config,
            'status': 'initialized'
        }
'''
        
        # Add the concrete implementation at the end of the file
        new_content = content + concrete_implementation
        
        # Write the updated content
        with open(converter_path, 'w') as f:
            f.write(new_content)
        
        logger.info("Added ConcreteDeviceConverter to source file")
        return True
    except Exception as e:
        logger.error(f"Error fixing device converter source file: {e}")
        return False

def fix_dsl_integration_file():
    """Fix the DSL integration source file by adding the missing imports."""
    logger.info("Fixing DSL integration source file...")
    
    # Path to the integration.py file
    integration_path = os.path.join('src', 'unitmcp', 'dsl', 'integration.py')
    
    if not os.path.exists(integration_path):
        logger.error(f"File not found: {integration_path}")
        return False
    
    try:
        # Read the current content
        with open(integration_path, 'r') as f:
            content = f.read()
        
        # Check if MCPHardwareClient is already imported
        if 'from unitmcp import MCPHardwareClient' in content or 'import unitmcp.MCPHardwareClient' in content:
            logger.info("MCPHardwareClient is already imported in the source file")
            return True
        
        # Find the import section
        import_section_end = 0
        for line in content.split('\n'):
            if line.startswith('import ') or line.startswith('from '):
                import_section_end = content.find(line) + len(line)
        
        # Add the import statement
        import_statement = '\nfrom unitmcp import MCPHardwareClient'
        new_content = content[:import_section_end] + import_statement + content[import_section_end:]
        
        # Write the updated content
        with open(integration_path, 'w') as f:
            f.write(new_content)
        
        logger.info("Added MCPHardwareClient import to DSL integration source file")
        return True
    except Exception as e:
        logger.error(f"Error fixing DSL integration source file: {e}")
        return False

def fix_cli_parser_file():
    """Fix the CLI parser source file by adding an alias for the parse method."""
    logger.info("Fixing CLI parser source file...")
    
    # Path to the parser.py file
    parser_path = os.path.join('src', 'unitmcp', 'cli', 'parser.py')
    
    if not os.path.exists(parser_path):
        logger.error(f"File not found: {parser_path}")
        return False
    
    try:
        # Read the current content
        with open(parser_path, 'r') as f:
            content = f.read()
        
        # Check if parse method already exists
        if 'def parse(' in content:
            logger.info("parse method already exists in the source file")
            return True
        
        # Find the parse_shell_command method
        parse_shell_method_match = re.search(r'def parse_shell_command\([^)]*\):', content)
        if not parse_shell_method_match:
            logger.error("parse_shell_command method not found")
            return False
        
        # Find the end of the parse_shell_command method
        parse_shell_end = content.find('\n\n', parse_shell_method_match.end())
        if parse_shell_end == -1:
            parse_shell_end = len(content)
        
        # Add the parse method as an alias
        parse_method = '''
    def parse(self, command: str) -> Dict[str, Any]:
        """
        Parse a command string into a structured command.
        This is an alias for parse_shell_command.
        
        Args:
            command: The command string to parse
            
        Returns:
            Dict[str, Any]: The parsed command
        """
        return self.parse_shell_command(command)
'''
        
        # Insert the parse method after the parse_shell_command method
        new_content = content[:parse_shell_end] + parse_method + content[parse_shell_end:]
        
        # Write the updated content
        with open(parser_path, 'w') as f:
            f.write(new_content)
        
        logger.info("Added parse method as an alias for parse_shell_command in source file")
        return True
    except Exception as e:
        logger.error(f"Error fixing CLI parser source file: {e}")
        return False

async def run_fixes():
    """Run all the fixes."""
    logger.info("Starting UnitMCP source file fixes...")
    
    # Run the fixes
    results = {}
    
    # Fix DSL compiler
    results['dsl_compiler'] = fix_dsl_compiler_file()
    
    # Fix device converter
    results['device_converter'] = fix_device_converter_file()
    
    # Fix DSL integration
    results['dsl_integration'] = fix_dsl_integration_file()
    
    # Fix CLI parser
    results['cli_parser'] = fix_cli_parser_file()
    
    # Print fix results
    logger.info("\n=== UnitMCP Source File Fix Results ===")
    for fix_name, result in results.items():
        status = "SUCCESS" if result else "FAILED"
        logger.info(f"{fix_name}: {status}")
    
    # Calculate overall result
    successful = sum(1 for result in results.values() if result)
    total = len(results)
    logger.info(f"\nOverall: {successful}/{total} source file fixes applied successfully")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_fixes())
